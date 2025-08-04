from pydantic import BaseModel
from typing import Optional

class UserRegisterRequest(BaseModel):
    email: str
    temp_pw: str


class ImageListRequest(BaseModel):
    categoryId : int


class KaKao(BaseModel):
    kakao_access_token : str
    device_token : str = None


class Google(BaseModel):
    google_access_token : str
    device_token : str = None

class Naver(BaseModel):
    naver_access_token : str
    device_token : str = None


class User(BaseModel):
    access_token : str


class UserUpdate(BaseModel):
    user_id : int
    store_business_number : str
    custom_menu : str
    insta_account: Optional[str] = None
    



class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str