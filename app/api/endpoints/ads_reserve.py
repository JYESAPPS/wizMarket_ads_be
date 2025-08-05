# app/api/fcm_push.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.service.ads_reserve import (
    insert_reserve as service_insert_reserve,
    get_user_reserve_list as service_get_user_reserve_list,
    update_reserve_status as service_update_reserve_status
)
from app.schemas.ads_reserve import (
    ReserveCreate, ReserveGet, ReserveUpdateStatus
)

router = APIRouter()


@router.post("/insert")
def insert_reserve(request: ReserveCreate):
    status = service_insert_reserve(request)
    return {"status": status}


@router.post("/get/user/list")
def get_user_reserve_list(request : ReserveGet):
    reserve_list = service_get_user_reserve_list(request)
    return reserve_list


@router.post("/update/status")
def update_reserve_status(req: ReserveUpdateStatus):
    success = service_update_reserve_status(req)
    return {"success": success}



