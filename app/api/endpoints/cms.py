from pathlib import Path
from uuid import uuid4
from fastapi.responses import FileResponse
from datetime import datetime
import mimetypes
from typing import Optional, Dict, Any, List
from fastapi import Form, Response
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, status
from pathlib import Path
from uuid import uuid4
from fastapi.responses import FileResponse
from app.schemas.cms import BVItem, BVListResponse, BVApproveResponse, BVRejectRequest, MarketingConsentIn
from fastapi import Query

from app.service.cms import (
    insert_business_verification as service_insert_business_verification,
    cms_list_verifications as service_cms_list_verifications,
    cms_approve_verification as service_cms_approve_verification,
    cms_reject_verification as service_cms_reject_verification,
    cms_get_user_list as service_cms_get_user_list,
    cms_get_user_detail as service_cms_get_user_detail,
    get_business_verification as service_get_business_verification,
    cms_marketing_agree as service_cms_marketing_agree,
)
from app.service.ads_app import (
    update_register_tag as service_update_register_tag
)
from app.service.ads_ticket import (
    get_valid_ticket as service_get_valid_ticket,
    get_token_deduction_history as service_get_token_deduction_history,
)

router = APIRouter()

UPLOAD_DIR = Path("app/uploads/business")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_filename(name: str) -> str:
    return Path(name).name.replace("\x00", "")

@router.post("/submit/business/regist")
async def check_business_regist(
    file: UploadFile = File(...),
    user_id: int = Form(...), 
    bs_name: str = Form(...),
    bs_number: str = Form(...),
):
    # (선택) 타입 체크
    if file.content_type not in {
        "application/pdf", "image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"
    }:
        raise HTTPException(status_code=400, detail="PDF 또는 이미지 파일만 업로드 가능합니다.")

    # 경로: uploads/business/{user_id}/{YYYY}/{MM}/UUID_원본명
    now = datetime.now()
    subdir = f"{user_id}/{now:%Y}/{now:%m}"
    user_dir = UPLOAD_DIR / subdir
    user_dir.mkdir(parents=True, exist_ok=True)

    original = sanitize_filename(file.filename or "upload.bin")
    saved_name = f"{uuid4().hex}_{original}"
    dest_path = user_dir / saved_name

    # 스트리밍 저장
    size_bytes = 0
    with dest_path.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size_bytes += len(chunk)
            out.write(chunk)
    await file.close()

    # DB 갱신 서비스 호출
    service_insert_business_verification(
        user_id,
        original,
        saved_name,
        str(dest_path),      # 가능하면 상대경로로 바꾸는 걸 권장
        file.content_type,
        size_bytes,
        bs_name,
        bs_number
    )

    return {"status": "pending"}


@router.get("/verification/list", response_model=BVListResponse)
def cms_list_verifications(
    request: Request,
    user_id: Optional[int] = None,
    status: Optional[str] = Query(None, pattern="^(pending|approved|rejected)$"),
    date_from: Optional[str] = None,  # '2025-08-01'
    date_to: Optional[str] = None,    # '2025-08-31'
    page: int = 1,
    page_size: int = 20,         # 관리자만 접근
):
    """
    관리자 전용 사업자등록증 제출 현황 목록.
    - 필터: user_id, status, 기간
    - 페이지네이션: page, page_size
    - 최신순 정렬
    """
    return service_cms_list_verifications(
        user_id=user_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )




@router.post("/verification/approve/{verification_id}", status_code=status.HTTP_204_NO_CONTENT)
def cms_approve_verification(
    request: Request,
    verification_id: int,
):
    """
    관리자 전용 사업자등록증 승인
    """
    service_cms_approve_verification(verification_id)



@router.post("/verification/reject/{verification_id}", status_code=status.HTTP_204_NO_CONTENT)
def cms_reject_verification(
    request: Request,
    verification_id: int,
    body: BVRejectRequest,
):
    """
    관리자 전용 사업자등록증 반려
    """
    service_cms_reject_verification(verification_id, body.notes)


@router.get("/get/user/list")
def cms_get_user_list():
    return service_cms_get_user_list()

@router.get("/get/user/detail")
def cms_get_user_detail(user_id: int):
    data = service_cms_get_user_detail(user_id)
    business = service_get_business_verification(user_id)
    ticket_info = service_get_valid_ticket(user_id)
    token_history = service_get_token_deduction_history(user_id)

    return {
        "detail": data,
        "business": business,
        "ticket_info": ticket_info,
        "token_history" : token_history,
    }

@router.post("/user/marketing_agree")
def cms_marketing_agree(body: MarketingConsentIn):
    affected = service_cms_marketing_agree(body.user_id, body.agree)
    return {"success": affected > 0}

@router.post("/user/register_tag")
def set_register_tag(user_id, register_tag):
    register_tag = service_update_register_tag(user_id, register_tag)
    return {"register_tag" : register_tag,}
