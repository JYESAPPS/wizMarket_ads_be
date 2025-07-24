from app.crud.ads_login import (
    ads_login as crud_ads_login,
    get_category as crud_get_category,
    get_image_list as crud_get_image_list,
    get_user_by_provider as crud_get_user_by_provider,
    insert_user_kakao as crud_insert_user_kakao,
    update_user_token as crud_update_user_token,
    get_user_by_id as crud_get_user_by_id
)
import requests
from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import jwt, JWTError


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


SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7일
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 예: 30일


def create_access_token(data: dict):

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# 유저 조회 하거나 없으면 카카오로 회원가입
def get_user_by_provider(provider: str, provider_id: str, email: str):
    user = crud_get_user_by_provider(provider, provider_id)
    if user is None:
        user_id = crud_insert_user_kakao(email, "kakao", provider_id)
    else:
        user_id = user["user_id"]

    return user_id


# 해당 유저 토큰 정보 DB 업데이트
def update_user_token(user_id: str, access_token: str, refresh_token: str):
    crud_update_user_token(user_id, access_token, refresh_token)


# JWT 토큰 디코딩
def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알 수 없는 오류: {str(e)}")
    


# 유저 ID로 유저 정보 조회
def get_user_by_id(user_id: int):
    user = crud_get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    return user