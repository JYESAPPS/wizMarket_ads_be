from app.crud.ads_notice import (
    get_notice as crud_get_notice,
    create_notice as crud_create_notice,
    get_notice_by_id as crud_get_notice_by_id,
    update_notice as crud_update_notice,
    delete_notice as crud_delete_notice,
    get_notice_read as crud_get_notice_read,
    insert_notice_read as crud_insert_notice_read,
    notice_views as crud_notice_views,
)
import json
from typing import List, Optional
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

def create_notice(notice_post: str, notice_type: str, notice_title: str, notice_content: str, notice_file: str, notice_file_org, notice_images, notice_push):
    return crud_create_notice(notice_post, notice_type, notice_title, notice_content, notice_file, notice_file_org, notice_images, notice_push)



####### 파일 저장 처리 ##########
UPLOAD_ROOT = "/app/uploads"  # 이미 쓰고 있는 값

NOTICE_SUBDIR = "notice"
NOTICE_DIR = Path(UPLOAD_ROOT) / NOTICE_SUBDIR
NOTICE_DIR.mkdir(parents=True, exist_ok=True)

MAX_BYTES = 10 * 1024 * 1024  # 10MB

async def save_notice_image(file: UploadFile | None) -> str | None:
    """
    공지 관련으로 업로드되는 이미지 1장 저장.
    DB에는 'notice/파일명.ext' 형태의 상대 경로를 저장.
    """
    print(f"service_save_notice_image called with file: {file}")
    if not file or not file.filename:
        print("no file provided")
        return None

    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="최대 10MB까지 업로드 가능합니다.")

    ext = Path(file.filename).suffix.lower()
    if not ext:
        kind = imghdr.what(None, h=data)
        if kind == "jpeg":
            ext = ".jpg"
        elif kind:
            ext = f".{kind}"
        else:
            ext = ".jpg"

    name = f"{uuid4().hex}{ext}"
    print(f"Generated file name: {name}")

    save_path = NOTICE_DIR / name
    save_path.write_bytes(data)
    print(f"Saved file to: {save_path}")

    storage_path = f"{NOTICE_SUBDIR}/{name}"   # notice/abcd1234.png
    print(f"Storage path for DB: {storage_path}")

    return storage_path

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


# 일반 파일(첨부파일) 저장 - 이미지가 아니어도 됨
async def save_notice_file(file: UploadFile | None) -> str | None:
    print(f"service_save_notice_file called with file: {file}")
    if not file or not file.filename:
        print("no file provided")
        return None

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="최대 10MB까지 업로드 가능합니다.")

    # 확장자는 원본 파일명 기준으로만 사용
    ext = Path(file.filename).suffix.lower() or ""
    name = f"{uuid4().hex}{ext}"
    save_path = NOTICE_DIR / name
    save_path.write_bytes(data)

    storage_path = f"{NOTICE_SUBDIR}/{name}"
    return storage_path

#################################################################


# app/service/notice_service.py

async def service_update_notice(
    notice_no: int,
    notice_post: str,
    notice_push: str,
    notice_type: str,
    notice_title: str,
    notice_content: str,
    notice_file_upload: UploadFile | None,
    remove_file: bool,
    existing_images_json: str,
    notice_images_uploads: List[UploadFile],
) -> None:
    # 1) 기존 공지 가져오기
    row = crud_get_notice_by_id(notice_no)
    if not row:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다.")

    old_file_path: str | None = row.get("NOTICE_FILE")
    old_file_org: str | None = row.get("NOTICE_FILE_ORG")

    # 2) 첨부파일 처리 (경로 + 원본파일명)
    new_file_path = old_file_path
    new_file_org = old_file_org

    if notice_file_upload is not None:
        # 새 파일 업로드 → 경로 + 원본명 둘 다 교체
        new_file_path = await save_notice_file(notice_file_upload)
        new_file_org = notice_file_upload.filename or None
    elif remove_file:
        # 삭제 체크 → 둘 다 삭제
        new_file_path = None
        new_file_org = None
    # 둘 다 아니면 기존 값 유지

    # 3) 첨부 이미지 처리 (부분 변경)
    try:
        images_list = json.loads(existing_images_json or "[]")
        if not isinstance(images_list, list):
            images_list = []
    except Exception:
        images_list = []

    for img in notice_images_uploads:
        if not img or not img.filename:
            continue
        path = await save_notice_image(img)
        if path:
            images_list.append(path)

    # 4) CRUD UPDATE 호출
    crud_update_notice(
        notice_no=notice_no,
        notice_post=notice_post,
        notice_push=notice_push,
        notice_type=notice_type,
        notice_title=notice_title,
        notice_content=notice_content,
        notice_file=new_file_path,
        notice_file_org=new_file_org,      # 🔹 추가
        notice_images=images_list,
    )





# 삭제
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