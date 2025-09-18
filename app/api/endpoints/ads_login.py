import os, requests
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from app.schemas.ads_user import (
    UserRegisterRequest, ImageListRequest, KaKao, Google, Naver, User, UserUpdate,
    TokenRefreshRequest, TokenRefreshResponse, InitUserInfo, NaverExchange
)
from jose import jwt, ExpiredSignatureError, JWTError


from app.service.ads_login import (
    ads_login as service_ads_login,
    get_category as service_get_category,
    get_image_list as service_get_image_list,
    get_kakao_user_info as service_get_kakao_user_info,
    get_google_user_info as service_get_google_user_info,
    get_naver_user_info as service_get_naver_user_info,
    create_access_token as service_create_access_token,
    create_refresh_token as service_create_refresh_token,
    get_user_by_provider as service_get_user_by_provider,
    update_user_token as service_update_user_token,
    decode_token as service_decode_token,
    get_user_by_id as service_get_user_by_id,
    update_user as service_update_user,
    token_refresh as service_token_refresh,
    update_device_token as service_update_device_token,
    insert_init_info as service_insert_init_info,
    update_init_info as service_update_init_info,

)

from app.service.ads_app import (
    get_user_profile as service_get_user_profile,
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


# 카카오 로그인 API 엔드포인트
@router.post("/login/kakao")
def ads_login_kakao_route(request: KaKao):
    kakao_info = service_get_kakao_user_info(request.kakao_access_token)

    if not kakao_info or "id" not in kakao_info:
        raise HTTPException(status_code=401, detail="카카오 토큰이 유효하지 않습니다.")


    kakao_id = str(kakao_info["id"])
    kakao_account = kakao_info.get("kakao_account", {})

    email = kakao_account.get("email")

    provider = "kakao"
    user_id = service_get_user_by_provider(provider, kakao_id, email, request.device_token, request.installation_id)
    user_info = service_get_user_by_id(user_id)

    # if request.device_token:
    #     service_update_device_token(user_id, request.device_token, request.android_id)

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
            "provider": provider,
            "type": user_info["type"],
            "store_business_number": user_info.get("store_business_number", None)
        }
    }


# 구글 로그인 API 엔드포인트
@router.post("/login/google")
def ads_login_google_route(request: Google):
    google_info = service_get_google_user_info(request.google_access_token)

    if not google_info or "sub" not in google_info:
        raise HTTPException(status_code=401, detail="구글 토큰이 유효하지 않습니다.")

    google_id = str(google_info["sub"])
    email = google_info.get("email")

    provider = "google"
    user_id = service_get_user_by_provider(provider, google_id, email, request.device_token, request.installation_id)
    user_info = service_get_user_by_id(user_id)

    # if request.device_token:
    #     service_update_device_token(user_id, request.device_token, request.android_id)

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
            "provider" : provider,
            "type": user_info["type"],
            "store_business_number": user_info.get("store_business_number", None)
        }
    }


# 네이버 로그인 API 엔드포인트
@router.post("/login/naver")
def ads_login_naver_route(request: Naver):
    naver_info = service_get_naver_user_info(request.naver_access_token)

    if not naver_info or "id" not in naver_info:
        raise HTTPException(status_code=401, detail="네이버 토큰이 유효하지 않습니다.")

    naver_id = str(naver_info["id"])
    email = f"{naver_id}@naver.com"

    provider = "naver"
    user_id = service_get_user_by_provider(provider=provider, provider_id=naver_id, email=email, device_token = request.device_token)
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
            "provider": provider,
            "type": user_info["type"],
            "store_business_number": user_info.get("store_business_number", None)
        }
    }

# 네이버 로그인 콜백
@router.post("/naver/exchange")
def naver_exchange(request: NaverExchange):
    print(request)
    NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
    print("in")
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        raise HTTPException(500, "naver client env missing")

    # 1) 코드 -> 토큰
    token_res = requests.post(
        "https://nid.naver.com/oauth2.0/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "client_id": NAVER_CLIENT_ID,
            "client_secret": NAVER_CLIENT_SECRET,
            "code": request.code,
            "state": request.state or "",
            "redirect_uri": request.redirect_uri,
        },
        timeout=10,
    )
    token_json = token_res.json() if token_res.content else {}
    if token_res.status_code != 200 or "access_token" not in token_json:
        raise HTTPException(400, f"token_fail_{token_res.status_code}:{token_json.get('error','')}")

    # 2) 프로필 조회
    me_res = requests.get(
        "https://openapi.naver.com/v1/nid/me",
        headers={"Authorization": f"Bearer {token_json['access_token']}"},
        timeout=10,
    )
    me_json = me_res.json() if me_res.content else {}
    if me_res.status_code != 200 or me_json.get("resultcode") != "00":
        raise HTTPException(400, f"me_fail_{me_res.status_code}:{me_json.get('message','')}")

    profile = me_json.get("response", {})
    print(profile)
    # TODO: 여기서 회원 매핑/가입/로그인 처리 후 JWT 발급 등
    return {"success": True, "profile": profile}


# 자동 로그인 API 엔드포인트
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


@router.post("/token/refresh", response_model=TokenRefreshResponse)
def token_refresh(req: TokenRefreshRequest):
    return service_token_refresh(req.refresh_token)



@router.post("/update/user/store/info")
def update_user_store_info(request: UserUpdate):
    user_id = request.user_id
    store_business_number = request.store_business_number
    insta_account = request.insta_account
    register_tag = request.register_tag

    success = service_update_user(user_id, store_business_number, register_tag, insta_account )

    return {
        "success": success,  # 성공 여부
        "message": "유저 정보가 업데이트 되었습니다." if success else "유저 정보 업데이트에 실패했습니다."
    }

# 본인인증 후 user_info 저장/수정
@router.post("/update/init/info")
def update_init_info(request: InitUserInfo):
    user_id = request.user_id
    name = request.name
    birth = request.birth

    try:
        exists = service_get_user_profile(user_id)

        if exists:
            success = service_update_init_info(user_id, name, birth)
        else:
            success = service_insert_init_info(user_id, name, birth)
        return JSONResponse(content={
            "success": success
        })

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg)