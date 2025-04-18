from app.crud.ads_login import (
    ads_login as crud_ads_login,
)


def ads_login(user_id, password):
    user = crud_ads_login(user_id, password)
    return user is not None  # 로그인 성공 여부
