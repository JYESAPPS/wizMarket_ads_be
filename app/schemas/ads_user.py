from pydantic import BaseModel
from typing import Optional

class UserRegisterRequest(BaseModel):
    email: str
    temp_pw: str


class ImageListRequest(BaseModel):
    categoryId : int


class KaKao(BaseModel):
    kakao_access_token : str

class User(BaseModel):
    access_token : str


class UserUpdate(BaseModel):
    user_id : int
    store_business_number : str
    insta_account: Optional[str] = None