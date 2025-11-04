from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class LoginIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    must_change_password: bool

class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class CreateAdminIn(BaseModel):
    username: str
    email: EmailStr | None = None
    role: str = Field(pattern="^(SUPER|MANAGER|STAFF)$", default="STAFF")
    temp_password: str = Field(min_length=8)



class CreateSubAdmin(BaseModel):
    is_active :int
    role: str = Field(pattern="^(SUPER|MANAGER|STAFF)$", default="STAFF")
    name: str
    admin_id : str
    phone : str
    temp_password: str = Field(min_length=8)
    email : str
    department : Optional[str]
    position : Optional[str]



class UpdateAdminInfo(BaseModel):
    is_active: Optional[int]
    role : Optional[str]
    name: Optional[str]
    phone: Optional[str]
    email:  Optional[str]
    department: Optional[str]
    position: Optional[str]