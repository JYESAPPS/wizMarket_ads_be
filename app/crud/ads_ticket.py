import logging
from datetime import datetime, date
from typing import Optional

import pymysql
import pymysql.cursors
from fastapi import HTTPException

from app.db.connect import (
    close_connection,
    close_cursor,
    commit,
    get_db_connection,
    get_re_db_connection,
    rollback,
)



logger = logging.getLogger(__name__)



#ticket_id로 상품 기간 조회
def get_cycle(ticket_id: int):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    try:
        if connection.open:
            select_query = """
                SELECT BILLING_CYCLE 
                FROM TICKET
                WHERE TICKET_ID=%s;
            """
            cursor.execute(select_query, (ticket_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return row["BILLING_CYCLE"]

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
    except Exception as e:
        logger.error(f"Unexpected Error in get_notice: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류가 발생했습니다.")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# 계약 내역에 삽입
def insert_payment(user_id, ticket_id, payment_method, payment_date, expire_date):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor()
        insert_query = """
            INSERT INTO ticket_payment (USER_ID, TICKET_ID, PAYMENT_METHOD, PAYMENT_DATE, EXPIRE_DATE)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (user_id, ticket_id, payment_method, payment_date, expire_date))
        commit(connection)  # 커스텀 commit 사용

    except pymysql.MySQLError as e:
        rollback(connection)  # 커스텀 rollback 사용
        print(f"Database error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)

#ticket_id로 토큰 개수 조회
def get_token_amount(ticket_id: int):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    try:
        if connection.open:
            select_query = """
                SELECT TOKEN_AMOUNT 
                FROM TICKET
                WHERE TICKET_ID=%s;
            """
            cursor.execute(select_query, (ticket_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return row["TOKEN_AMOUNT"]

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
    except Exception as e:
        logger.error(f"Unexpected Error in get_notice: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류가 발생했습니다.")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def has_ticket_grant(user_id: int, ticket_id: int) -> bool:
    """
    무료 토큰 중복 지급 여부 확인

    token_purchase에서 단건(one_time) 유형으로 동일 ticket_id 지급 이력이 있는지 확인한다.
    """
    connection = get_re_db_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        query = """
            SELECT 1
              FROM token_purchase
             WHERE user_id = %s
               AND ticket_id = %s
               AND transaction_type = 'one_time'
             LIMIT 1
        """
        cursor.execute(query, (user_id, ticket_id))
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"has_ticket_grant error: {e}")
        raise HTTPException(status_code=500, detail="토큰 지급 이력 조회 중 오류가 발생했습니다.")
    finally:
        if cursor:
            close_cursor(cursor)
        close_connection(connection)

def insert_token_purchase(
    user_id: int,
    ticket_id: int,
    purchased_tokens: int,
    remaining_tokens: Optional[int] = None,
    transaction_type: str = "one_time",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """
    TOKEN_PURCHASE에 지급/구매 내역을 기록한다.
    remaining_tokens 를 명시하지 않으면 purchased_tokens 값으로 채운다.
    """
    connection = get_re_db_connection()
    cursor = None

    try:
        cursor = connection.cursor()
        insert_query = """
            INSERT INTO TOKEN_PURCHASE (
                user_id,
                ticket_id,
                transaction_type,
                purchased_tokens,
                remaining_tokens,
                start_date,
                end_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        remaining = purchased_tokens if remaining_tokens is None else remaining_tokens
        cursor.execute(
            insert_query,
            (user_id, ticket_id, transaction_type, purchased_tokens, remaining, start_date, end_date),
        )
        commit(connection)
    except pymysql.MySQLError as e:
        rollback(connection)
        logger.error(f"insert_token_purchase DB error: {e}")
        raise
    finally:
        if cursor:
            close_cursor(cursor)
        close_connection(connection)

# 현재 구독 상품 조회
def get_subscription_info(user_id):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    try:
        if connection.open:
            select_query = """
                SELECT subscription_type 
                FROM user_info
                WHERE user_id=%s;
            """
            cursor.execute(select_query, (user_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return row["subscription_type"]

    except Exception as e:
        logger.error(f"Unexpected Error in get_notice: {e}")
        raise HTTPException(status_code=500, detail="구독 정도 조회 오류가 발생했습니다.")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# 구매 시 user_info에 티켓 정보 추가
def update_subscription_info(user_id, plan_type):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor()
        update_query = """
            UPDATE user_info
            SET subscription_type = %s
            WHERE user_id = %s
        """

        cursor.execute(update_query, (plan_type, user_id))
        commit(connection)  # 커스텀 commit 사용

    except pymysql.MySQLError as e:
        rollback(connection)  # 커스텀 rollback 사용
        print(f"Database error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)



#사용자의 결제 내역 조회
def get_history_100(user_id):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM ticket t 
                JOIN ticket_payment p
                ON t.TICKET_ID = p.TICKET_ID
                WHERE p.USER_ID = %s AND p.TICKET_ID = 12
                ORDER BY p.PAYMENT_DATE DESC
            """, (user_id))
            row = cursor.fetchone()
            # status = True

            # if row : 
                # status = False
            if row and row[0] > 0: 
                # print(f"[중복 결제 차단] 유저 {user_id}가 이미 구매함 → row={row}")
                return False

            # return status
            # print(f"[결제 가능] 유저 {user_id}는 아직 구매 안함 → row={row}")
            return True

    except Exception as e:
        logger.error(f"get_history_100 error: {e}")
        return False
    finally:
        connection.close()
    


#사용자의 결제 내역 조회
def get_history(user_id):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT t.TICKET_NAME, t.TICKET_PRICE, t.BILLING_CYCLE, t.TOKEN_AMOUNT, p.PAYMENT_DATE, p.EXPIRE_DATE
                FROM ticket t 
                JOIN ticket_payment p
                ON t.TICKET_ID = p.TICKET_ID
                WHERE p.USER_ID = %s
                ORDER BY p.PAYMENT_ID DESC
            """, (user_id))
            rows = cursor.fetchall()
            return rows

    except Exception as e:
        logger.error(f"get_history error: {e}")
        return []
    finally:
        connection.close()

#사용자의 결제 내역 조회
def get_valid_history(user_id):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT t.TICKET_NAME, t.TICKET_PRICE, t.BILLING_CYCLE, t.TOKEN_AMOUNT, p.PAYMENT_DATE, p.EXPIRE_DATE
                FROM ticket t 
                JOIN ticket_payment p
                ON t.TICKET_ID = p.TICKET_ID
                WHERE p.USER_ID = %s
                AND p.EXPIRE_DATE IS NOT NULL
                AND p.EXPIRE_DATE >= CURDATE()
                ORDER BY p.PAYMENT_ID DESC
            """, (user_id))
            rows = cursor.fetchall()
            return rows

    except Exception as e:
        logger.error(f"get_history error: {e}")
        return []
    finally:
        connection.close()

#사용자의 결제 내역 조회
def get_purchase_history(user_id):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    t.TICKET_NAME, 
                    t.TICKET_PRICE,
                    t.TOKEN_AMOUNT,
                    p.transaction_type, 
                    p.created_at
                FROM ticket t 
                JOIN token_purchase p
                ON t.TICKET_ID = p.TICKET_ID
                WHERE p.USER_ID = %s
                ORDER BY p.purchase_id DESC
            """, (user_id))
            rows = cursor.fetchall()
            return rows

    except Exception as e:
        logger.error(f"get_history error: {e}")
        return []
    finally:
        connection.close()


def get_token_deduction_history(user_id: int):
    """
    TOKEN_PURCHASE / TOKEN_USAGE를 활용해 일별 토큰 사용 이력을 계산한다.
    """
    conn = None
    try:
        conn = get_re_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            sql = """
                WITH daily_grant AS (
                    SELECT
                        DATE(created_at) AS grant_date,
                        SUM(COALESCE(purchased_tokens, 0)) AS total_granted,
                        SUM(
                            CASE
                                WHEN transaction_type IN ('subscription', 'change', 'unsubscribe')
                                    THEN COALESCE(remaining_tokens, 0)
                                ELSE 0
                            END
                        ) AS subscription_snapshot,
                        SUM(
                            CASE
                                WHEN transaction_type = 'one_time'
                                    THEN COALESCE(remaining_tokens, 0)
                                ELSE 0
                            END
                        ) AS onetime_snapshot
                    FROM TOKEN_PURCHASE
                    WHERE user_id = %s
                    GROUP BY DATE(created_at)
                ),
                daily_usage AS (
                    SELECT
                        usage_date,
                        SUM(COALESCE(used_tokens, 0)) AS total_used
                    FROM TOKEN_USAGE
                    WHERE user_id = %s
                    GROUP BY usage_date
                )
                SELECT
                    COALESCE(g.grant_date, u.usage_date) AS grant_date,
                    COALESCE(u.total_used, 0) AS total_deducted,
                    COALESCE(g.total_granted, 0) AS total_granted,
                    COALESCE(g.onetime_snapshot, 0) AS end_onetime,
                    COALESCE(g.subscription_snapshot, 0) AS end_subscription
                FROM daily_grant g
                FULL OUTER JOIN daily_usage u
                  ON g.grant_date = u.usage_date
                ORDER BY grant_date DESC
            """
            cur.execute(sql, (user_id, user_id))
            return cur.fetchall()
    finally:
        if conn is not None:
            conn.close()








# app/crud/token.py 안에 추가

def get_valid_ticket(
    cursor: pymysql.cursors.Cursor,
    user_id: int,
) -> Optional[dict]:
    """
    구독 계열 티켓 정보 (subscription / unsubscribe / change)
    오늘 기준 유효한 것 중 가장 최근 1건
    """
    sql = """
        SELECT
            tp.purchase_id,
            tp.user_id,
            tp.ticket_id,
            tp.transaction_type,
            tp.purchased_tokens,
            tp.remaining_tokens,
            tp.start_date,
            tp.end_date,
            tp.created_at,
            tp.updated_at,
            t.TICKET_NAME   AS ticket_name,
            t.BILLING_CYCLE AS billing_cycle,
            t.TICKET_TYPE   AS ticket_type,
            t.TOKEN_AMOUNT  AS ticket_token_amount
        FROM TOKEN_PURCHASE tp
        JOIN TICKET t
          ON t.TICKET_ID = tp.ticket_id
        WHERE tp.user_id = %s
          AND tp.transaction_type IN ('subscription', 'unsubscribe', 'change')
          AND (tp.start_date IS NULL OR tp.start_date <= CURDATE())
          AND (tp.end_date   IS NULL OR tp.end_date   >= CURDATE())
        ORDER BY
            tp.end_date DESC,
            tp.created_at DESC,
            tp.purchase_id DESC
        LIMIT 1
    """
    cursor.execute(sql, (user_id,))
    return cursor.fetchone()


def get_token_onetime(
    cursor: pymysql.cursors.Cursor,
    user_id: int,
) -> Optional[dict]:
    """
    단건(one_time)으로 구매한 티켓 중 가장 최근 1건.
    (remaining_tokens 조건은 걸지 않음 - 최근에 어떤 단건 상품을 샀는지 보여주기용)
    """
    sql = """
        SELECT
            tp.purchase_id,
            tp.user_id,
            tp.ticket_id,
            tp.transaction_type,
            tp.purchased_tokens,
            tp.remaining_tokens,
            tp.start_date,
            tp.end_date,
            tp.created_at,
            tp.updated_at,
            t.TICKET_NAME   AS ticket_name,
            t.BILLING_CYCLE AS billing_cycle,
            t.TICKET_TYPE   AS ticket_type,
            t.TOKEN_AMOUNT  AS ticket_token_amount
        FROM TOKEN_PURCHASE tp
        JOIN TICKET t
          ON t.TICKET_ID = tp.ticket_id
        WHERE tp.user_id = %s
          AND tp.transaction_type = 'one_time'
        ORDER BY
            tp.created_at DESC,
            tp.purchase_id DESC
        LIMIT 1
    """
    cursor.execute(sql, (user_id,))
    return cursor.fetchone()


