from pydantic import BaseModel

class UserRegisterRequest(BaseModel):
    email: str
    temp_pw: str


class ImageListRequest(BaseModel):
    categoryId : int