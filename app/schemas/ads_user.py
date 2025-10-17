from pydantic import BaseModel, Field
from typing import Optional, List


class InstallCheckResponse(BaseModel):
    exists: bool


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


class AddRequest(BaseModel):

    road_name : str

    user_id: int

    large_category_code: str 
    medium_category_code: str 
    small_category_code: str

    store_name: str 
    

    business_name: str
    business_number: str

    status: str  # 예: pending, approved, rejected
    register_tag: Optional[str] = None
    



class SNSAccount(BaseModel):
    channel: str = Field(..., description="채널명 (인스타그램/블로그/페이스북/X/네이버밴드 등)")
    account: str = Field(..., description="계정 ID 또는 URL")

class SNSRegisterRequest(BaseModel):
    user_id: int
    status: str = Field(..., description="유저 상태, 예: active")
    accounts: Optional[List[SNSAccount]] = None


class UserDelete(BaseModel):
    user_id: str




class ImageListRequest(BaseModel):
    categoryId : int


class KaKao(BaseModel):
    kakao_access_token : str
    email : str = None
    device_token : str = None
    installation_id : str = None
    platform : str = None

class Google(BaseModel):
    google_access_token : str
    email : str
    device_token : str = None
    installation_id : str = None
    platform : str = None
    
class Apple(BaseModel):
    apple_access_token : str
    email : str
    device_token : str = None
    installation_id : str = None
    platform : str = None

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

class UserStop(BaseModel):
    user_id: int
    reason: Optional[str] = None

class UserUnstop(BaseModel):
    user_id: int

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
