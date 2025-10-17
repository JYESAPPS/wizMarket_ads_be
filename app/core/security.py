import os, bcrypt, uuid, datetime as dt, hashlib
from typing import Tuple
from jose import jwt, JWTError, ExpiredSignatureError


JWT_SECRET   = os.getenv("JWT_SECRET", "dev-secret-change-me")
ALGO         = "HS256"
ACCESS_MIN   = int(os.getenv("JWT_ACCESS_MIN", "30"))
REFRESH_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "7"))

print("[BOOT] JWT_SECRET_HASH=", hashlib.sha256(JWT_SECRET.encode()).hexdigest()[:10])

def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()

def hash_token(raw: str) -> str:
    """긴 토큰은 bcrypt 대신 SHA-256(hex)로 저장"""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode(), hashed.encode())
    except Exception:
        return False

def _ts(dt_obj: dt.datetime) -> int:
    # UTC 기준 epoch seconds
    return int(dt_obj.replace(tzinfo=dt.timezone.utc).timestamp())

# app/core/security.py

def make_tokens(user_id: int, role: str) -> Tuple[str, str, str, dt.datetime, dt.datetime]:
    now  = dt.datetime.utcnow()
    aexp = now + dt.timedelta(minutes=ACCESS_MIN)
    rexp = now + dt.timedelta(days=REFRESH_DAYS)
    sid  = str(uuid.uuid4())

    access_payload = {
        "sub": str(user_id),   # ✅ 정수 → 문자열
        "role": role,
        "sid": sid,
        "exp": _ts(aexp),
    }
    refresh_payload = {
        "sub": str(user_id),   # ✅ 정수 → 문자열
        "sid": sid,
        "typ": "refresh",
        "exp": _ts(rexp),
    }

    access  = jwt.encode(access_payload, JWT_SECRET, algorithm=ALGO)
    refresh = jwt.encode(refresh_payload, JWT_SECRET, algorithm=ALGO)
    return access, refresh, sid, aexp, rexp


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGO], options={"verify_aud": False})
    except ExpiredSignatureError as e:
        # 만료는 401로 처리할 수 있게 명확한 예외 메시지 제공
        raise e
    except JWTError as e:
        # 서명/형식 문제
        raise e
