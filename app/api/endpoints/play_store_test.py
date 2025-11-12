from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel
from google.oauth2 import service_account
from googleapiclient.discovery import build
from appstoreserverlibrary.models.Environment import Environment
from appstoreserverlibrary.signed_data_verifier import SignedDataVerifier
from appstoreserverlibrary.signed_data_verifier import VerificationException
import os
import time
import httpx
import jwt
from pathlib import Path
from typing import Optional

router = APIRouter()

# ------------------------------
# Google Play API 설정
# ------------------------------
SCOPES = ["https://www.googleapis.com/auth/androidpublisher"]
PACKAGE_NAME = "com.wizmarket"  # 플레이스토어 상의 패키지명

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(BASE_DIR), "../","core", "service-account.json")


def get_android_publisher():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )
    service = build("androidpublisher", "v3", credentials=credentials)
    return service


# ------------------------------
# 요청 바디 모델 (테스트용 최소)
# ------------------------------
class PlayStorePurchase(BaseModel):
    product_id: str
    purchase_token: str
    platform: str = "android"      # 기본값 android
    # transaction_id: str | None = None   # 옵션


# ------------------------------
# /play/store 테스트 엔드포인트
# ------------------------------
@router.post("/play/store/test")
async def verify_play_store_purchase(payload: PlayStorePurchase):

    if payload.platform != "android":
        return {"success": False, "message": "Only Android supported in test mode"}

    publisher = get_android_publisher()

    # ------------------------------
    # 1. 구매 검증
    # ------------------------------
    try:
        verify = publisher.purchases().products().get(
            packageName=PACKAGE_NAME,
            productId=payload.product_id,
            token=payload.purchase_token,
        ).execute()
    except Exception as e:
        return {"success": False, "message": f"Google verify failed: {e}"}

    # 구글이 반환한 purchaseState: 0=구매완료
    purchase_state = verify.get("purchaseState", None)
    if purchase_state != 0:
        return {"success": False, "message": f"Invalid purchaseState: {purchase_state}"}

    # ------------------------------
    # 2. 소비 처리 (소모성)
    # ------------------------------
    try:
        publisher.purchases().products().consume(
            packageName=PACKAGE_NAME,
            productId=payload.product_id,
            token=payload.purchase_token,
        ).execute()
    except Exception as e:
        return {"success": False, "message": f"Consume failed: {e}"}

    # ------------------------------
    # 3. 성공 응답
    # ------------------------------
    return {
        "success": True,
        "message": "Purchase verified & consumed successfully",
        "product_id": payload.product_id,
        # "transaction_id": payload.transaction_id,
    }



# ------------------------------
# IOS App Store Server API 설정
# ------------------------------

APPLE_ISSUER_ID = os.getenv("APPLE_ISSUER_ID", "")
APPLE_KEY_ID    = os.getenv("APPLE_KEY_ID", "")
APPLE_BUNDLE_ID = os.getenv("APPLE_BUNDLE_ID", "")
APPLE_P8_PATH   = os.getenv("APPLE_P8_PATH", "AuthKey.p8")  # p8 경로
DEFAULT_ENV     = os.getenv("APPLE_ENV", "SANDBOX").upper() # SANDBOX | PROD

APPLE_BASE = {
    "PROD":    "https://api.storekit.itunes.apple.com",
    "SANDBOX": "https://api.storekit-sandbox.itunes.apple.com",
}


def _load_private_key() -> str:
    # 파일이 있으면 파일에서 읽고, 없으면 APPLE_P8_PATH 값을 PEM 문자열로 간주
    p = Path(APPLE_P8_PATH)
    if p.exists():
        return p.read_text()
    return APPLE_P8_PATH  # PEM 문자열로 전달된 경우

def make_apple_jwt() -> str:
    """
    Apple App Store Server API 호출용 ES256 JWT
    """
    if not (APPLE_ISSUER_ID and APPLE_KEY_ID and APPLE_BUNDLE_ID):
        raise RuntimeError("Apple API 자격(ISSUER_ID/KEY_ID/BUNDLE_ID)이 설정되지 않았습니다.")

    now = int(time.time())
    payload = {
        "iss": APPLE_ISSUER_ID,
        "iat": now,
        "exp": now + 20 * 60,          # 최대 20분
        "aud": "appstoreconnect-v1",
        "bid": APPLE_BUNDLE_ID,
    }
    headers = {"alg": "ES256", "kid": APPLE_KEY_ID, "typ": "JWT"}
    return jwt.encode(payload, _load_private_key(), algorithm="ES256", headers=headers)

def base_url(env: str) -> str:
    env = (env or DEFAULT_ENV).upper()
    if env not in APPLE_BASE:
        raise HTTPException(400, f"env는 SANDBOX | PROD 중 하나여야 합니다. 전달값: {env}")
    return APPLE_BASE[env]

