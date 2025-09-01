from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
from typing import List
import pymysql
import logging
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


# 사업자 등록증 제출
def insert_business_verification(
    user_id,
    original_filename,
    saved_filename,
    saved_path,    
    content_type,
    size_bytes,
    bs_name,
    bs_number
) -> int:
    conn = None
    cursor = None
    bs_number = str(bs_number)
    try:
        conn = get_re_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
        INSERT INTO business_verification
            (user_id, bs_name, bs_number, original_filename, saved_filename, saved_path, content_type, size_bytes, status, created_at)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, 'pending', NOW())
        """
        cursor.execute(sql, (
            user_id,
            bs_name,
            bs_number,
            original_filename,
            saved_filename,
            saved_path,          # 가능하면 상대경로를 권장
            content_type,
            size_bytes,
        ))

        new_id = cursor.lastrowid
        commit(conn)
        return new_id

    except Exception as e:
        if conn:
            rollback(conn)
        logger.error(f"insert_business_verification error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if cursor:
            close_cursor(cursor)
        if conn:
            close_connection(conn)



# 사업자 등록증 목록 조회
def cms_list_verifications(
    user_id: Optional[int],
    status: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    page: int,
    page_size: int,
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    DB에서 business_verification 목록을 조회.
    반환: (total_count, items)
    """
    # 기본 가드(옵션)
    page = max(1, int(page))
    page_size = max(1, min(200, int(page_size)))
    offset = (page - 1) * page_size

    conn = get_re_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    try:
        where = ["1=1"]
        params: List[Any] = []

        if user_id is not None:
            where.append("bv.user_id = %s")
            params.append(user_id)

        if status is not None:
            where.append("bv.status = %s")
            params.append(status)

        if date_from:
            where.append("bv.created_at >= %s")
            params.append(date_from + " 00:00:00")

        if date_to:
            where.append("bv.created_at <= %s")
            params.append(date_to + " 23:59:59")

        where_sql = " AND ".join(where)

        # total
        sql_total = f"SELECT COUNT(*) AS cnt FROM business_verification bv WHERE {where_sql}"
        print("SQL TOTAL:", cur.mogrify(sql_total, params))
        cur.execute(sql_total, params)
        total = cur.fetchone()["cnt"]

        # items
        sql_items = f"""
            SELECT
              bv.id, bv.user_id, bv.original_filename, bv.saved_filename, bv.saved_path,
              bv.content_type, bv.size_bytes, bv.status, bv.notes, bv.reviewer_id,
              DATE_FORMAT(bv.created_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS created_at,
              IFNULL(DATE_FORMAT(bv.reviewed_at, '%%Y-%%m-%%d %%H:%%i:%%s'), NULL) AS reviewed_at
            FROM business_verification bv
            WHERE {where_sql}
            ORDER BY bv.created_at DESC
            LIMIT %s OFFSET %s
        """
        # print("SQL ITEMS:", cur.mogrify(sql_items, params + [page_size, offset]))
        cur.execute(sql_items, params + [page_size, offset])
        items = cur.fetchall()

        return total, items

    finally:
        close_cursor(cur)
        close_connection(conn)



