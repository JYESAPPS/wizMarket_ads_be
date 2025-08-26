from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from uuid import uuid4
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime
import mimetypes
from typing import Optional, Dict, Any, List
from fastapi import Form, Response


router = APIRouter()

UPLOAD_DIR = Path("uploads/business")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/check/business/regist")
async def check_business_regist(file: UploadFile = File(...)):
    # (선택) 타입 간단 체크
    if file.content_type not in {
        "application/pdf", "image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"
    }:
        raise HTTPException(status_code=400, detail="PDF 또는 이미지 파일만 업로드 가능합니다.")

    # 저장 파일명: UUID_원본파일명
    safe_name = f"{uuid4().hex}_{Path(file.filename).name}"
    dest_path = UPLOAD_DIR / safe_name

    # 스트리밍 저장 (메모리 절약)
    size_bytes = 0
    with dest_path.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)  # 1MB씩 읽기
            if not chunk:
                break
            size_bytes += len(chunk)
            out.write(chunk)
    await file.close()

    return {
        "ok": True,
        "filename": file.filename,
        "saved_name": safe_name,
        "saved_path": str(dest_path),
        "content_type": file.content_type,
        "size_bytes": size_bytes,
    }


@router.get("/check/business/list")
def list_business_files():
    if not UPLOAD_DIR.exists():
        return {"ok": True, "files": []}

    items = []
    for p in UPLOAD_DIR.iterdir():
        if not p.is_file():
            continue
        stat = p.stat()
        mtime = stat.st_mtime
        content_type, _ = mimetypes.guess_type(p.name)
        # 업로드 시 UUID_원본파일명 형태라면 원본 표시용 추출
        original = p.name.split("_", 1)[1] if "_" in p.name else p.name

        items.append({
            "saved_name": p.name,                       # 실제 저장명
            "original_filename": original,              # 사람이 보기 좋은 이름
            "size_bytes": stat.st_size,
            "content_type": content_type or "application/octet-stream",
            "modified_at": datetime.fromtimestamp(mtime).isoformat(),
            "mtime_epoch": mtime                        # 정렬용
        })

    items.sort(key=lambda x: x["mtime_epoch"], reverse=True)
    for i in items:
        i.pop("mtime_epoch", None)

    return {"ok": True, "files": items}

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