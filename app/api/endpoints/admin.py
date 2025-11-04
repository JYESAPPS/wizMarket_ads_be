# app/routers/cms_auth.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.crud.admin_user import get_user_by_username, set_password, touch_last_login, create_admin_user
from app.service.admin import (
    get_admin_list as service_get_admin_list,
    create_admin_user as service_create_admin_user,
    delete_admin as service_delete_admin,
    get_admin_detail as service_get_admin_detail,
    update_admin_info as service_update_admin_info
)
from app.crud.admin_session import insert_session
from app.core.security import verify_password, make_tokens, hash_password
from app.deps.auth import get_current_admin, require_role
from pydantic import BaseModel, EmailStr, Field
from app.schemas.admin import (
    CreateSubAdmin, UpdateAdminInfo
)

router = APIRouter(prefix="/admin", tags=["CMS Auth"])

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

@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request):
    user = get_user_by_username(body.username)
    if not user or not user["is_active"] or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "아이디 또는 비밀번호가 올바르지 않습니다.")
    access, refresh, sid, _, _ = make_tokens(user["id"], user["role"])
    insert_session(
        user_id=user["id"],
        session_id=sid,
        refresh_token_raw=refresh,
        ip=(request.client.host if request.client else None),
        ua=request.headers.get("user-agent")
    )
    touch_last_login(user["id"])
    return TokenOut(access_token=access, refresh_token=refresh, must_change_password=bool(user["must_change_password"]))

@router.get("/me")
def me(current = Depends(get_current_admin)):
    return {
        "id": current["id"],
        "username": current["username"],
        "email": current["email"],
        "role": current["role"],
        "must_change_password": bool(current["must_change_password"]),
    }

@router.post("/change/password")
def change_password(body: ChangePasswordIn, current = Depends(get_current_admin)):
    if not verify_password(body.old_password, current["password_hash"]):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "현재 비밀번호가 올바르지 않습니다.")
    set_password(current["id"], body.new_password)
    return {"ok": True}



class CreateAdminIn(BaseModel):
    username: str
    email: EmailStr | None = None
    role: str = Field(pattern="^(SUPER|MANAGER|STAFF)$", default="STAFF")
    temp_password: str = Field(min_length=8)

@router.post("/users", dependencies=[Depends(require_role("SUPER"))])
def create_admin(body: CreateAdminIn):
    if get_user_by_username(body.username):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "이미 존재하는 아이디입니다.")
    uid = create_admin_user(body.username, body.email, body.role, body.temp_password)
    return {"id": uid, "username": body.username, "role": body.role, "must_change_password": True}



@router.get("/list")
def get_admin_list():
    return service_get_admin_list()


# 관리자 계정 부여
@router.post("/list/create")
def create_admin_user(payload: CreateSubAdmin):
    return service_create_admin_user(data=payload)

# 관리자 삭제
@router.post("/delete/{id}")
def delete_admin(admin_id):
    return service_delete_admin(admin_id)

# 관리자 상세보기
@router.get("/{admin_id}")
def get_admin_detail(admin_id):
    return service_get_admin_detail(admin_id)


# 관리자 정보 업데이트
@router.post("/update/{admin_id}")
def update_admin(admin_id, request : UpdateAdminInfo):
    return service_update_admin_info(admin_id, request)