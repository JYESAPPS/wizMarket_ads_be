from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
from typing import List
import pymysql
import logging
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime

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
    try:
        conn = get_re_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
        INSERT INTO business_verification
            (user_id, business_name, business_number, original_filename, saved_filename, saved_path, content_type, size_bytes, status, created_at)
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
        # print("SQL TOTAL:", cur.mogrify(sql_total, params))
        cur.execute(sql_total, params)
        total = cur.fetchone()["cnt"]

        # items
        sql_items = f"""
            SELECT
              bv.id, bv.user_id, bv.business_name, bv.business_number, bv.original_filename, bv.saved_filename, bv.saved_path,
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

def cms_approve_verification(id: int) -> int:
    """
    returns: affected row count (1이면 승인 성공, 0이면 이미 처리되었거나 없음)
    """
    conn = get_re_db_connection()
    cur = conn.cursor()  # DictCursor 불필요: 반환 안 씀
    try:
        now = datetime.utcnow()
        sql = """
            UPDATE business_verification
               SET status='approved',
                   reviewer_id=1,
                   reviewed_at=%s
             WHERE id=%s
               AND status='pending'
        """
        cur.execute(sql, (now, id))
        affected = cur.rowcount
        commit(conn)
        return affected
    except Exception:
        rollback(conn)
        raise
    finally:
        close_cursor(cur)
        close_connection(conn)


def cms_reject_verification(id : int, notes: Optional[str]) -> int:
    """
    returns: affected row count (1=성공, 0=이미 처리/없음)
    """
    conn = get_re_db_connection()
    cur = conn.cursor()  # DictCursor 불필요(반환값 안 씀)
    try:
        now = datetime.utcnow()
        reason = (notes or "").strip() or None
        if reason and len(reason) > 255:
            reason = reason[:255]

        sql = """
            UPDATE business_verification
               SET status='rejected',
                   notes=%s,
                   reviewed_at=%s
             WHERE id=%s
               AND status='pending'
        """
        cur.execute(sql, (reason, now, id))
        affected = cur.rowcount
        commit(conn)
        return affected
    except Exception:
        rollback(conn)
        raise
    finally:
        close_cursor(cur)
        close_connection(conn)



# cms용: 전체 사용자 목록 반환
def cms_get_user_list():
    conn = get_re_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.user_id, u.email, u.login_provider, u.created_at, ui.nickname, ud.platform, ud.last_seen,
                        t.ticket_name, tp.ticket_id, tp.payment_date
                FROM user u
                LEFT JOIN user_info AS ui ON ui.user_id = u.user_id
                LEFT JOIN (
                    SELECT d.user_id, d.platform, d.last_seen
                    FROM user_device AS d
                    JOIN (
                        SELECT user_id, MAX(last_seen) AS last_seen
                        FROM user_device
                        GROUP BY user_id
                    ) AS mx
                      ON mx.user_id = d.user_id AND mx.last_seen = d.last_seen
                ) AS ud
                    ON ud.user_id = u.user_id
                LEFT JOIN (
                    SELECT tp.user_id, tp.ticket_id, tp.payment_date
                    FROM ticket_payment tp
                    JOIN (
                        SELECT user_id, MAX(payment_date) AS max_payment_date
                        FROM ticket_payment
                        GROUP BY user_id
                    ) mx
                        ON mx.user_id = tp.user_id
                    AND mx.max_payment_date = tp.payment_date
                ) AS tp ON tp.user_id = u.user_id
                LEFT JOIN ticket t ON t.ticket_id = tp.ticket_id
                ORDER BY u.created_at DESC
            """)
            return cur.fetchall()
    finally:
        close_connection(conn)


def cms_get_user_detail(user_id):
    conn = get_re_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.user_id, u.email, u.login_provider, u.created_at, ui.nickname, ui.register_tag, ud.platform, ud.last_seen,
                        ls.store_name, ls.large_category_name, ls.medium_category_name, ls.small_category_name, ls.industry_name, ls.road_name_address
                FROM wiz_report.user AS u
                LEFT JOIN wiz_report.user_info AS ui ON ui.user_id = u.user_id
                LEFT JOIN (
                    SELECT d.user_id, d.platform, d.last_seen
                    FROM wiz_report.user_device AS d
                    WHERE d.user_id = %s
                    ORDER BY d.last_seen DESC
                    LIMIT 1
                ) AS ud
                    ON ud.user_id = u.user_id
                LEFT JOIN test.local_store AS ls
                    ON ls.store_business_number = u.store_business_number
                WHERE u.user_id = %s
                LIMIT 1
            """, (user_id, user_id))
            return cur.fetchone()
    finally:
        close_connection(conn)

def cms_get_user_payments(user_id):
    conn = get_re_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tp.payment_id, tp.user_id, tp.ticket_id,
                    t.ticket_name, t.ticket_price, t.billing_cycle,
                    tp.payment_date, tp.expire_date,
                    CASE 
                        WHEN t.billing_cycle IS NULL OR t.billing_cycle = 0 
                            THEN NULL
                        ELSE DATE_ADD(tp.payment_date, INTERVAL t.billing_cycle MONTH)
                    END AS next_renewal,
                    CASE 
                        WHEN tp.expire_date IS NOT NULL AND tp.expire_date >= CURDATE() 
                            THEN 1 ELSE 0 
                    END AS is_valid
                FROM wiz_report.ticket_payment tp
                LEFT JOIN wiz_report.ticket t 
                    ON t.ticket_id = tp.ticket_id
                WHERE tp.user_id = %s
                ORDER BY tp.payment_date DESC
        """, (user_id,))
        return cur.fetchall()
    finally:
        close_connection(conn)                


def get_business_verification(user_id):
    conn = get_re_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("""
                SELECT user_id, business_name, business_number
                FROM wiz_report.business_verification
                WHERE user_id = %s
                LIMIT 1
            """, (user_id,))
            return cur.fetchone()  # 없으면 None
    finally:
        close_connection(conn)

def cms_marketing_agree(user_id: int, agree: bool):
    conn = get_re_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE wiz_report.user_info
                SET marketing_agree = %s,
                    marketing_agree_at = CASE WHEN %s=1 THEN NOW() ELSE NULL END
                WHERE user_id = %s
            """, (1 if agree else 0, 1 if agree else 0, user_id))
        conn.commit()
        return cur.rowcount
    finally:
        close_connection(conn)

