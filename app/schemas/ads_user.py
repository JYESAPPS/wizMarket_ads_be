from pydantic import BaseModel

class UserRegisterRequest(BaseModel):
    user_id: str
    password: str