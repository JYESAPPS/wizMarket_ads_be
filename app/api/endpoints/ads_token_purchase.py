from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List
import logging
from app.schemas.ads_ticket import (
    InsertPayRequest,
)

from app.service.ads_ticket import (
    update_subscription_info as service_update_subscription_info,
)

from app.service.ads_token_purchase import (
    insert_purchase as service_insert_purchase,
)

from app.service.play_store import (
    verify_play_store_purchase as service_verify_play_store_purchase
)


router = APIRouter()
logger = logging.getLogger(__name__)


# 결제
@router.post("/purchase")
def insert_payment(request: InsertPayRequest):  

    # 확인용
    # print(request)

    # 구글 플레이스토어 검증
    if request.platform == "android" : 
        verify = service_verify_play_store_purchase(request)
    
    # ios 앱 스토어 검증 X
    elif request.platform == "ios" :
        verify = {"success": True}


    # 구매 검증 분기 처리
    if verify.get("success"):
        # token_purchase insert
        try:
            service_insert_purchase(request)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"토큰 구매 과정에서 문제가 발생했습니다.: {str(e)}"
            )

        # if request.plan_type in ["basic", "standard", "premium"]:
        #     try:
        #         service_update_subscription_info(request.user_id, request.plan_type)
        #     except Exception as e:
        #         raise HTTPException(
        #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #             detail=f"구독 정보 저장 과정에서 문제가 발생했습니다.: {str(e)}"
        #         )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "결제가 성공적으로 처리되었습니다.",
                "count": request.qty,
            }
        )
    
    else :
        return JSONResponse(
            status_code=status.HTTP_500_FALSE,
            content={
                "success": False,
                "message": "결제 처리 실패.",
                "count": request.qty,
            }
        )