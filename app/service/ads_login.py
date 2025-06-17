from app.crud.ads_login import (
    ads_login as crud_ads_login,
)


def ads_login(email, temp_pw):
    user = crud_ads_login(email, temp_pw)
    return user 
