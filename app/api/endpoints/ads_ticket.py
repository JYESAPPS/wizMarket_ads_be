from fastapi import APIRouter, HTTPException, status
from typing import List
from app.schemas.ads_ticket import (
    InsertPayRequest
)

from app.service.ads_ticket import (
    insert_payment as service_insert_payment,
    insert_token as service_insert_token
)


router = APIRouter()

# 결제
@router.post("/payment")
def insert_payment(request: List[InsertPayRequest]):    
    # 결제 내역에 추가 로직
    try:
        for each in request:
            for _ in range(each.qty):
                service_insert_payment(each)
        pass
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

#결제 목록
# @router.get("/payment")
# def get_history(user_id: int):
#     try:
#         data = service_get_history
#         return data
#     except Exception as e:
#         return {"success": False, "message": "조회 중 오류 발생"}