# google_play_consume.py
"""
Google Play Developer API를 사용해 특정 인앱 결제(purchaseToken)를 consume 처리하는 스크립트.

사용 전 준비:
1. Google Cloud Console에서 Play Console에 연결된 서비스 계정 키(JSON) 다운로드
2. 아래 CONFIG 부분 값 채우기:
   - SERVICE_ACCOUNT_FILE: 서비스 계정 JSON 경로
   - PACKAGE_NAME: 인앱이 붙어있는 앱 패키지명 (ex: "com.wizmarket")
   - PRODUCT_ID: 인앱상품 ID (ex: "wm_basic_n")
   - PURCHASE_TOKEN: consume 처리할 purchaseToken
3. 패키지 설치:
   pip install google-auth google-auth-httplib2 requests
"""

import json
import sys
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

# ===== CONFIG =====
SERVICE_ACCOUNT_FILE = "C:\\Users\\jyes_semin\\Downloads\\api-5264199636846743917-375244-8bb21552be02.json"  # 서비스 계정 JSON 파일 경로
PACKAGE_NAME = "com.wizmarket"                # 실제 패키지명
PRODUCT_ID = "wm_basic_n"                     # 실제 인앱 상품 ID
PURCHASE_TOKEN = (
    "lbefaemdgchangbfgpeoocem.AO-J1Oz3U7_z5g1Wt8j2HOrjAB4ae-shjpGht2qIgYGGVqRaTzOhtH-itr2xyokEtVBdS80rGcZK1kosFVNSD4TVhxnXoU7x4g"
)
# ===================



SCOPE = ["https://www.googleapis.com/auth/androidpublisher"]


def get_authed_session(service_account_file: str) -> AuthorizedSession:
    """서비스 계정 JSON으로 인증된 세션 생성."""
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file,
        scopes=SCOPE,
    )
    authed_session = AuthorizedSession(credentials)
    return authed_session


def consume_purchase(
    session: AuthorizedSession,
    package_name: str,
    product_id: str,
    purchase_token: str,
) -> dict:
    """
    Google Play Developer API - purchases.products.consume 호출.

    참고 공식 엔드포인트:
    POST https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{packageName}/purchases/products/{productId}/tokens/{token}:consume
    """
    url = (
        f"https://androidpublisher.googleapis.com/androidpublisher/v3/"
        f"applications/{package_name}/purchases/products/{product_id}/"
        f"tokens/{purchase_token}:consume"
    )

    # body는 비어 있어도 됨
    resp = session.post(url)
    try:
        data = resp.json()
    except Exception:
        data = {"raw_text": resp.text}

    result = {
        "status_code": resp.status_code,
        "response": data,
    }
    return result


def main():
    # 값 확인용 출력
    print("=== Google Play Consume Test ===")
    print(f"PACKAGE_NAME   = {PACKAGE_NAME}")
    print(f"PRODUCT_ID     = {PRODUCT_ID}")
    print(f"PURCHASE_TOKEN = {PURCHASE_TOKEN[:16]}...")

    if "TODO" in (PACKAGE_NAME + PRODUCT_ID) or not PURCHASE_TOKEN:
        print("[ERROR] CONFIG 값을 실제 값으로 채워주세요.")
        sys.exit(1)

    try:
        session = get_authed_session(SERVICE_ACCOUNT_FILE)
    except Exception as e:
        print("[ERROR] 서비스 계정 인증 실패:", e)
        sys.exit(1)

    try:
        result = consume_purchase(session, PACKAGE_NAME, PRODUCT_ID, PURCHASE_TOKEN)
        print("=== Consume API Result ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print("[ERROR] Consume 호출 중 예외:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
