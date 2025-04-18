from crud.ads_user import (
    check_user_id as crud_check_user_id,
    register_user as crud_register_user
)



def check_user_id(user_id):
    exists = crud_check_user_id(user_id)
    return exists

def register_user(user_id, password):
    crud_register_user(user_id, password)
