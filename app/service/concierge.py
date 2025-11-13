import pymysql
from typing import Optional, List

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



# 커밋 처리 한번에
def submit_concierge(fields, image_paths):
    main_category = fields.get("mainCategory")
    sub_category = fields.get("SubCategory") or fields.get("subCategory")
    detail_category = fields.get("detailCategory")

    name = fields.get("name")
    phone = fields.get("phone")
    pin = fields.get("pin")

    store_name = fields.get("storeName")
    road_address = fields.get("roadAddress")
    menus = fields.get("menus")

    connection = get_re_db_connection()
    cursor = None
    step = "init"

    try:
        cursor = connection.cursor()

        # 1) 컨시어지 유저 생성
        step = "user"
        user_id = crud_submit_concierge_user(cursor, name, phone, pin)

        # 2) 컨시어지 가게 생성
        step = "store"
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

        # 3) 컨시어지 이미지 저장
        step = "image"
        crud_submit_concierge_image(cursor, user_id, image_paths)

        # ✅ 세 개 다 성공했을 때만 커밋
        commit(connection)

        return {
            "success": True,
            "message": "",
        }

    except pymysql.MySQLError as e:
        # ❌ 중간에 하나라도 실패하면 전부 롤백
        rollback(connection)

        # 단계별 에러 메시지 매핑
        step_message = {
            "user": "컨시어지 사용자 생성 중 오류가 발생했습니다.",
            "store": "컨시어지 매장 생성 중 오류가 발생했습니다.",
            "image": "컨시어지 이미지 저장 중 오류가 발생했습니다.",
        }
        msg = step_message.get(step, "컨시어지 신청 처리 중 오류가 발생했습니다.")

        print(f"[submit_concierge] step={step}, DB error: {e}")

        # 여기서 예외를 다시 던지지 않고, 메시지 리턴
        return {
            "success": False,
            "message": msg,
        }

    finally:
        close_cursor(cursor)


def select_concierge_list(keyword: Optional[str] = None) -> List[dict]:
    """
    컨시어지 신청 리스트 조회 서비스.
    - 나중에 페이징, 권한 체크, 추가 가공 등을 여기에 붙이면 됨.
    """
    items = crud_select_concierge_list(keyword=keyword)
    return items

