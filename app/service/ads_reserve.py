from app.crud.ads_reserve import (
    insert_reserve as crud_insert_reserve
)


def insert_reserve(request):
    status = crud_insert_reserve(request)
    return status