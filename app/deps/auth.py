# app/deps/auth.py
from fastapi import Depends, Header, HTTPException, status
from app.core.security import decode_token
from app.crud.admin_user import get_user_by_id

def get_current_admin(authorization: str = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "인증 필요")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except Exception as e:
        print("[AUTH][decode_error]", type(e).__name__, str(e))
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "토큰 오류")
    user = get_user_by_id(int(payload["sub"]))
    if not user or not user.get("is_active"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "유효하지 않은 계정")
    user["_role_token"] = payload.get("role")
    user["_sid_token"] = payload.get("sid")
    return user

def require_role(*allowed: str):
    def dep(user = Depends(get_current_admin)):
        if user.get("role") not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "권한이 없습니다.")
        return user
    return dep
