import os, secrets
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, Union
from fastapi import UploadFile, HTTPException
from app.schemas.help import HelpCreate
from app.crud.help import insert_help


ALLOWED_MIME_PREFIX = "image/"
MAX_BYTES = 10 * 1024 * 1024  # 10MB

UPLOAD_BASE_DIR = Path(os.getenv("HELP_UPLOAD_DIR", "../uploads/help"))
UPLOAD_BASE_DIR.mkdir(parents=True, exist_ok=True)

def ensure_dir(path: Union[str, Path]) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)

def safe_ext(filename: str) -> str:
    # 간단 확장자 추출 (보안상 실제 환경은 mimetypes/검증 강화 권장)
    return os.path.splitext(filename)[1].lower() or ""

async def save_image(
    file: UploadFile,
    base_dir: Path,
) -> str:
    if not file:
        return ""
    if not file.content_type or not file.content_type.startswith(ALLOWED_MIME_PREFIX):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")

    # 사이즈 제한 체크
    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="파일 용량은 최대 10MB 입니다.")

    ensure_dir(base_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rand = secrets.token_hex(4)
    ext = safe_ext(file.filename)
    fname = f"{ts}_{rand}{ext}"
    fpath = base_dir / fname

    fpath.write_bytes(contents)  # Path 방식

    # DB에는 상대경로/정적서빙 경로로 저장하려면 여기서 변환
    return str(fpath)

async def create_help(
    payload: HelpCreate,
    file1: Optional[UploadFile],
    file2: Optional[UploadFile],
    file3: Optional[UploadFile],
) -> Dict[str, Any]:
    if not payload.consent_personal:
        raise HTTPException(status_code=400, detail="개인정보 처리 동의가 필요합니다.")

    a1 = await save_image(file1, UPLOAD_BASE_DIR) if file1 else None
    a2 = await save_image(file2, UPLOAD_BASE_DIR) if file2 else None
    a3 = await save_image(file3, UPLOAD_BASE_DIR) if file3 else None

    return insert_help(
        payload=payload,
        attachments=(a1, a2, a3),
    )