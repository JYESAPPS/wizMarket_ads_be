from app.crud.ads_login import (
    ads_login as crud_ads_login,
    get_category as crud_get_category,
    get_image_list as crud_get_image_list
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

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)




def get_user_by_provider(provider: str, provider_id: str):
    # 이 함수는 provider와 provider_id를 사용하여 사용자 정보를 조회하는 로직을 구현해야 합니다.
    # 예시로, provider가 "kakao"인 경우 카카오 사용자 정보를 조회하는 로직을 작성할 수 있습니다.
    # 실제 구현은 데이터베이스나 다른 서비스와의 연동에 따라 달라질 수 있습니다.
    pass