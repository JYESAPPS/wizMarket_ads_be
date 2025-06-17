from fastapi import APIRouter, HTTPException, status
from app.schemas.ads_user import (
    UserRegisterRequest
)

from app.service.ads_login import (
    ads_login as service_ads_login,
)


router = APIRouter()


# 로그인 API 엔드포인트
@router.post("/login")
def ads_login(request: UserRegisterRequest):
    success = service_ads_login(request.email, request.temp_pw)
    print(success)
    if success:
        return {"success": True, "message": "로그인 성공", "user_id": success}
    else:
        return {"success": False, "message": "아이디 또는 비밀번호가 올바르지 않습니다.", "user_id": 0}