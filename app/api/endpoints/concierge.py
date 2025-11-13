from fastapi import APIRouter, HTTPException, status, UploadFile, File, Request, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
import logging
import os
from uuid import uuid4
from typing import List
from fastapi import UploadFile, File, Request

from app.schemas.concierge import (
    IsConcierge
) 
from app.service.concierge import (
    is_concierge as service_is_concierge,
    submit_concierge as service_submit_concierge,
    select_concierge_list as service_select_concierge_list,
    select_concierge_detail as service_select_concierge_detail
)

router = APIRouter()
logger = logging.getLogger(__name__)


# 존재 여부
@router.post("/is/concierge/store")
def check_concierge(request: IsConcierge):
    exists = not service_is_concierge(request)  # True면 이미 등록됨
    if exists:
        return {"success": False, "message": "이미 등록 된 컨시어지 매장입니다."}
    return {"success": True, "message": ""}


# 신청
UPLOAD_DIR = "uploads/concierge"  # 원하는 경로로 바꿔도 됨
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/submit/concierge")
async def submit_concierge(
    request: Request,
    images: List[UploadFile] = File(None),
):
    form = await request.form()

    # 1) 일반 필드 뽑기
    fields = {}
    from starlette.datastructures import UploadFile as StarletteUploadFile
    for key, value in form.items():
        if isinstance(value, (UploadFile, StarletteUploadFile)):
            continue
        fields[key] = value

    # 2) 서비스에 fields + 이미지 원본 그대로 넘김
    success, msg = await service_submit_concierge(fields, images or [])

    return {
        "success": success,
        "msg": msg,
    }


# 리스트 + 검색 조회
@router.get("/select/concierge/list")
def get_concierge_list(
    keyword: str | None = Query(None),
    search_field: str | None = Query(None),
    status: str | None = Query(None),
    apply_start: str | None = Query(None),
    apply_end: str | None = Query(None),
):
    rows = service_select_concierge_list(
        keyword=keyword,
        search_field=search_field,
        status=status,
        apply_start=apply_start,
        apply_end=apply_end,
    )
    return {"items": rows}


# 상세 페이지
@router.get("/select/concierge/detail/{user_id}")
def select_concierge_detail(user_id: int) -> Dict[str, Any]:
    """
    컨시어지 신청 상세 조회
    - 프론트: /admin/concierge/:id 에서 사용
    """
    detail = service_select_concierge_detail(user_id)
    return detail
