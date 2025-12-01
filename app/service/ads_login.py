from app.crud.ads_login import (
    ads_login as crud_ads_login,
    get_category as crud_get_category,
    get_image_list as crud_get_image_list,
    get_user_by_provider as crud_get_user_by_provider,
    insert_user_sns as crud_insert_user_sns,
    upsert_user_device as crud_upsert_user_device,
    update_user_token as crud_update_user_token,
    get_user_by_id as crud_get_user_by_id,
    update_user as crud_update_user,
    select_insta_account as crud_select_insta_account,
    update_device_token as crud_update_device_token,
    select_user_id as crud_select_user_id,
    insert_init_info as crud_insert_init_info,
    update_init_info as crud_update_init_info,
    update_verified as crud_update_verified,
    get_permission_confirmed as crud_get_permission_confirmed,
    update_permission_confirmed as crud_update_permission_confirmed,
    check_install_id as crud_check_install_id,
    chect_logout_user_id as crud_logout_user_id,
    get_logout_user_by_id as crud_get_logout_user_by_id,
    update_logout_status as crud_update_logout_status,
    update_last_seen as crud_update_last_seen,
    insert_push as crud_insert_push,
    select_login_provider as crud_select_login_provider,
    select_business_name as crud_select_business_name,
)
from app.crud.ads_ticket import (
    get_latest_token_onetime as crud_get_latest_token_onetime,
    get_token_amount as crud_get_token_amount,
    insert_onetime as crud_insert_onetime,
)
import requests
from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import jwt, ExpiredSignatureError, JWTError
from typing import Optional
from fastapi import HTTPException
import re
import subprocess
import json
import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()




def check_install_id(install_id: str):
    install_id = install_id.strip()
    if not install_id:
        return False
    return crud_check_install_id(install_id)



def ads_login(email, temp_pw):
    user = crud_ads_login(email, temp_pw)
    return user 

def get_category():
    list = crud_get_category()
    return list


def get_image_list(category_id):
    list = crud_get_image_list(category_id)
    return list




def get_kakao_user_info(access_token: str) -> dict | None:
    url = "https://kapi.kakao.com/v2/user/me"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None



def get_google_user_info(id_token: str) -> dict | None:
    """
    구글 id_token을 검증하고 사용자 정보를 반환합니다.
    """
    url = "https://oauth2.googleapis.com/tokeninfo"
    params = {
        "id_token": id_token
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None


def get_naver_user_info(access_token: str) -> dict | None:
    """
    네이버 access_token을 이용해 사용자 정보를 반환합니다.
    """
    url = "https://openapi.naver.com/v1/nid/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        # API 형식: { "resultcode": "00", "message": "success", "response": { ... } }
        if data.get("resultcode") == "00":
            return data.get("response")  # ✅ 사용자 정보만 반환
    return None


secret_key = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7일
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 예: 30일


def create_access_token(data: dict):

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)

    

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)



# 로그아웃 유저인지 먼저 판별
def get_logout_user(installation_id: int):
    user_id = crud_logout_user_id(installation_id)

    user_info = crud_get_logout_user_by_id(user_id)


    return user_info


# 로그아웃 유저가 재로그인 시 status active로 전환
def update_logout_status(installation_id, device_token) -> bool:
    user_id = crud_logout_user_id(installation_id)
    if not user_id:
        return False

    success = crud_update_logout_status(user_id)
    if not success:
        return False

    result = crud_update_last_seen(device_token)
    return bool(result)



# 유저 조회 하거나 없으면 카카오로 회원가입
# def get_user_by_provider(provider: str, provider_id: str, email: str, device_token : str, installation_id : str):
def get_user_by_provider(provider: str, provider_id: str, email: str, provider_key: str | None = None):
    try:
        # 1) 사용자 조회
        user = crud_get_user_by_provider(provider, provider_id, provider_key)

        # 2) 없으면 SNS 가입
        if user:
            user_id = user["user_id"]
        else:
            if provider in {"kakao", "google", "naver", "apple"}:
                user_id = crud_insert_user_sns(email, provider, provider_id, provider_key)
                crud_insert_push(user_id)
            else:
                raise ValueError(f"지원하지 않는 provider: {provider}")

        # 3) 기기 업서트 (installation_id + 최신 토큰)
        # crud_upsert_user_device(user_id=user_id, installation_id=installation_id, device_token=device_token)

        return user_id

    except HTTPException:
        # 이미 포맷된 예외는 그대로 통과
        raise
    except Exception as e:
        # 로그에 전체 스택 기록
        print.error(f"Unexpected Error: {e}")
    
    


