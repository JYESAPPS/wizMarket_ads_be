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
    deduct_token as service_deduct_token
)


router = APIRouter()
logger = logging.getLogger(__name__)


# 결제
@router.post("/payment")
def insert_payment(request: List[InsertPayRequest]):  
    # 토큰 구매 100개 제한
    try:
        is_exist = service_get_history_100(request[0])
        if not is_exist:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "이미 구매하셨습니다.",
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"결제 과정에서 문제가 발생했습니다.: {str(e)}"
        )  
    # 결제 내역에 추가 로직
    try:
        for each in request:
            for _ in range(each.qty):
                service_insert_payment(each)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"결제 과정에서 문제가 발생했습니다.: {str(e)}"
        )

    #토큰 지급 로직
    try:
        for each in request:
            for _ in range(each.qty):
                service_insert_token(each)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"토큰 지급 과정에서 문제가 발생했습니다.: {str(e)}"
        )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "결제가 성공적으로 처리되었습니다.",
            "count": sum(each.qty for each in request),
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