from fastapi import APIRouter, HTTPException, status, UploadFile, File, Request, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
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
    select_concierge_list as service_select_concierge_list
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
    for key, value in form.items():
        from starlette.datastructures import UploadFile as StarletteUploadFile
        if isinstance(value, (UploadFile, StarletteUploadFile)):
            continue
        fields[key] = value

    # ─ 이미지 처리 ──────────────────────────────
    image_paths = {}  # {"image_1": "...", "image_2": "..."}
    if images:
        for idx, img in enumerate(images[:6], start=1):  # 최대 6장
            # 확장자 추출
            _, ext = os.path.splitext(img.filename)
            ext = ext.lower() or ".jpg"

            # 파일명 생성 (UUID 등)
            filename = f"{uuid4().hex}_{idx}{ext}"
            save_path = os.path.join(UPLOAD_DIR, filename)

            # 실제 파일 저장
            # with open(save_path, "wb") as f:
            #     content = await img.read()
            #     f.write(content)

            # image_1, image_2 형태로 할당
            image_key = f"image_{idx}"
            image_paths[image_key] = save_path  # 또는 URL

    success, msg = service_submit_concierge(fields, image_paths)

    return {
        "success": success,
        "msg" : msg
    }



@router.get("/select/concierge/list")
async def select_concierge_list(
    keyword: Optional[str] = Query(
        None,
        description="이름 / 매장명 / 도로명 통합 검색어",
    ),
):
    """
    컨시어지 신청 리스트 조회용 엔드포인트 (어드민용)
    GET /select/concierge/list?keyword=...
    """
    items = service_select_concierge_list(keyword=keyword)
    return {
        "items": items,
        "count": len(items),
    }
