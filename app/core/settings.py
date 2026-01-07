# app/core/settings.py
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # ✅ KCB (선택값 – 없으면 비활성)
    KCB_SITE_CD: Optional[str] = None
    KCB_CLIENT_ID: Optional[str] = None
    KCB_CLIENT_SECRET: Optional[str] = None

    KCB_SITE_NAME: str = "OurService"
    KCB_SITE_URL: str = "https://our.service.com"
    KCB_ENV: str = "test"  # test | prod

    KCB_ENC_ALGO_CD: str = "SEED"
    KCB_ENC_IV: str = "0000000000000000"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()

# ✅ KCB 엔드포인트 (환경별)
if settings.KCB_ENV == "prod":
    OAUTH_URL = "https://api.ok-name.co.kr:20443/v1/oauth2/access_token"
    POPUP_START_URL = "https://api.ok-name.co.kr:20443/v1/id/phone/popup-start"
else:
    OAUTH_URL = "https://tapi.ok-name.co.kr:40443/v1/oauth2/access_token"
    POPUP_START_URL = "https://tapi.ok-name.co.kr:40443/v1/id/phone/popup-start"