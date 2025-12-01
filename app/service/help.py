import os, secrets
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, Union
from fastapi import UploadFile, HTTPException
from app.schemas.help import HelpCreate
from app.crud.help import insert_help


ALLOWED_MIME_PREFIX = "image/"
MAX_BYTES = 10 * 1024 * 1024  # 10MB

UPLOAD_ROOT = "/app/uploads"  # 이미 쓰던 값 재사용


def safe_ext(filename: str) -> str:
    # 간단 확장자 추출
    return os.path.splitext(filename)[1].lower() or ""


async def save_help_image(
    file: UploadFile,
) -> str:
    """
    1:1 문의용 이미지 업로드.

    - 실제 저장 경로: /app/uploads/help[/user_{user_id}]/파일명
    - 반환 값: DB용 상대 경로 (예: "help/20251201_142355_a1b2c3d4.png")
              또는 user 지정 시: "help/user_13/20251201_142355_a1b2c3d4.png"
    """

    if not file:
        return ""

    # MIME 타입 체크
    if not file.content_type or not file.content_type.startswith(ALLOWED_MIME_PREFIX):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")

    # 사이즈 제한 체크
    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="파일 용량은 최대 10MB 입니다.")

    # ───── 실제 저장 디렉토리 구성 ─────
    # 기본: /app/uploads/help
    # 옵션: /app/uploads/help/user_{user_id}
    parts = ["help"]

    # 디스크 상 실제 경로
    save_dir = os.path.join(UPLOAD_ROOT, *parts)
    os.makedirs(save_dir, exist_ok=True)

    # 파일명: 타임스탬프 + 랜덤 + 원본 확장자
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rand = secrets.token_hex(4)
    ext = safe_ext(file.filename or "")
    filename = f"{ts}_{rand}{ext}"

    save_path = os.path.join(save_dir, filename)

    # 실제 파일 쓰기
    with open(save_path, "wb") as f:
        f.write(contents)

    # DB에 저장할 상대 경로 ("help/...", OS 구분자 통일)
    storage_path = os.path.join(*parts, filename).replace("\\", "/")
    print(f"[HELP_UPLOAD] save_dir={save_dir}, filename={filename}")
    return storage_path

async def create_help(
    payload: HelpCreate,
    file1: Optional[UploadFile],
    file2: Optional[UploadFile],
    file3: Optional[UploadFile],
) -> Dict[str, Any]:

    a1 = await save_help_image(file1) if file1 else None
    a2 = await save_help_image(file2) if file2 else None
    a3 = await save_help_image(file3) if file3 else None

    safe_payload = payload.model_copy(update={"name": payload.name or ""})
    return insert_help(
        payload=safe_payload,
        attachments=(a1, a2, a3),
    )