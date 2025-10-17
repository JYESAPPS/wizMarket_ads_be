from app.crud.ads_notice import (
    get_notice as crud_get_notice,
    create_notice as crud_create_notice,
    update_notice as crud_update_notice,
    delete_notice as crud_delete_notice,
    get_notice_read as crud_get_notice_read,
    insert_notice_read as crud_insert_notice_read,
    update_notice_set_file as crud_update_notice_set_file,
    update_notice_clear_file as crud_update_notice_clear_file,
    notice_views as crud_notice_views,
)

from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, Request
import logging, os
from uuid import uuid4
import imghdr

_TRUTHY = {"1","true","t","y","yes","on"}

def _as_bool(v) -> bool:
    if isinstance(v, bool): return v
    if v is None: return False
    return str(v).strip().lower() in _TRUTHY

def get_notice(
    request: Request | None = None,
    *,
    is_admin: bool | None = None,  # 내부/테스트용 오버라이드
):
    """
    판정 우선순위:
    1) is_admin 인자(내부 호출용)
    2) 쿼리: type=admin 또는 include_hidden=true 또는 admin=true
    """
    show_all = False
    if is_admin is not None:
        show_all = bool(is_admin)
    elif request is not None:
        qp = request.query_params
        show_all = (
            qp.get("type") == "admin" or
            _as_bool(qp.get("include_hidden")) or
            _as_bool(qp.get("admin"))
        )

    return crud_get_notice(include_hidden=show_all)

# def get_notice():
#     notice = crud_get_notice()
#     return notice

def create_notice(notice_post: str, notice_title: str, notice_content: str, notice_file: str):
    crud_create_notice(notice_post, notice_title, notice_content, notice_file)


SERVICE_DIR = Path(__file__).resolve().parent
NOTICE_DIR  = (SERVICE_DIR.parent / "static/images/notice").resolve()
PUBLIC_PREFIX = "/static/images/notice"
NOTICE_DIR.mkdir(parents=True, exist_ok=True)
MAX_BYTES = 10 * 1024 * 1024  # 10MB

async def save_notice_image(file: UploadFile | None) -> str | None:
    if not file or not file.filename:
        return None
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(400, "이미지 파일만 업로드할 수 있습니다.")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(400, "최대 10MB까지 업로드 가능합니다.")

    # 확장자 보정
    ext = Path(file.filename).suffix.lower()
    if not ext:
        kind = imghdr.what(None, h=data)  # 'jpeg','png' 등
        ext = f".{('jpg' if kind == 'jpeg' else kind or 'jpg')}"

    name = f"{uuid4().hex}{ext}"
    (NOTICE_DIR / name).write_bytes(data)
    return f"{PUBLIC_PREFIX}/{name}"

def delete_notice_image(public_path: str | None) -> None:
    if not public_path:
        return
    name = Path(public_path).name  # 파일명만 추출
    target = (NOTICE_DIR / name).resolve()
    if NOTICE_DIR in target.parents and target.exists():
        try:
            target.unlink()
        except Exception:
            pass  # 실패는 치명적 아님(로그만 남겨도 OK)

def _extract_notice_file_path(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get("NOTICE_FILE") or row.get("notice_file")
    return getattr(row, "notice_file", None) or getattr(row, "NOTICE_FILE", None)

def update_notice(notice_no: int, notice_post: str, notice_title: str, notice_content: str, new_path: str | None, remove_file: bool):
    try:
        crud_update_notice(notice_no, notice_post, notice_title, notice_content)
        
        # 파일 처리: 교체 > 삭제 > 유지
        old = crud_get_notice(notice_no)
        old_path = old["NOTICE_FILE"] if isinstance(old, dict) else getattr(old, "notice_file", None)

        if new_path:  # 교체
            crud_update_notice_set_file(notice_no, new_path)
            if old_path:
                delete_notice_image(old_path)

        elif remove_file:  # 삭제
            crud_update_notice_clear_file(notice_no)
            if old_path:
                delete_notice_image(old_path)

    except Exception as e:
        raise

def delete_notice(notice_no: int):
    old = crud_get_notice(notice_no)
    old_path = old["NOTICE_FILE"] if isinstance(old, dict) else getattr(old, "notice_file", None)
    crud_delete_notice(notice_no)
    if old_path:
        delete_notice_image(old_path)

def get_notice_read(user_id):
    data = crud_get_notice_read(user_id)
    return data

def insert_notice_read(user_id, notice_no):
    try:
        crud_insert_notice_read(user_id, notice_no)
        return True
    except Exception as e:
        print(f"서비스 오류: {e}")
        return False

class NoticeNotFoundError(Exception):
    pass

def notice_views(notice_no: int) -> None:
    """
    조회수 +1 비즈니스 규칙 적용 지점
    - 존재하지 않는 notice면 예외
    """
    affected = crud_notice_views(notice_no)
    if affected == 0:
        raise NoticeNotFoundError()