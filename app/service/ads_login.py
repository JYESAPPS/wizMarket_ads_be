from app.crud.ads_login import (
    ads_login as crud_ads_login,
    get_category as crud_get_category,
)


def ads_login(email, temp_pw):
    user = crud_ads_login(email, temp_pw)
    return user 

def get_category():
    list = crud_get_category()
    return list