def load_apple_root_certs(dir_path: str = "apple_roots"):
    """
    apple_roots 폴더에 넣어둔 Apple Root CA들을 모두 읽어서 bytes 배열로 반환.
    예: Apple Root CA - G3.cer, Apple Root CA - G2.cer 등
    """
    import os, glob
    certs = []
    if not os.path.isdir(dir_path):
        raise RuntimeError(f"Apple root cert dir not found: {dir_path}")
    for p in glob.glob(os.path.join(dir_path, "*")):
        try:
            with open(p, "rb") as f:
                certs.append(f.read())
        except Exception:
            pass
    if not certs:
        raise RuntimeError("No Apple root certificates found in apple_roots/")
    return certs


# ─────────────────────────────────────────────────────────────
# 요청 바디 스키마
# ─────────────────────────────────────────────────────────────
class VerifyTxBody(BaseModel):
    transactionId: str
    env: Optional[str] = None
    productId: Optional[str] = None   # (선택) 기대 제품 확인용

class VerifySubBody(BaseModel):
    originalTransactionId: str
    env: Optional[str] = None

# ─────────────────────────────────────────────────────────────
# FastAPI
# ─────────────────────────────────────────────────────────────
app = FastAPI(title="Apple IAP Test (Single File)")

@router.get("/")
def root():
    return {"ok": True, "msg": "Go to /docs for Swagger UI."}

