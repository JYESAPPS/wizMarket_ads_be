from crud.ads_user import (
    check_user_id as crud_check_user_id,
    register_user as crud_register_user,
    get_store as crud_get_store,
)



def check_user_id(user_id):
    exists = crud_check_user_id(user_id)
    return exists

def register_user(user_id, password):
    crud_register_user(user_id, password)

# 매장 조회
def get_store(store_name, road_name):
    return crud_get_store(store_name, road_name)