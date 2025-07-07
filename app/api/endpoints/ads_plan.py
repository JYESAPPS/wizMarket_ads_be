from fastapi import APIRouter, HTTPException, status
from app.schemas.ads_plan import (
    InsertFeeRequest
)

from app.service.ads_plan import (
    get_plan_list as service_get_plan_list,
    insert_fee as service_insert_fee
)


router = APIRouter()



# 요금제 불러오기
@router.get("/list")
def get_plan_list():
    list = service_get_plan_list()

    return list

# 요금제 등록
@router.post("/save")
def insert_fee(request: InsertFeeRequest):
   service_insert_fee(request)

    