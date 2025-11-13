import pymysql
from typing import Dict, List, Tuple, Optional
import os
from fastapi import UploadFile
from uuid import uuid4

from app.db.connect import (
    get_re_db_connection,
    commit,
    rollback,
    close_cursor,
    close_connection,
)

from app.crud.concierge import (
    is_concierge as crud_is_concierge,
    submit_concierge_user as crud_submit_concierge_user,
    submit_concierge_store as crud_submit_concierge_store,
    submit_concierge_image as crud_submit_concierge_image,
    select_concierge_list as crud_select_concierge_list
)


def is_concierge(request):
    is_concierge = crud_is_concierge(request)
    return is_concierge



# 이미지 저장 처리
UPLOAD_ROOT = "/app/uploads"  # 도커 컨테이너 내부 실제 저장 위치 (볼륨 마운트 추천)

async def save_concierge_images(user_id: int, images: List[UploadFile]) -> Dict[str, str]:
    """
    user_id 기준으로 concierge/user_{user_id}/... 에 저장하고,
    DB에 넣을 storage_path 맵을 반환.
    예: { "image_1": "concierge/user_1/abcd1234_1.png", ... }
    """
    image_paths: Dict[str, str] = {}

    if not images:
        return image_paths

    # 1) 실제 저장 디렉토리 (컨테이너 내부)
    user_dir = os.path.join(UPLOAD_ROOT, "concierge", f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)  # 폴더 없으면 자동 생성

    for idx, img in enumerate(images[:6], start=1):  # 최대 6장
        if not img.filename:
            continue

        _, ext = os.path.splitext(img.filename)
        ext = (ext or ".jpg").lower()

        filename = f"{uuid4().hex}_{idx}{ext}"

        # 실제 파일이 저장될 전체 경로 (컨테이너 파일 시스템 기준)
        save_path = os.path.join(user_dir, filename)

        # 파일 쓰기
        content = await img.read()
        with open(save_path, "wb") as f:
            f.write(content)

        # 🔹 DB에는 이렇게 저장 (논리 경로)
        #    concierge/user_1/abcd1234_1.png
        storage_path = os.path.join("concierge", f"user_{user_id}", filename).replace("\\", "/")

        image_paths[f"image_{idx}"] = storage_path

    return image_paths


# 커밋 처리 한번에
async def submit_concierge(fields: Dict[str, str], images: List[UploadFile]) -> Tuple[bool, str]:
    """
    - concierge_user / concierge_store / concierge_user_file INSERT
    - 이미지 파일은 user_id 기준 폴더에 저장: uploads/concierge/user_{user_id}/...
    """
    main_category = fields.get("mainCategory")
    sub_category = fields.get("subCategory")
    detail_category = fields.get("detailCategory")

    name = fields.get("name")
    phone = fields.get("phone")
    pin = fields.get("pin")

    store_name = fields.get("storeName")
    road_address = fields.get("roadAddress")
    menus = fields.get("menus")

    connection = get_re_db_connection()
    cursor = None

    try:
        cursor = connection.cursor()

        # 1) 컨시어지 유저 생성
        user_id = crud_submit_concierge_user(cursor, name, phone, pin)

        # 2) 컨시어지 가게 생성
        crud_submit_concierge_store(
            cursor,
            user_id,
            store_name,
            road_address,
            menus,
            main_category,
            sub_category,
            detail_category,
        )

        # 3) 이미지 저장 → image_paths 구성 (user_id 기준 폴더 내부)
        image_paths = await save_concierge_images(user_id, images)

        # 4) 컨시어지 이미지 메타데이터 INSERT
        if image_paths:
            crud_submit_concierge_image(cursor, user_id, image_paths)

        # 5) 모두 성공 시 커밋
        commit(connection)
        return True, "신청이 정상적으로 접수되었습니다."

    except pymysql.MySQLError as e:
        rollback(connection)
        print(f"[submit_concierge] DB error: {e}")
        return False, "신청 처리 중 DB 오류가 발생했습니다."

    except Exception as e:
        rollback(connection)
        print(f"[submit_concierge] error: {e}")
        return False, "신청 처리 중 알 수 없는 오류가 발생했습니다."

    finally:
        close_cursor(cursor)
        close_connection(connection)



def select_concierge_list(
    keyword: Optional[str],
    search_field: Optional[str],
    status: Optional[str],
    apply_start: Optional[str],
    apply_end: Optional[str],
):
    return crud_select_concierge_list(
        keyword=keyword,
        search_field=search_field,
        status=status,
        apply_start=apply_start,
        apply_end=apply_end,
    )


