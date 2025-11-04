# app/services/kcb_token.py
import os
import uuid
import time
import requests
import logging
from app.core.settings import settings, OAUTH_URL

log = logging.getLogger("kcb")
_token_cache = {"access_token": None, "exp_ts": 0}

def get_access_token() -> str:
    now = time.time()
    if _token_cache["access_token"] and _token_cache["exp_ts"] - 60 > now:
        return _token_cache["access_token"]

    payload = {
        "grant_type": "client_credentials",
        "scope": "ids",
        "site_cd": settings.KCB_SITE_CD,
        "client_id": settings.KCB_CLIENT_ID,
        "client_secret": settings.KCB_CLIENT_SECRET,
    }
    headers = {
        # 👇 폼 전송으로 변경 (중요)
        "Content-Type": "application/x-www-form-urlencoded",
        "x-api-tran-id": uuid.uuid4().hex[:32],
    }

    insecure = os.getenv("KCB_SSL_INSECURE", "false").lower() == "true"
    if insecure:
        log.warning("[KCB OAuth] SSL verify=False (개발 임시 우회). 운영 전 반드시 해제하세요.")

    # 👇 json= 이 아니라 data= 로 전송
    resp = requests.post(
        OAUTH_URL,
        data=payload,
        headers=headers,
        timeout=10,
        verify=not insecure,
    )

    # ✅ 실패 원인 바로 보이게
    if resp.status_code >= 400:
        try:
            body = resp.json()
        except Exception:
            body = {"raw": resp.text}
        log.error(f"[KCB OAuth] HTTP {resp.status_code} body={body}")
        raise RuntimeError(f"OAuth HTTP {resp.status_code}: {body}")

    data = resp.json()
    access_token = data.get("access_token")
    expires_in = int(data.get("expires_in", 300))
    if not access_token:
        log.error(f"[KCB OAuth] access_token 없음, body={data}")
        raise RuntimeError("KCB OAuth: access_token 없음")

    _token_cache["access_token"] = access_token
    _token_cache["exp_ts"] = now + expires_in
    log.info(f"[KCB OAuth] success, expires_in={expires_in}s")
    return access_token