# 해당 유저 토큰 정보 DB 업데이트
def update_user_token(user_id: str, access_token: str, refresh_token: str):
    crud_update_user_token(user_id, access_token, refresh_token)


# JWT 토큰 디코딩
def decode_token(token: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알 수 없는 오류: {str(e)}")
    

# 토큰 갱신
def token_refresh(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, secret_key, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="토큰에 사용자 정보가 없습니다.")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="리프레시 토큰이 만료되었습니다.")
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.")

    user = get_user_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # DB에 저장된 refresh_token 과 비교 (선택사항)
    if user["refresh_token"] != refresh_token:
        raise HTTPException(status_code=403, detail="리프레시 토큰이 일치하지 않습니다.")

    # 새 토큰 발급
    new_access = create_access_token(data={"sub": str(user_id)})
    new_refresh = create_refresh_token(data={"sub": str(user_id)})

    update_user_token(user_id, new_access, new_refresh)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
    }


# 디바이스 토큰 항상 업데이트
def update_device_token(user_id: int, device_token: str, installation_id: Optional[str] = None, platform: Optional[str] = None):
    return crud_update_device_token(user_id, device_token, installation_id, platform)

# 첫 가입 시 user_push TB 인서트
def insert_push(user_id):
    # user TB 에 로그인 감지 (재로그인은)
    return crud_insert_push(user_id)


# last_seen 업데이트
def update_last_seen(device_token):
    return crud_update_last_seen(device_token)




# 유저 ID로 유저 정보 조회
def get_user_by_id(user_id: int):
    user = crud_get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    return user


# 회원 가입 로직
def update_user(user_id: int, store_business_number: str, register_tag: str, insta_account: Optional[str] = None, ):
    success = crud_update_user(user_id, store_business_number, register_tag, insta_account )

    if not success:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    
    try:
        ticket_id = 13
        token_amount = crud_get_token_amount(ticket_id)
        grant_date = date.today()
        token_onetime = crud_get_latest_token_onetime(user_id) + token_amount
        crud_insert_onetime(user_id, ticket_id, token_amount, token_onetime, grant_date)
    except Exception:
        # logger.exception("update_user: token grant failed", exc_info=True)
        raise HTTPException(status_code=500, detail="토큰 지급을 실패했습니다.")

    return success


venv_python = os.path.abspath(".venv/Scripts/python.exe")

def select_insta_account(store_business_number: str):
    insta_account = crud_select_insta_account(store_business_number)

    if not insta_account:
        return None

    try:
        result = subprocess.run(
            [venv_python, "insta.py", insta_account],  # ✅ 여기에 명시적으로 venv python
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode != 0:
            print("STDERR:", result.stderr)
            raise HTTPException(status_code=500, detail="크롤링 스크립트 실행 실패")

        stats = json.loads(result.stdout)
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"크롤링 실패: {str(e)}")



# 관리번호로 user_id 가져오기
def select_user_id(store_business_number):
    user_id = crud_select_user_id(store_business_number)
    return user_id

def select_login_provider(user_id):
    login_provider = crud_select_login_provider(user_id)
    return login_provider

def select_business_name(user_id):
    business_name = crud_select_business_name(user_id)
    # print(
    #     "[select_business_name] user_id:", user_id,
    #     "| value:", business_name,
    #     "| type:", type(business_name)
    # )

    return business_name

def update_init_info(user_id, name, birth):
    try:
        verified = crud_update_verified(user_id)
        user_info = crud_update_init_info(user_id, name, birth)
        return bool(verified) and bool(user_info)
    except Exception:
        return False
 
def insert_init_info(user_id, name, birth):
    try:
        verified = crud_update_verified(user_id)
        user_info = crud_insert_init_info(user_id, name, birth)
        return bool(verified) and bool(user_info)
    except Exception:
        return False


def get_permission_confirmed(user_id: int):
    return crud_get_permission_confirmed(user_id)

def update_permission_confirmed(install_id: str):
    return crud_update_permission_confirmed(install_id)

