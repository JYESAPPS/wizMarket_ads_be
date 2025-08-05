from app.crud.ads_reserve import (
    insert_reserve as crud_insert_reserve,
    get_user_reserve_list as crud_get_user_reserve_list,
    update_reserve_status as crud_update_reserve_status
)


def insert_reserve(request):
    status = crud_insert_reserve(request)
    return status


def get_user_reserve_list(request):
    reserve_list = crud_get_user_reserve_list(request)
    return reserve_list


def update_reserve_status(request):
    success = crud_update_reserve_status(request)
    return success