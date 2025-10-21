# app/api/fcm_push.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.service.ads_reserve import (
    insert_reserve as service_insert_reserve,
    get_user_reserve_list as service_get_user_reserve_list,
    update_reserve_status as service_update_reserve_status,
    delete_reserve as service_delete_reserve,
    update_reserve as service_update_reserve,
    get_reserve_push as service_get_reserve_push,
    update_push_consent as service_update_push_consent,
)
from app.schemas.ads_reserve import (
    ReserveCreate, ReserveGet, ReserveUpdateStatus, ReserveDelete, ReserveUpdate,
    DeviceData,
)

router = APIRouter()


@router.post("/insert")
def insert_reserve(request: ReserveCreate):
    new_reserve  = service_insert_reserve(request)
    return new_reserve


@router.post("/get/user/list")
def get_user_reserve_list(request : ReserveGet):
    reserve_list = service_get_user_reserve_list(request)
    return reserve_list

# 예약 푸시 알림 수신 여부 확인
@router.post("/get/push")
def get_reserve_push(request: DeviceData):
    push_consent = service_get_reserve_push(request)
    return {"push_consent": push_consent}

# 예약 알림 수신 여부 수정
@router.post("/update/push")
def update_push_consent(request: DeviceData):
    success = service_update_push_consent(request)
    return {"success": success}

@router.post("/update/status")
def update_reserve_status(req: ReserveUpdateStatus):
    success = service_update_reserve_status(req)
    return {"success": success}



@router.post("/delete")
def delete_reserve(request: ReserveDelete):
    success = service_delete_reserve(request)
    return {"success": success}


@router.post("/update")
def update_reserve(req: ReserveUpdate):
    new_reserve = service_update_reserve(req)
    return new_reserve


