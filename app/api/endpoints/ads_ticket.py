from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List
import logging
from app.schemas.ads_ticket import (
    InsertPayRequest,
    InsertTokenRequest
)

from app.service.ads_ticket import (
    insert_payment as service_insert_payment,
    insert_token as service_insert_token,
    get_history_100 as service_get_history_100,
    get_history as service_get_history,
    get_token as service_get_token,
    get_valid_ticket as service_get_valid_ticket,
    deduct_token as service_deduct_token,
    get_token_deduction_history as service_get_token_deduction_history,
    update_subscription_info as service_update_subscription_info,
)
from app.service.play_store import (
    verify_play_store_purchase as service_verify_play_store_purchase
)


router = APIRouter()
logger = logging.getLogger(__name__)


# 결제
@router.post("/payment")
def insert_payment(request: InsertPayRequest):  

    # 확인용
    print(request)

    # 구글 플레이스토어 검증
    if request.platform == "android" : 
        verify = service_verify_play_store_purchase(request)
    
    else :
        verify = ""

    # 구매 검증 분기 처리
    if verify.get("success"):
        
        # 결제 내역에 추가 로직
        try:
            service_insert_payment(request)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"결제 과정에서 문제가 발생했습니다.: {str(e)}"
            )

        #토큰 지급 로직
        try:
            service_insert_token(request)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"토큰 지급 과정에서 문제가 발생했습니다.: {str(e)}"
            )

        if request.plan_type in ["basic", "standard", "premium"]:
            try:
                service_update_subscription_info(request.user_id, request.plan_type)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"구독 정보 저장 과정에서 문제가 발생했습니다.: {str(e)}"
                )
        
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


#결제 목록 호출
@router.get("/list")
def get_history(user_id: int):
    try:
        data = service_get_history(user_id)
        return data
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "조회 중 오류 발생"}

# 가진 단건+정기 토큰 호출
@router.get("/token")
def get_token(user_id: int):
    try:
        token = service_get_token(user_id)
        return token
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "조회 중 오류 발생"}
    
# 사용자 티켓 & 토큰 정보 호출
@router.get("/user/info")
def get_valid_ticket(userId: int):
    try: 
        data = service_get_valid_ticket(userId)
        return data
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "조회 중 오류 발생"}

@router.post("/token/deduct")
def deduct_token_endpoint(request: InsertTokenRequest):
    try:
        user_id = request.user_id
        data = service_deduct_token(user_id=user_id)

        return {
            "used_type": data["used_type"],
            "remaining_tokens": data["token_onetime"] + data["token_subscription"],
            "total_tokens": data["total_tokens"]
        }
    except ValueError as ve:
        logger.error(f"[400 Error] {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"[500 Error] {str(e)}")  # ✅ 에러 로그 출력
        raise HTTPException(status_code=500, detail=f"토큰 차감 중 오류 발생: {str(e)}")
    
@router.get("/token/history")
def get_token_history(user_id: int):
    try:
        data = service_get_token_deduction_history(user_id)
        return {"success": True, "history": data}
    except Exception as e:
        logger.error(f"[토큰 차감 이력 오류] {e}")
        raise HTTPException(status_code=500, detail="토큰 차감 이력 조회 중 오류 발생")