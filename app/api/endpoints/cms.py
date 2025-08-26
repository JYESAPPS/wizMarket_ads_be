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


# 공지사항
NOTICES: List[Dict[str, Any]] = []
AUTO_ID = 1

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def to_public(n: Dict[str, Any]) -> Dict[str, Any]:
    m = n.copy()
    m.pop("image_bytes", None)
    m.pop("image_mime", None)
    return m

@router.get("/notice", response_model=List[Dict[str, Any]])
def list_notices():
    return [to_public(n) for n in NOTICES[::-1]]

@router.get("/notice/{notice_id}", response_model=Dict[str, Any])
def get_notice(notice_id: int):
    for n in NOTICES:
        if n["id"] == notice_id:
            return to_public(n)
    raise HTTPException(status_code=404, detail="Notice not found")

@router.post("/notice", response_model=Dict[str, Any])
async def create_notice(
    title: str = Form(...),
    content: str = Form(...),
    file: Optional[UploadFile] = File(default=None),
):
    global AUTO_ID
    item = {
        "id": AUTO_ID,
        "title": title.strip(),
        "content": content.strip(),
        "image_name": None,
        "image_mime": None,
        "image_bytes": None,
        "created_at": now_str(),
        "updated_at": now_str(),
    }
    if file:
        data = await file.read()
        item["image_name"] = file.filename
        item["image_mime"] = file.content_type or "application/octet-stream"
        item["image_bytes"] = data

    AUTO_ID += 1
    NOTICES.append(item)
    return to_public(item)

@router.put("/notice/{notice_id}", response_model=Dict[str, Any])
async def update_notice(
    notice_id: int,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(default=None),  # ← 추가
):
    for n in NOTICES:
        if n["id"] == notice_id:
            if title is not None:
                n["title"] = title.strip()
            if content is not None:
                n["content"] = content.strip()
            if file is not None:
                data = await file.read()
                n["image_name"] = file.filename
                n["image_mime"] = file.content_type or "application/octet-stream"
                n["image_bytes"] = data
            n["updated_at"] = now_str()
            return to_public(n)
    raise HTTPException(status_code=404, detail="Notice not found")

@router.delete("/notice/{notice_id}")
def delete_notice(notice_id: int):
    global NOTICES
    before = len(NOTICES)
    NOTICES = [n for n in NOTICES if n["id"] != notice_id]
    if len(NOTICES) == before:
        raise HTTPException(status_code=404, detail="Notice not found")
    return {"ok": True}

@router.get("/notice/{notice_id}/image")
def get_notice_image(notice_id: int):
    for n in NOTICES:
        if n["id"] == notice_id:
            data = n.get("image_bytes")
            mime = (n.get("image_mime") or "application/octet-stream")
            if data:
                return Response(content=data, media_type=mime)
            raise HTTPException(status_code=404, detail="Image not found")
    raise HTTPException(status_code=404, detail="Notice not found")