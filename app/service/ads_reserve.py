from app.crud.ads_reserve import (
    insert_reserve as crud_insert_reserve,
    get_user_reserve_list as crud_get_user_reserve_list,
    update_reserve_status as crud_update_reserve_status,
    delete_reserve as crud_delete_reserve,
    update_reserve as crud_update_reserve
)


def insert_reserve(request):
    new_reserve  = crud_insert_reserve(request)
    return new_reserve 


def get_user_reserve_list(request):
    reserve_list = crud_get_user_reserve_list(request)
    return reserve_list


def update_reserve_status(request):
    success = crud_update_reserve_status(request)
    return success


def delete_reserve(request):
    success = crud_delete_reserve(request)
    return success


def update_reserve(request):
    success = crud_update_reserve(request)
    return success