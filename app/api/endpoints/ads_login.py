from fastapi import APIRouter, HTTPException, status
from app.schemas.ads_user import (
    UserRegisterRequest, ImageListRequest, KaKao, User, UserUpdate
)



from app.service.ads_login import (
    ads_login as service_ads_login,
    get_category as service_get_category,
    get_image_list as service_get_image_list,
    get_kakao_user_info as service_get_kakao_user_info,
    create_access_token as service_create_access_token,
    create_refresh_token as service_create_refresh_token,
    get_user_by_provider as service_get_user_by_provider,
    update_user_token as service_update_user_token,
    decode_token as service_decode_token,
    get_user_by_id as service_get_user_by_id,
    update_user as service_update_user
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
    kakao_info = service_get_kakao_user_info(request.kakao_access_token)

    if not kakao_info or "id" not in kakao_info:
        raise HTTPException(status_code=401, detail="카카오 토큰이 유효하지 않습니다.")


    kakao_id = str(kakao_info["id"])
    kakao_account = kakao_info.get("kakao_account", {})

    email = kakao_account.get("email")

    user_id = service_get_user_by_provider(provider="kakao", provider_id=kakao_id, email=email)
    user_info = service_get_user_by_id(user_id)

    # JWT 발급
    access_token = service_create_access_token(data={"sub": str(user_id)})
    refresh_token = service_create_refresh_token({"sub": str(user_id)})

    # 토큰 update
    service_update_user_token(user_id, access_token, refresh_token)


    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "user_id": user_id,
            "email": email,
            "type": user_info["type"],
            "store_business_number": user_info.get("store_business_number", None)
        }
    }



@router.post("/auto/login")
def auto_login(request: User):
    """
    저장된 access_token으로 자동 로그인 시도
    """
    access_token  = request.access_token

    payload = service_decode_token(access_token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="토큰에 user_id(sub)가 없습니다.")

    user = service_get_user_by_id(int(user_id))

    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "type": user["type"],
        "store_business_number": user.get("store_business_number", None)
    }


@router.post("/update/user/store/info")
def update_user_store_info(request: UserUpdate):
    user_id = request.user_id
    store_business_number = request.store_business_number
    insta_account = request.insta_account

    sucess = service_update_user(user_id, store_business_number, insta_account)

    return {
        "success": sucess,  # 성공 여부
        "message": "유저 정보가 업데이트 되었습니다." if sucess else "유저 정보 업데이트에 실패했습니다."
    }