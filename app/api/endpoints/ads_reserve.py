# app/api/fcm_push.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.service.ads_reserve import (
    insert_reserve as service_insert_reserve
)
from app.schemas.ads_reserve import ReserveCreate

router = APIRouter()


@router.post("/insert")
def insert_reserve(request: ReserveCreate):
    status = service_insert_reserve(request)
    return {"status": status}