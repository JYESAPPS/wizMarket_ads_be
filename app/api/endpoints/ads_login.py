from fastapi import APIRouter, HTTPException, status
from app.schemas.ads_user import (
    UserRegisterRequest
)

from app.service.ads_login import (
    ads_login as service_ads_login,
    get_category as service_get_category
)


router = APIRouter()


# 로그인 API 엔드포인트
@router.post("/login")
def ads_login(request: UserRegisterRequest):
    success = service_ads_login(request.email, request.temp_pw)

    if success:
        return {"success": True, "message": "로그인 성공", "user_id": success}
    else:
        return {"success": False, "message": "아이디 또는 비밀번호가 올바르지 않습니다.", "user_id": 0}
    

# 어드민 CMS 등록
@router.get("/get/category")
def get_category():
    list = service_get_category()

    if list:
        return {"category_list": list}
    else:
        return {"category_list": False}
    
