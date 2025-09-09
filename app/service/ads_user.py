from crud.ads_user import (
    check_user_id as crud_check_user_id,
    register_user as crud_register_user,
    get_store as crud_get_store,
    insert_business_info as crud_insert_business_info,
    update_user as crud_update_user
)

from crud.ads_app import (
    update_register_tag as crud_update_register_tag,
)



def check_user_id(user_id):
    exists = crud_check_user_id(user_id)
    return exists

def register_user(user_id, password):
    crud_register_user(user_id, password)

# 매장 조회
def get_store(store_name, road_name):
    return crud_get_store(store_name, road_name)

# 기존 매장 관련 정보 등록
def register_store_info(request):
    user_id = request.user_id

    # 사업자 정보 (번호, 대표자)는 business_verification
    success1 = crud_insert_business_info(user_id, request.business_name, request.business_number)

    # store_business_number를 userTB에 업데이트
    success2 = crud_update_user(user_id, request.store_business_number)

    # register_tag를 user_info TB에 업데이트
    success3 = crud_update_register_tag(user_id, request.register_tag)

    return success1 and success2 and success3