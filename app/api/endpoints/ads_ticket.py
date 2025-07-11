from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List
import logging
from app.schemas.ads_ticket import (
    InsertPayRequest
)

from app.service.ads_ticket import (
    insert_payment as service_insert_payment,
    insert_token as service_insert_token,
    get_history as service_get_history,
    get_token as service_get_token
)


router = APIRouter()
logger = logging.getLogger(__name__)


# 결제
@router.post("/payment")
def insert_payment(request: List[InsertPayRequest]):    
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