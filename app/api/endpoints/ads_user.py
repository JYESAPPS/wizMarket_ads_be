from fastapi import APIRouter, Request
from app.schemas.ads_user import (
    UserRegisterRequest
)

from app.service.ads_user import (
    check_user_id as service_check_user_id,
    register_user as service_register_user
)


router = APIRouter()


@router.get("/check/id")
def check_user_id(user_id: str):
    try:
        exists = service_check_user_id(user_id)
        return {"available": not bool(exists)}
    except Exception as e:
        print(f"중복 검사 오류: {e}")
        return {"available": False}


@router.post("/register/user")
def register_user(request: UserRegisterRequest):
    try:
        service_register_user(request.user_id, request.password)
        
        return {"success": True}

    except Exception as e:
        print(f"회원가입 오류: {e}")
        return {"success": False, "message": "서버 오류"}