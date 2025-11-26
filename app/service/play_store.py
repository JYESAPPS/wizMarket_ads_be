from fastapi import APIRouter
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

router = APIRouter()

# ------------------------------
# Google Play API 설정
# ------------------------------
SCOPES = ["https://www.googleapis.com/auth/androidpublisher"]
PACKAGE_NAME = "com.wizmarket"  # 플레이스토어 상의 패키지명

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_JSON_PATH")


def get_android_publisher():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )
    service = build("androidpublisher", "v3", credentials=credentials)
    return service


# 단건 소모성 / 구독 SKU만 관리
CONSUMABLE_PRODUCT_IDS = {
    "wm_basic_n",  # 단건(소모성)
}

SUBSCRIPTION_PRODUCT_IDS = {
    "wm_standard_m",
    "wm_standard_y",
    "wm_premium_m",
    "wm_premium_y",
    "wm_concierge_m",
}


def verify_play_store_purchase(request):
    """
    - 단건(소모성): products.get → purchaseState 확인 → products.consume
    - 구독: subscriptions.get → purchaseState 확인 → subscriptions.acknowledge
    """

    if request.platform != "android":
        return {"success": False, "message": "Only Android supported in test mode"}

    publisher = get_android_publisher()

    product_id = request.product_id
    purchase_token = request.purchase_token

    # ------------------------------
    # 1) 구독 결제
    # ------------------------------
    if product_id in SUBSCRIPTION_PRODUCT_IDS:
        try:
            sub = (
                publisher.purchases()
                .subscriptions()
                .get(
                    packageName=PACKAGE_NAME,
                    subscriptionId=product_id,
                    token=purchase_token,
                )
                .execute()
            )
        except Exception as e:
            return {
                "success": False,
                "message": f"Google subscription verify failed: {e}",
            }

        # purchaseState: 0 = 구매 완료
        purchase_state = sub.get("purchaseState", None)
        if purchase_state != 0:
            return {
                "success": False,
                "message": f"Invalid subscription purchaseState: {purchase_state}",
            }

        # acknowledgementState: 1 = 이미 승인됨
        ack_state = sub.get("acknowledgementState", 0)
        if ack_state != 1:
            try:
                body = {
                    "developerPayload": f"user_id={getattr(request, 'user_id', '')}"
                }
                (
                    publisher.purchases()
                    .subscriptions()
                    .acknowledge(
                        packageName=PACKAGE_NAME,
                        subscriptionId=product_id,
                        token=purchase_token,
                        body=body,
                    )
                    .execute()
                )
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Subscription acknowledge failed: {e}",
                }

        return {
            "success": True,
            "message": "Subscription verified & acknowledged successfully",
            "product_id": product_id,
            "transaction_id": request.transaction_id,
            "type": "subscription",
        }

    # ------------------------------
    # 2) 단건 소모성 결제
    # ------------------------------
    if product_id in CONSUMABLE_PRODUCT_IDS:
        try:
            verify = (
                publisher.purchases()
                .products()
                .get(
                    packageName=PACKAGE_NAME,
                    productId=product_id,
                    token=purchase_token,
                )
                .execute()
            )
        except Exception as e:
            return {
                "success": False,
                "message": f"Google product verify failed: {e}",
            }

        # purchaseState: 0=구매완료
        purchase_state = verify.get("purchaseState", None)
        if purchase_state != 0:
            return {
                "success": False,
                "message": f"Invalid product purchaseState: {purchase_state}",
            }

        # 소비 처리 (소모성)
        try:
            (
                publisher.purchases()
                .products()
                .consume(
                    packageName=PACKAGE_NAME,
                    productId=product_id,
                    token=purchase_token,
                )
                .execute()
            )
        except Exception as e:
            return {"success": False, "message": f"Consume failed: {e}"}

        return {
            "success": True,
            "message": "Consumable purchase verified & consumed successfully",
            "product_id": product_id,
            "transaction_id": request.transaction_id,
            "type": "consumable",
        }

    # ------------------------------
    # 3) 정의되지 않은 product_id
    # ------------------------------
    return {
        "success": False,
        "message": f"Unknown product_id: {product_id}",
    }
