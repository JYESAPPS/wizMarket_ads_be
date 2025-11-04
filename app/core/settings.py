# app/core/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict  # ✅ 변경점
# (주의) from pydantic import BaseSettings  ← 이제 쓰면 안 됨

class Settings(BaseSettings):
    KCB_SITE_CD: str
    KCB_CLIENT_ID: str
    KCB_CLIENT_SECRET: str
    KCB_SITE_NAME: str = "OurService"
    KCB_SITE_URL: str = "https://our.service.com"
    KCB_ENV: str = "test"  # test | prod
    # ✅ 추가
    KCB_ENC_ALGO_CD: str = "SEED"
    KCB_ENC_IV: str = "0000000000000000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# KCB 엔드포인트 구성
# app/core/settings.py

if settings.KCB_ENV == "prod":
    OAUTH_URL = "https://api.ok-name.co.kr:20443/v1/oauth2/access_token"   # ✅ co.kr
    POPUP_START_URL = "https://api.ok-name.co.kr:20443/v1/id/phone/popup-start"
else:
    OAUTH_URL = "https://tapi.ok-name.co.kr:40443/v1/oauth2/access_token"  # ✅ co.kr
    POPUP_START_URL = "https://tapi.ok-name.co.kr:40443/v1/id/phone/popup-start"

