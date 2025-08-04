# app/api/fcm_push.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.service.ads_push import send_push_fcm_v1

router = APIRouter()

class PushRequest(BaseModel):
    token: str
    title: str
    body: str

@router.post("/push/test")
def test_push(request: PushRequest):
    status, result = send_push_fcm_v1(
        request.token,
        request.title,
        request.body
    )
    return {"status": status, "result": result}
