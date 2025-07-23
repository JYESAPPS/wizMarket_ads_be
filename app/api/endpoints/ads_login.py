from fastapi import APIRouter, HTTPException, status
from app.schemas.ads_user import (
    UserRegisterRequest, ImageListRequest, KaKao
)

from app.service.ads_login import (
    ads_login as service_ads_login,
    get_category as service_get_category,
    get_image_list as service_get_image_list,
    get_kakao_user_info as service_get_kakao_user_info,
    create_access_token as service_create_access_token
)


router = APIRouter()


# 로그인 API 엔드포인트
@router.post("/login")
def ads_login_route(request: UserRegisterRequest):
    user = service_ads_login(request.email, request.temp_pw)
    if user:
        user_id, user_type, store_bn = user
        return {
            "success": True,
            "message": "로그인 성공",
            "user_id": user_id,
            "type": user_type,
            "store_business_number": store_bn
        }
    else:
        return {
            "success": False,
            "message": "아이디 또는 비밀번호가 올바르지 않습니다."
        }
    

# 어드민 CMS 등록
@router.get("/get/category")
def get_category():
    list = service_get_category()

    if list:
        return {"category_list": list}
    else:
        return {"category_list": False}
    

@router.post("/get/image/list")
def get_image_list(request: ImageListRequest):
    category_id = request.categoryId
    result = service_get_image_list(category_id)

    return {"image_list": result or []}



@router.post("/login/kakao")
def ads_login_kakao_route(request: KaKao):
    user_info = service_get_kakao_user_info(request.kakao_access_token)

    if not user_info or "id" not in user_info:
        raise HTTPException(status_code=401, detail="카카오 토큰이 유효하지 않습니다.")

    kakao_id = str(user_info["id"])
    nickname = user_info.get("properties", {}).get("nickname", "카카오유저")
    email = user_info.get("kakao_account", {}).get("email", None)

    # 🧨 여기선 DB 없이 그냥 가정: 신규 유저 생성 처리만 함
    fake_user_id = f"kakao-{kakao_id}"  # 예: 고유 식별자 생성

    # JWT 발급
    token = service_create_access_token(data={"sub": fake_user_id})

    return {
        "access_token": token,
        "user": {
            "id": fake_user_id,
            "nickname": nickname,
            "email": email,
        }
    }