from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
from app.schemas.ads_faq import AdsFaqList, AdsTagList
from typing import List, Dict, Optional
import pymysql
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
        INSERT INTO CONCIERGE_USER (user_name, phone, pin, is_payment)
        VALUES (%s, %s, %s, 0)
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
            temp_big_category,
            temp_medium_category,
            temp_small_category
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



# CMS 어드민에서 컨시어지 신청 목록 조회
def select_concierge_list(keyword: Optional[str] = None) -> List[dict]:
    """
    컨시어지 신청 리스트 조회용 CRUD.
    - CONCIERGE_USER + CONCIERGE_STORE + concierge_user_file 조인
    - keyword가 있으면 이름/매장명/도로명 LIKE 검색
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
                cs.created_at       AS created_at
            FROM CONCIERGE_USER cu
            JOIN CONCIERGE_STORE cs
                ON cs.user_id = cu.user_id
            LEFT JOIN concierge_user_file cf
                ON cf.user_id = cu.user_id
        """

        params: list = []

        # keyword 조건 (이름 / 매장명 / 도로명)
        if keyword:
            sql += """
            WHERE
                cu.user_name LIKE %s
                OR cs.store_name LIKE %s
                OR cs.road_name LIKE %s
            """
            kw = f"%{keyword.strip()}%"
            params.extend([kw, kw, kw])

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
                cs.created_at
            ORDER BY cs.created_at DESC
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()  # List[Dict]

        return rows

    except pymysql.MySQLError as e:
        print(f"[crud_select_concierge_list] DB error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)