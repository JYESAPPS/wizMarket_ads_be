from pydantic import BaseModel
from typing import Optional

class UserRegisterRequest(BaseModel):
    email: str
    temp_pw: str

class StoreMatch(BaseModel):
    store_name: str
    road_name: str

class StoreAddInfo(BaseModel):
    user_id: int
    business_name: str
    business_number: str
    register_tag: str
    store_business_number: str
    road_name: str
    status: str  

class ImageListRequest(BaseModel):
    categoryId : int


class KaKao(BaseModel):
    kakao_access_token : str
    email : str = None
    device_token : str = None
    # android_id : str = None
    # installation_id : str = None


class Google(BaseModel):
    google_access_token : str
    email : str
    device_token : str = None
    # installation_id : str = None

class Naver(BaseModel):
    naver_access_token : str
    device_token : str = None

class NaverExchange(BaseModel):
    code: str = None
    state: str  = None
    redirect_uri: str = None

class User(BaseModel):
    access_token : str
    device_token : str = None


class UserUpdate(BaseModel):
    user_id : int
    store_business_number : str
    register_tag : str
    insta_account: Optional[str] = None
    
class InitUserInfo(BaseModel):
    user_id : int
    name: str
    birth: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str

class DeviceRegister(BaseModel):
    install_id: str
    push_token: str
