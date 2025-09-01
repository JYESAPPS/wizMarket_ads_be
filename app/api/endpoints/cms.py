from pathlib import Path
from uuid import uuid4
from fastapi.responses import FileResponse
from datetime import datetime
import mimetypes
from typing import Optional, Dict, Any, List
from fastapi import Form, Response
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from pathlib import Path
from uuid import uuid4
from fastapi.responses import FileResponse
from app.schemas.cms import BVItem, BVListResponse
from fastapi import Query

from app.service.cms import (
    insert_business_verification as service_insert_business_verification,
    cms_list_verifications as service_cms_list_verifications
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

@router.get("/check/business/file/{saved_name}")
def get_business_file(saved_name: str):
    # 경로 역참조 방지
    name = Path(saved_name).name
    path = UPLOAD_DIR / name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="파일이 없습니다.")
    content_type, _ = mimetypes.guess_type(path.name)
    return FileResponse(
        path,
        media_type=content_type or "application/octet-stream",
        filename=path.name
    )