@router.post("/iap/apple/verify-purchase")
async def verify_transaction(body: VerifyTxBody):
    """
    특정 거래(transactionId) 단건 조회 + JWS 서명 검증 + 핵심 클레임 요약
    """
    try:
        token = make_apple_jwt()
        url = f"{base_url(body.env)}/inApps/v1/transactions/{body.transactionId}"
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        if r.status_code != 200:
            raise HTTPException(r.status_code, f"Apple API error: {r.text}")

        data = r.json()
        signed_tx = data.get("signedTransactionInfo")
        if not signed_tx:
            raise HTTPException(400, "signedTransactionInfo not found")

        # ★ 환경 매핑 (SANDBOX/PROD → Enum)
        env_str = (body.env or DEFAULT_ENV).upper()
        env_enum = Environment.SANDBOX if env_str == "SANDBOX" else Environment.PRODUCTION  # ★

        # ★ 루트 인증서 + 온라인체크 여부 + 환경 + 번들ID로 Verifier 생성
        roots = load_apple_root_certs()  # apple_roots 폴더에서 읽음  ★
        verifier = SignedDataVerifier(
            roots,
            True,                # enable_online_checks (CRL/OCSP 온라인 검증)
            env_enum,
            APPLE_BUNDLE_ID,
        )  # ★

        # ★ 정확한 메서드명: verify_and_decode_signed_transaction
        claims = verifier.verify_and_decode_signed_transaction(signed_tx)   # ★

        # attrs 객체일 수 있어서 getattr로 안전 추출
        def g(name):
            return getattr(claims, name, None)

        problems = []
        if g("bundleId") and g("bundleId") != APPLE_BUNDLE_ID:
            problems.append("bundleId mismatch")
        if getattr(body, "productId", None) and g("productId") != body.productId:
            problems.append("productId mismatch")

        # 요약
        def ms_to_iso(ms):
            if not ms: return None
            import datetime
            return datetime.datetime.utcfromtimestamp(int(ms)/1000).isoformat()+"Z"

        summary = {
            "bundleId": g("bundleId"),
            "productId": g("productId"),
            "transactionId": g("transactionId"),
            "originalTransactionId": g("originalTransactionId"),
            "environment": g("environment"),  # "Sandbox"/"Production"
            "purchasedAt": ms_to_iso(g("purchaseDate")),
            "expiresAt":   ms_to_iso(g("expiresDate")),
            "revoked":     g("revocationDate") is not None,
        }

        # 상태 판정
        status = "active"
        if summary["revoked"]:
            status = "refunded"
        elif summary["expiresAt"]:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            exp = datetime.fromisoformat(summary["expiresAt"].replace("Z","+00:00"))
            if exp <= now:
                status = "expired"

        return {
            "ok": len(problems) == 0,
            "status": status,
            "problems": problems,
            "summary": summary,
            "apple_raw": data,
        }
    except VerificationException as ve:
        raise HTTPException(400, f"verification failed: {ve}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"verify_transaction failed: {e}")



@router.post("/iap/apple/verify-subscription")
async def verify_subscription(body: VerifySubBody):
    try:
        token = make_apple_jwt()
        url = f"{base_url(body.env)}/inApps/v1/subscriptions/{body.originalTransactionId}"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        if r.status_code != 200:
            raise HTTPException(r.status_code, f"Apple API error: {r.text}")
        data = r.json()

        # Verifier 준비
        env_str = (body.env or DEFAULT_ENV).upper()
        env_enum = Environment.SANDBOX if env_str == "SANDBOX" else Environment.PRODUCTION
        roots = load_apple_root_certs()
        verifier = SignedDataVerifier(roots, True, env_enum, APPLE_BUNDLE_ID)

        def ms_to_iso(ms):
            if not ms: return None
            import datetime
            return datetime.datetime.utcfromtimestamp(int(ms)/1000).isoformat()+"Z"

        # 핵심: data[] -> lastTransactions[] -> signedTransactionInfo
        summaries = []
        for group in (data.get("data") or []):
            for lt in (group.get("lastTransactions") or []):
                stx = lt.get("signedTransactionInfo")
                if not stx:
                    continue
                claims = verifier.verify_and_decode_signed_transaction(stx)
                g = lambda n: getattr(claims, n, None)
                summaries.append({
                    "subscriptionGroup": group.get("subscriptionGroupIdentifier"),
                    "statusCode": lt.get("status"),  # 숫자 상태코드 그대로 리턴
                    "productId": g("productId"),
                    "transactionId": g("transactionId"),
                    "originalTransactionId": g("originalTransactionId"),
                    "environment": g("environment"),
                    "purchasedAt": ms_to_iso(g("purchaseDate")),
                    "expiresAt":   ms_to_iso(g("expiresDate")),
                    "revoked":     g("revocationDate") is not None,
                })

        # (선택) 최신 순으로 정렬하고 맨 앞만 쓰고 싶다면 주석 해제
        # from datetime import datetime, timezone
        # def to_dt(s): return datetime.fromisoformat(s.replace("Z","+00:00")) if s else None
        # summaries.sort(key=lambda x: to_dt(x["purchasedAt"]) or to_dt(x["expiresAt"]), reverse=True)
        # latest = summaries[0] if summaries else None

        return {"ok": True, "summaries": summaries, "apple_raw": data}
    except VerificationException as ve:
        raise HTTPException(400, f"verification failed: {ve}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"verify_subscription failed: {e}")


# ─────────────────────────────────────────────────────────────
# 앱 내 구매 소모
# ─────────────────────────────────────────────────────────────
@router.post("/iap/apple/consume")
async def consume_purchase(body: VerifyTxBody):
    """
    [Consumable] 서버에서 Apple JWS 검증만 수행하고,
    클라이언트(StoreKit)에게 finishTransaction 호출 지시를 반환.
    DB/토큰 지급 없이 '소모 가능 상태'만 보장합니다.
    """
    try:
        # 1) Apple에서 거래 단건 조회
        token = make_apple_jwt()
        url = f"{base_url(body.env)}/inApps/v1/transactions/{body.transactionId}"
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        if r.status_code != 200:
            raise HTTPException(r.status_code, f"Apple API error: {r.text}")

        data = r.json()
        signed_tx = data.get("signedTransactionInfo")
        if not signed_tx:
            raise HTTPException(400, "signedTransactionInfo not found")

        # 2) JWS 서명 검증 + 클레임 추출
        env_str = (body.env or DEFAULT_ENV).upper()
        env_enum = Environment.SANDBOX if env_str == "SANDBOX" else Environment.PRODUCTION
        roots = load_apple_root_certs()
        verifier = SignedDataVerifier(roots, True, env_enum, APPLE_BUNDLE_ID)
        claims = verifier.verify_and_decode_signed_transaction(signed_tx)

        # 3) 최소 정합성 검사 (번들/상품/환불)
        problems = []
        if getattr(claims, "bundleId", None) and claims.bundleId != APPLE_BUNDLE_ID:
            problems.append("bundleId mismatch")
        if body.productId and getattr(claims, "productId", None) != body.productId:
            problems.append("productId mismatch")
        if getattr(claims, "revocationDate", None):
            problems.append("revoked")

        if problems:
            # 유효하지 않으면 finish 시키지 않음
            return {
                "ok": False,
                "problems": problems,
                "action": "doNotFinish",  # 클라이언트는 finishTransaction 호출 금지
                "apple_raw": data,
            }

        # 4) 유효 → 클라이언트에서 finishTransaction 호출 지시
        return {
            "ok": True,
            "action": "finishTransaction",  # ← 여기만 보면 됨
            "transactionId": getattr(claims, "transactionId", None),
            "productId": getattr(claims, "productId", None),
            "note": "After receiving this, call finishTransaction on iOS.",
            "apple_raw": data,  # 필요 없으면 제거해도 됩니다
        }

    except VerificationException as ve:
        raise HTTPException(400, f"verification failed: {ve}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"consume failed: {e}")
