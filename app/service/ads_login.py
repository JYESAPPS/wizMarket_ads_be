from app.crud.ads_login import (
    ads_login as crud_ads_login,
    get_category as crud_get_category,
    get_image_list as crud_get_image_list,
    get_user_by_provider as crud_get_user_by_provider,
    insert_user_kakao as crud_insert_user_kakao,
    update_user_token as crud_update_user_token
)
import requests
from datetime import datetime, timedelta
from jose import jwt

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



def get_user_by_provider(provider: str, provider_id: str, email: str):
    user = crud_get_user_by_provider(provider, provider_id)
    if user is None:
        user_id = crud_insert_user_kakao(email, "kakao", provider_id)
    else:
        user_id = user["user_id"]

    return user_id


def update_user_token(user_id: str, access_token: str, refresh_token: str):
    crud_update_user_token(user_id, access_token, refresh_token)