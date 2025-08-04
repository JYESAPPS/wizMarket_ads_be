# app/api/fcm_push.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.service.ads_push import (
    send_push_fcm_v1,
    select_user_id_token as service_select_user_id_token
)
from app.schemas.ads_push import PushRequest

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