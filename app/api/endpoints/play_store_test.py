from fastapi import APIRouter
from pydantic import BaseModel
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

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
