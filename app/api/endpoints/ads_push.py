# app/api/fcm_push.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.service.ads_push import (
    send_push_fcm_v1,
    select_user_id_token as service_select_user_id_token,
    get_marketing_opt as service_get_marketing_opt,
    update_marketing_opt as service_update_marketing_opt,
)
from app.schemas.ads_push import PushRequest, MarketingOpt

router = APIRouter()


@router.post("/push/test")
def test_push(request: PushRequest):
    status, result = send_push_fcm_v1(
        request.token,
        request.title,
        request.body
    )
    return {"status": status, "result": result}


@router.post("/reserve")
def send_reserve_push():
    user_id_token_list = service_select_user_id_token()
    print(user_id_token_list)

# 마케팅 수신 여부 조회
@router.get("/get/marketing")
def get_marketing_opt(user_id: int):
    return service_get_marketing_opt(user_id)

# 마케팅 수신 동의 설정
@router.post("/update/marketing")
def update_marketing_opt(request: MarketingOpt):
    result = service_update_marketing_opt(request.opt, request.user_id)
    return {"result": result}
