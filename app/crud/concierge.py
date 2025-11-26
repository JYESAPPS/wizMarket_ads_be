from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
from app.schemas.ads_faq import AdsFaqList, AdsTagList
from typing import List, Dict, Optional, Any
import pymysql
from pymysql.cursors import Cursor
import logging

logger = logging.getLogger(__name__)


# 도로명 정규화
import re
import unicodedata

# utils/address_normalize.py
import re
import unicodedata

# 축약/변형 → 정식 명칭 매핑
_ALIAS_TO_CANON = {
    # 특별/광역시
    "서울": "서울특별시", "서울시": "서울특별시",
    "부산": "부산광역시", "부산시": "부산광역시",
    "대구": "대구광역시", "대구시": "대구광역시",
    "인천": "인천광역시", "인천시": "인천광역시",
    "광주": "광주광역시", "광주시": "광주광역시",
    "대전": "대전광역시", "대전시": "대전광역시",
    "울산": "울산광역시", "울산시": "울산광역시",
    "세종": "세종특별자치시", "세종시": "세종특별자치시", "세종특별시": "세종특별자치시",

    # 도(광역자치단체)
    "경기": "경기도", "경기도": "경기도",
    "강원": "강원특별자치도", "강원도": "강원특별자치도", "강원특별자치도": "강원특별자치도",
    "충북": "충청북도", "충청북도": "충청북도",
    "충남": "충청남도", "충청남도": "충청남도",
    "전북": "전라북도", "전라북도": "전라북도",
    "전남": "전라남도", "전라남도": "전라남도",
    "경북": "경상북도", "경상북도": "경상북도",
    "경남": "경상남도", "경상남도": "경상남도",
    "제주": "제주특별자치도", "제주도": "제주특별자치도", "제주특별자치도": "제주특별자치도",
}

def normalize_addr_full(addr: str) -> str:
    """
    예)
      '부산 동구 고관로 85-1'  → '부산광역시 동구 고관로 85-1'
      '서울시 강남구 역삼로'    → '서울특별시 강남구 역삼로'
      '경기 성남시 분당구 ...'  → '경기도 성남시 분당구 ...'
      '강원도 춘천시 ...'       → '강원특별자치도 춘천시 ...'
    """
    if not addr:
        return ""

    # 1) 유니코드 정규화 + 공백/구두점 정리
    s = unicodedata.normalize("NFKC", addr).strip()
    # 괄호, 쉼표 등 최소 정리
    s = re.sub(r"[(),]", " ", s)
    # '대한민국 ' 같은 선행 국가명 제거
    s = re.sub(r"^대한민국\s+", "", s)
    # 다중 공백 축약
    s = re.sub(r"\s+", " ", s)

    # 2) 첫 토큰(시/도 단위 추정)만 정식 명칭으로 교체
    parts = s.split(" ", 1)  # ['부산', '동구 고관로 85-1']
    head = parts[0]
    tail = parts[1] if len(parts) > 1 else ""

    # head 후보에서 불필요 접미사 제거 후 매핑 확인 (예: '부산시' → '부산')
    head_base = head
    for suf in ("특별자치도", "특별시", "광역시", "자치시", "도", "시"):
        if head_base.endswith(suf):
            head_base = head_base[: -len(suf)]
            break

    # 우선 순위: 완전일치 → 베이스 치환 → 원형 보정
    canonical = (
        _ALIAS_TO_CANON.get(head) or
        _ALIAS_TO_CANON.get(head_base) or
        head  # 매핑 없으면 원본 유지
    )

    normalized = canonical if not tail else f"{canonical} {tail}"
    # 마무리 공백 정리
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized



def is_concierge(request):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    store_name = request.store_name
    road_name = request.road_address
    norm_road = normalize_addr_full(road_name)

    try:
        if not connection.open:
            raise HTTPException(status_code=500, detail="DB 연결이 열려있지 않습니다.")

        # 별칭을 써서 키를 확정
        sql = """
            SELECT COUNT(*) AS cnt
            FROM REPORT
            WHERE STORE_NAME = %s
              AND ROAD_NAME = %s
              AND IS_CONCIERGE = 1
        """
        cursor.execute(sql, (store_name, norm_road))
        row = cursor.fetchone() or {"cnt": 0}
        exists = (row.get("cnt", 0) > 0)

        # 존재하면 이미 등록 → False, 아니면 신규 가능 → True
        return not exists

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
    except Exception as e:
        logger.error(f"Unexpected Error in is_concierge: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류가 발생했습니다.")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass




