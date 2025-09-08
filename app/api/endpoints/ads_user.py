from fastapi import APIRouter, Request
from app.schemas.ads_user import (
    UserRegisterRequest, StoreMatch,
)

from app.service.ads_user import (
    check_user_id as service_check_user_id,
    register_user as service_register_user,
    get_store as service_get_store,
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
    
# 본인인증 후 user_info 적용 여기로 데려올까 (현재 ads_login에 있음)

# 매장 정보 검색 : 있으면 목록 반환, 없으면 null 반환
@router.post("/store/match")
def match_store(request: StoreMatch):
    try: 
        store_name = request.store_name
        road_name = request.road_name

        store_info = service_get_store(store_name, road_name)

        if not store_info:
            return None

        return store_info
    except Exception as e:
        print(f"중복 검사 오류: {e}")
        return {"available": False}