def submit_concierge_user(cursor, name, phone, pin) -> int:
    """
    concierge_user 한 건 INSERT 하고, 새 user_id를 반환.
    - 커넥션/커밋/롤백은 바깥(service)에서 처리
    """
    insert_query = """
        INSERT INTO CONCIERGE_USER (user_name, phone, pin, status)
        VALUES (%s, %s, %s, "PENDING")
    """

    cursor.execute(insert_query, (name, phone, pin))
    user_id = cursor.lastrowid  # 신규 유저 ID

    return user_id




def submit_concierge_store(
    cursor,
    user_id,
    store_name,
    road_address,
    menus,
    main_category,
    sub_category,
    detail_category,
):
    norm_road = normalize_addr_full(road_address)

    # menus → menu_1, menu_2, menu_3
    menus_raw = menus or ""
    parts = [m.strip() for m in menus_raw.split(",") if m.strip()]
    menu_1, menu_2, menu_3 = (parts + [None, None, None])[:3]

    insert_query = """
        INSERT INTO CONCIERGE_STORE (
            user_id,
            store_name,
            road_name,
            menu_1,
            menu_2,
            menu_3,
            big_category_code,
            medium_category_code,
            small_category_code
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(
        insert_query,
        (
            user_id,
            store_name,
            norm_road,
            menu_1,
            menu_2,
            menu_3,
            main_category,
            sub_category,
            detail_category,
        ),
    )


def submit_concierge_image(cursor, user_id: int, image_paths: Dict[str, str]) -> int:
    """
    concierge_user_file 테이블에 파일 메타데이터를 INSERT한다.

    :param cursor: 이미 열린 DB 커서
    :param user_id: concierge_user.user_id (FK)
    :param image_paths: {"image_1": "path1", "image_2": "path2", ...}
    :return: 실제로 INSERT된 행(row) 개수
    """
    if not image_paths:
        return 0

    insert_query = """
        INSERT INTO concierge_user_file (
            user_id,
            file_order,
            storage_path,
            original_name,
            mime_type,
            file_size
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    rows = []
    for key, path in image_paths.items():
        if not path:
            continue

        # key: "image_1" → file_order = 1
        try:
            order_str = key.split("_")[1]
            file_order = int(order_str)
        except (IndexError, ValueError):
            # 형식이 안 맞으면 그냥 스킵
            continue

        rows.append(
            (
                user_id,        # user_id
                file_order,     # file_order (1, 2, 3...)
                path,           # storage_path
                None,           # original_name
                None,           # mime_type
                None,           # file_size
            )
        )

    if not rows:
        return 0

    cursor.executemany(insert_query, rows)




# 리스트 + 검색 조회
def select_concierge_list(
    keyword: Optional[str] = None,
    search_field: Optional[str] = None,      # "all" | "name" | "store_name" | None
    status: Optional[str] = None,            # "PENDING" | "APPROVED" | "REJECTED" | None
    apply_start: Optional[str] = None,       # ISO datetime string
    apply_end: Optional[str] = None,         # ISO datetime string
) -> List[dict]:
    """
    컨시어지 신청 리스트 조회용 CRUD.
    - CONCIERGE_USER + CONCIERGE_STORE + concierge_user_file 조인
    - keyword: search_field에 따라 이름/매장명 LIKE 검색
    - status: 신청 상태 필터 (예: PENDING/APPROVED/REJECTED)
    - apply_start/apply_end: 신청일(생성일) 범위 필터
    """
    connection = get_re_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT
                cu.user_id          AS id,
                cu.user_name        AS user_name,
                cu.phone            AS phone,
                cs.store_name       AS store_name,
                cs.road_name        AS road_name,
                cs.menu_1           AS menu_1,
                cs.menu_2           AS menu_2,
                cs.menu_3           AS menu_3,
                COUNT(cf.file_id)   AS image_count,
                cu.status           AS status,
                cs.created_at       AS created_at
            FROM CONCIERGE_USER cu
            JOIN CONCIERGE_STORE cs
                ON cs.user_id = cu.user_id
            LEFT JOIN concierge_user_file cf
                ON cf.user_id = cu.user_id
        """

        where_clauses = []
        params: list = []

        # 🔹 keyword 조건
        if keyword:
            kw = f"%{keyword.strip()}%"
            field = (search_field or "all").lower()  # 기본값: all

            if field == "name":
                # 이름만
                where_clauses.append("cu.user_name LIKE %s")
                params.append(kw)

            elif field == "store_name":
                # 매장명만
                where_clauses.append("cs.store_name LIKE %s")
                params.append(kw)

            else:
                # ✅ 전체: 이름 OR 매장명
                where_clauses.append(
                    "(cu.user_name LIKE %s OR cs.store_name LIKE %s)"
                )
                params.extend([kw, kw])

        # 🔹 상태 조건
        if status:
            where_clauses.append("cu.status = %s")
            params.append(status)

        # 🔹 신청일(생성일) 범위
        if apply_start and apply_end:
            where_clauses.append("cs.created_at BETWEEN %s AND %s")
            params.extend([apply_start, apply_end])
        elif apply_start:
            where_clauses.append("cs.created_at >= %s")
            params.append(apply_start)
        elif apply_end:
            where_clauses.append("cs.created_at <= %s")
            params.append(apply_end)

        if where_clauses:
            sql += "\nWHERE " + " AND ".join(where_clauses)

        sql += """
            GROUP BY
                cu.user_id,
                cu.user_name,
                cu.phone,
                cs.store_name,
                cs.road_name,
                cs.menu_1,
                cs.menu_2,
                cs.menu_3,
                cu.status,
                cs.created_at
            ORDER BY cs.created_at DESC
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return rows

    except pymysql.MySQLError as e:
        print(f"[crud_select_concierge_list] DB error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)


# 시스템용 리스트 조회
def get_concierge_system_list() -> List[dict]:

    connection = get_re_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT
                cu.user_id          AS id,
                cu.user_name        AS user_name,
                cu.phone            AS phone,
                cs.store_name       AS store_name,
                cs.road_name        AS road_name,
                cs.menu_1           AS menu_1,
                cs.menu_2           AS menu_2,
                cs.menu_3           AS menu_3,
                COUNT(cf.file_id)   AS image_count,
                cu.status           AS status,
                cs.created_at       AS created_at
            FROM CONCIERGE_USER cu
            JOIN CONCIERGE_STORE cs
                ON cs.user_id = cu.user_id
            LEFT JOIN concierge_user_file cf
                ON cf.user_id = cu.user_id
            WHERE cu.status = 'APPROVED'
            GROUP BY
                cu.user_id,
                cu.user_name,
                cu.phone,
                cs.store_name,
                cs.road_name,
                cs.menu_1,
                cs.menu_2,
                cs.menu_3,
                cu.status,
                cs.created_at
            ORDER BY cs.created_at DESC
        """

        cursor.execute(sql)
        rows = cursor.fetchall()
        return rows

    except pymysql.MySQLError as e:
        print(f"[crud_select_concierge_list] DB error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)


# 상세 조회
def select_concierge_detail(user_id: int) -> Optional[Dict[str, Any]]:
    """
    한 명의 컨시어지 신청 상세 조회
    - CONCIERGE_USER + CONCIERGE_STORE + concierge_user_file
    """
    connection = get_re_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 1) 유저 + 스토어 정보 (1건)
        sql_main = """
            SELECT
                cu.user_id        AS user_id,
                cu.user_name      AS user_name,
                cu.phone          AS phone,
                cu.status         AS status,
                cu.memo           AS memo,
                cu.store_business_number AS store_business_number,
                cs.store_name     AS store_name,
                cs.road_name      AS road_name,
                cs.big_category_code AS main_category_code,
                cs.medium_category_code AS sub_category_code,
                cs.small_category_code AS detail_category_code,
                cs.menu_1         AS menu_1,
                cs.menu_2         AS menu_2,
                cs.menu_3         AS menu_3,
                cs.created_at     AS created_at
            FROM CONCIERGE_USER cu
            JOIN CONCIERGE_STORE cs
              ON cs.user_id = cu.user_id
            WHERE cu.user_id = %s
            LIMIT 1
        """
        cursor.execute(sql_main, (user_id,))
        main = cursor.fetchone()

        if not main:
            return None

        # 2) 이미지 리스트
        sql_files = """
            SELECT
                file_id,
                user_id,
                file_order,
                storage_path,
                original_name,
                mime_type,
                file_size,
                created_at
            FROM concierge_user_file
            WHERE user_id = %s
            ORDER BY file_order ASC, file_id ASC
        """
        cursor.execute(sql_files, (user_id,))
        files: List[Dict[str, Any]] = cursor.fetchall() or []

        main["images"] = files
        return main

    except pymysql.MySQLError as e:
        print(f"[select_concierge_detail] DB error: {e}")
        raise
    finally:
        close_cursor(cursor)
        close_connection(connection)






def get_report_store(store_name, road_name):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    norm_road = normalize_addr_full(road_name)

    try:
        if not connection.open:
            raise HTTPException(status_code=500, detail="DB 연결이 열려있지 않습니다.")

        # 🔹 STORE_BUSINESS_NUMBER 조회
        sql = """
            SELECT STORE_BUSINESS_NUMBER
            FROM REPORT
            WHERE STORE_NAME = %s
              AND ROAD_NAME = %s
            LIMIT 1
        """
        cursor.execute(sql, (store_name, norm_road))
        row = cursor.fetchone()

        # 🔹 있으면 사업자번호 반환, 없으면 None
        if row and row.get("STORE_BUSINESS_NUMBER"):
            return row["STORE_BUSINESS_NUMBER"]

        return None

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
    except Exception as e:
        logger.error(f"Unexpected Error in is_concierge: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류가 발생했습니다.")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass



# 컨시어지 스케줄 인서트
def reserve_schedule(user_id, week_day, send_time):
    connection = get_re_db_connection()
    cursor = None

    try:
        # DictCursor 안 써도 되지만, 습관대로 써도 무방
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        sql = """
            INSERT INTO concierge_schedule (
                user_id,
                week_day,
                send_time
            )
            VALUES (%s, %s, %s)
        """

        cursor.execute(sql, (user_id, week_day, send_time))
        connection.commit()

        # 필요하면 생성된 PK 반환
        return cursor.lastrowid

    except pymysql.MySQLError as e:
        print(f"[reserve_schedule] DB error: {e}")
        connection.rollback()
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)


def update_report_is_concierge(cursor, store_business_number):
    connection = get_re_db_connection()

    try:
        if not connection.open:
            raise HTTPException(status_code=500, detail="DB 연결이 열려있지 않습니다.")

        # 🔹 STORE_BUSINESS_NUMBER 조회
        sql = """
            UPDATE REPORT 
            SET IS_CONCIERGE = 1
            WHERE store_business_number = %s
        """
        cursor.execute(sql, (store_business_number,))
        connection.commit()
    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
    except Exception as e:
        logger.error(f"Unexpected Error in is_concierge: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류가 발생했습니다.")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass








# 컨시어지 매장 삭제 처리
def delete_concierge_user(cursor, user_ids: List[int]) -> int:
    """
    CONCIERGE_USER 의 PK 리스트를 받아 삭제.
    - ON DELETE CASCADE 로 인해, 연결된 CONCIERGE_STORE / CONCIERGE_FILE 은 자동 삭제.
    - 반환: 삭제된 USER 개수
    """
    if not user_ids:
        return 0

    placeholders = ", ".join(["%s"] * len(user_ids))

    query = f"""
        DELETE FROM CONCIERGE_USER
        WHERE user_id IN ({placeholders})
    """
    cursor.execute(query, user_ids)
    return cursor.rowcount


def update_concierge_basic(
    cursor: Cursor,
    concierge_id: int,
    *,
    status: str,
    user_name: str,
    phone: str,
    memo: str,
    store_business_number: str,
    main_category_code: Optional[str],
    sub_category_code: Optional[str],
    detail_category_code: Optional[str],
    menu_1: Optional[str],
    menu_2: Optional[str],
    menu_3: Optional[str],
) -> None:
    """
    - concierge_user : 이름/휴대폰/메모/상태 업데이트
    - concierge_store: 업종/메뉴 업데이트
    """

    # 1) 유저 테이블
    sql_user = """
        UPDATE concierge_user
           SET user_name = %s,
               phone     = %s,
               memo      = %s,
               status    = %s,
               updated_at = NOW(),
               store_business_number = %s
         WHERE user_id = %s
    """
    cursor.execute(
        sql_user,
        (user_name, phone, memo, status, store_business_number, concierge_id),
    )

    if cursor.rowcount == 0:
        # 엔드포인트/서비스에서 처리
        raise ValueError("CONCIERGE_USER_NOT_FOUND")

    # 2) 매장 테이블 (업종 + 메뉴)
    sql_store = """
        UPDATE concierge_store
           SET big_category_code   = %s,
               medium_category_code    = %s,
               small_category_code = %s,
               menu_1               = %s,
               menu_2               = %s,
               menu_3               = %s,
               updated_at           = NOW()
         WHERE user_id = %s
    """
    cursor.execute(
        sql_store,
        (
            main_category_code,
            sub_category_code,
            detail_category_code,
            menu_1,
            menu_2,
            menu_3,
            concierge_id,
        ),
    )


def mark_concierge_images_deleted(
    cursor: Cursor,
    user_id: int,
    removed_file_ids: List[int],
) -> None:
    """
    기존 신청 이미지 삭제
    - concierge_user_file 테이블에서 실제 삭제
    """

    if not removed_file_ids:
        return

    placeholders = ",".join(["%s"] * len(removed_file_ids))

    sql = f"""
        DELETE FROM concierge_user_file
         WHERE user_id = %s
           AND file_id IN ({placeholders})
    """
    cursor.execute(sql, [user_id, *removed_file_ids])

def insert_concierge_image(
    cursor: Cursor,
    user_id: int,
    storage_path: str,
    original_name: str,
    mime_type: Optional[str],
    file_size: int,
) -> None:
    """
    새 이미지 1개 insert
    - file_order 는 해당 user_id 기준으로 MAX + 1 자동 부여
    """

    # 1) 현재 user_id 기준 최대 file_order 조회
    cursor.execute(
        """
        SELECT COALESCE(MAX(file_order), 0)
          FROM concierge_user_file
         WHERE user_id = %s
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    max_order = row[0] if row is not None else 0
    next_order = max_order + 1

    # 2) INSERT
    sql = """
        INSERT INTO concierge_user_file (
            user_id,
            file_order,
            storage_path,
            original_name,
            mime_type,
            file_size,
            created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
    """
    cursor.execute(
        sql,
        (user_id, next_order, storage_path, original_name, mime_type, file_size),
    )




# 해당하는 요일, 시간 user_id 리스트 가져오기
def get_user_id_list(same_day: bool, today_code: str, next_day_code: str, start_time_str: str, end_time_str: str) -> List[int]:
    connection = get_re_db_connection()
    cursor = None

    # print(same_day, today_code, next_day_code, start_time_str, end_time_str)

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 날짜가 안 바뀌는 대부분 경우: 오늘 요일 + 시간 BETWEEN
        if same_day:
            sql = """
                SELECT DISTINCT user_id
                  FROM concierge_schedule
                 WHERE is_active = 1
                   AND week_day = %s
                   AND send_time BETWEEN %s AND %s
            """
            params = (today_code, start_time_str, end_time_str)

        # 예: 23:30 ~ 00:30 같은 경우 → 오늘/내일로 나눠서 OR
        else:
            sql = """
                SELECT DISTINCT user_id
                  FROM concierge_schedule
                 WHERE is_active = 1
                   AND (
                        (week_day = %s AND send_time >= %s)
                     OR (week_day = %s AND send_time <  %s)
                   )
            """
            params = (today_code, start_time_str, next_day_code, end_time_str)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # [8, 12, 15] 형태로 반환
        return [row["user_id"] for row in rows]

    except pymysql.MySQLError as e:
        print(f"[select_scheduled_user_ids_within_next_hour] DB error: {e}")
        raise
    finally:
        close_cursor(cursor)
        close_connection(connection)



# 추가 정보 가져오기
def select_concierge_users_by_ids(user_id_list):
    """
    concierge_user + concierge_store 조인해서
    user_id 목록에 해당하는 store_business_number, menu_1, road_name 조회
    """
    if not user_id_list:
        return []

    connection = get_re_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        placeholders = ", ".join(["%s"] * len(user_id_list))
        sql = f"""
            SELECT
                cu.user_id,
                cu.store_business_number,
                cs.menu_1,
                cs.road_name
            FROM concierge_user cu
            JOIN concierge_store cs
              ON cs.user_id = cu.user_id
            WHERE cu.user_id IN ({placeholders})
        """

        cursor.execute(sql, user_id_list)
        rows = cursor.fetchall()
        return rows
    except pymysql.MySQLError as e:
        print(f"[select_concierge_users_by_ids] DB error: {e}")
        raise
    finally:
        close_cursor(cursor)
        close_connection(connection)


# 히스토리 리스트 조회
def select_history_list(
    keyword: Optional[str] = None,
    search_field: Optional[str] = None,      # "all" | "name" | "store_name" | None
    status: Optional[str] = None,            # "PENDING" | "APPROVED" | "REJECTED" | None
    apply_start: Optional[str] = None,       # ISO datetime string (KST)
    apply_end: Optional[str] = None,         # ISO datetime string (KST)
) -> List[dict]:
    """
    컨시어지 인스타 업로드 히스토리 리스트 조회용 CRUD.

    - 한 매장(user_id)당 1행만 노출
      → concierge_user_history 에서 insta_status='SUCCESS' 인 것 중
        가장 최근(created_at MAX) 1건만 사용
    - keyword: search_field 에 따라 이름/매장명 LIKE 검색
    - status: 신청 상태 필터 (PENDING/APPROVED/REJECTED 등, cu.status 기준)
    - apply_start/apply_end: 히스토리 생성일(ch.created_at) 범위 필터
    """
    connection = get_re_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 👇 핵심: user_id 별로 가장 최근 SUCCESS 히스토리 1건만 뽑는 서브쿼리
        sql = """
            SELECT
                cu.user_id          AS id,
                cu.user_name        AS user_name,
                cu.phone            AS phone,
                cs.store_name       AS store_name,
                cs.road_name        AS road_name,
                cs.menu_1           AS menu_1,
                cs.menu_2           AS menu_2,
                cs.menu_3           AS menu_3,
                COUNT(cf.file_id)   AS image_count,
                cu.status           AS status,
                ch.created_at       AS created_at,
                ch.image_path       AS image_path,
                ch.register_tag     AS register_tag
            FROM CONCIERGE_USER cu
            JOIN CONCIERGE_STORE cs
                ON cs.user_id = cu.user_id
            -- 🔥 user_id별 최신 SUCCESS 히스토리 1건만 추출
            JOIN (
                SELECT h.user_id,
                       h.created_at,
                       h.image_path,
                       h.register_tag
                FROM concierge_user_history h
                JOIN (
                    SELECT user_id, MAX(created_at) AS latest_created_at
                    FROM concierge_user_history
                    WHERE insta_status = 'SUCCESS'
                    GROUP BY user_id
                ) latest
                  ON latest.user_id = h.user_id
                 AND latest.latest_created_at = h.created_at
                WHERE h.insta_status = 'SUCCESS'
            ) ch
                ON ch.user_id = cu.user_id
            LEFT JOIN concierge_user_file cf
                ON cf.user_id = cu.user_id
        """

        where_clauses = []
        params: list = []

        # 🔹 keyword 조건
        if keyword:
            kw = f"%{keyword.strip()}%"
            field = (search_field or "all").lower()  # 기본값: all

            if field == "name":
                where_clauses.append("cu.user_name LIKE %s")
                params.append(kw)
            elif field == "store_name":
                where_clauses.append("cs.store_name LIKE %s")
                params.append(kw)
            else:
                # ✅ 전체: 이름 OR 매장명
                where_clauses.append(
                    "(cu.user_name LIKE %s OR cs.store_name LIKE %s)"
                )
                params.extend([kw, kw])

        # 🔹 상태 조건 (컨시어지 신청 상태)
        if status:
            where_clauses.append("cu.status = %s")
            params.append(status)

        # 🔹 히스토리 생성일 범위 (ch.created_at 기준)
        if apply_start and apply_end:
            where_clauses.append("ch.created_at BETWEEN %s AND %s")
            params.extend([apply_start, apply_end])
        elif apply_start:
            where_clauses.append("ch.created_at >= %s")
            params.append(apply_start)
        elif apply_end:
            where_clauses.append("ch.created_at <= %s")
            params.append(apply_end)

        if where_clauses:
            sql += "\nWHERE " + " AND ".join(where_clauses)

        sql += """
            GROUP BY
                cu.user_id,
                cu.user_name,
                cu.phone,
                cs.store_name,
                cs.road_name,
                cs.menu_1,
                cs.menu_2,
                cs.menu_3,
                cu.status,
                ch.created_at,
                ch.image_path,
                ch.register_tag
            ORDER BY ch.created_at DESC
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return rows

    except pymysql.MySQLError as e:
        print(f"[crud_select_history_list] DB error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)


