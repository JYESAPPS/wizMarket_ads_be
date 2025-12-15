import pymysql.cursors
from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
import pymysql
import logging
from datetime import datetime
from typing import Optional



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

#사용자의 단건 현재 토큰 개수 불러오기
def get_latest_token_onetime(user_id: int):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        query = """
            SELECT TOKEN_ONETIME
            FROM ticket_token
            WHERE USER_ID=%s
            AND TOKEN_ONETIME IS NOT NULL
            ORDER BY GRANT_ID DESC
            LIMIT 1
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        if result is None:
            return 0
        return result["TOKEN_ONETIME"] 

    except Exception as e:
        logger.error(f"get_latest_token_onetime error: {e}")
        return None

    finally:
        cursor.close()
        connection.close()

# 사용자의 현재 정기 토큰+기한 호출
def get_latest_token_subscription(user_id):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT TOKEN_SUBSCRIPTION, VALID_UNTIL
                FROM ticket_token
                WHERE USER_ID = %s
                AND TOKEN_ONETIME IS NOT NULL
                ORDER BY GRANT_ID DESC
                LIMIT 1
            """, (user_id))
            result = cursor.fetchone()

        if result is None:
            return {
                "sub": 0,
                "valid": None
            }
        return {
            "sub": result[0],
            "valid": result[1]
        }
            
    except Exception as e:
        logger.error(f"get_history error: {e}")
        return []
    finally:
        connection.close()     

#사용자의 토큰 내역에 단건 삽입
def insert_onetime(user_id, ticket_id, token_grant, token_subscription, token_onetime, grant_date):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor()
        insert_query = """
            INSERT INTO ticket_token (GRANT_TYPE, USER_ID, TICKET_ID, TOKEN_GRANT, TOKEN_SUBSCRIPTION, TOKEN_ONETIME, GRANT_DATE)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        #grant_type은 토큰 지급일 때 1, 소모일 때 0 
        cursor.execute(insert_query, (1, user_id, ticket_id, token_grant, token_subscription, token_onetime, grant_date))
        commit(connection)  # 커스텀 commit 사용

    except pymysql.MySQLError as e:
        rollback(connection)  # 커스텀 rollback 사용
        print(f"Database error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)



# 사용자의 토큰 내역에 월구독 삽입
def insest_monthly(user_id, ticket_id, token_grant, token_subscription, token_onetime, grant_date):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor()
        insert_query = """
            INSERT INTO ticket_token (GRANT_TYPE, USER_ID, TICKET_ID, TOKEN_GRANT, TOKEN_SUBSCRIPTION, TOKEN_ONETIME, GRANT_DATE)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        #grant_type은 토큰 지급일 때 1, 소모일 때 0 
        cursor.execute(insert_query, (1, user_id, ticket_id, token_grant, token_subscription, token_onetime, grant_date))
        commit(connection)  # 커스텀 commit 사용

    except pymysql.MySQLError as e:
        rollback(connection)  # 커스텀 rollback 사용
        print(f"Database error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)


# 사용자의 토큰 내역에 년구독 삽입
def insest_yearly(user_id, ticket_id, token_grant, token_subscription, token_onetime, grant_date):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor()
        insert_query = """
            INSERT INTO ticket_token (GRANT_TYPE, USER_ID, TICKET_ID, TOKEN_GRANT, TOKEN_SUBSCRIPTION, TOKEN_ONETIME, GRANT_DATE)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        #grant_type은 토큰 지급일 때 1, 소모일 때 0 
        cursor.execute(insert_query, (1, user_id, ticket_id, token_grant, token_subscription, token_onetime, grant_date))
        commit(connection)  # 커스텀 commit 사용

    except pymysql.MySQLError as e:
        rollback(connection)  # 커스텀 rollback 사용
        print(f"Database error: {e}")
        raise

    finally:
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


# 구독 토큰 차감
def update_subscription_token(user_id: int):
    connection = get_re_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE ticket_token
                SET TOKEN_SUBSCRIPTION = TOKEN_SUBSCRIPTION - 1
                WHERE USER_ID = %s
                AND TOKEN_SUBSCRIPTION > 0
                ORDER BY GRANT_ID DESC
                LIMIT 1
            """, (user_id,))
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise RuntimeError(f"구독 토큰 차감 실패: {e}")
    finally:
        connection.close()

# 단건 토큰 차감
def update_onetime_token(user_id: int):
    connection = get_re_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE ticket_token
                SET TOKEN_ONETIME = TOKEN_ONETIME - 1
                WHERE USER_ID = %s
                AND TOKEN_ONETIME > 0
                ORDER BY GRANT_ID DESC
                LIMIT 1
            """, (user_id,))
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise RuntimeError(f"단건 토큰 차감 실패: {e}")
    finally:
        connection.close()

# ticket_payment 테이블에 차감 이력 저장
def insert_payment_history(user_id: int, ticket_id: int = 0, payment_method: str = "deduct"):
    connection = get_re_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO ticket_payment (
                    USER_ID, TICKET_ID, PAYMENT_METHOD, PAYMENT_DATE
                ) VALUES (%s, %s, %s, %s)
            """, (
                user_id,
                ticket_id,
                payment_method,
                datetime.now()
            ))
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise RuntimeError(f"토큰 차감 INSERT 실패: {e}")
    finally:
        connection.close()


def upsert_token_usage(user_id: int, grant_date, token_grant: int):
    connection = get_re_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
            INSERT INTO TOKEN_USAGE (user_id, usage_date, used_tokens)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                used_tokens = used_tokens + VALUES(used_tokens),
                updated_at = CURRENT_TIMESTAMP
            """, (user_id, grant_date, token_grant))
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise RuntimeError(f"토큰 사용 기록 실패: {e}")
    finally:
        connection.close()

# 토큰 차감 기록 가져오기
def get_token_deduction_history(user_id: int):
    connection = get_re_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT
                    DATE(GRANT_DATE) AS grant_date,

                    -- 차감량과 지급량을 따로 합산
                    SUM(CASE WHEN GRANT_TYPE = 0 THEN TOKEN_GRANT ELSE 0 END) AS total_deducted,
                    SUM(CASE WHEN GRANT_TYPE = 1 THEN TOKEN_GRANT ELSE 0 END) AS total_granted,

                    SUBSTRING_INDEX(GROUP_CONCAT(TOKEN_ONETIME ORDER BY GRANT_DATE DESC), ',', 1) AS end_onetime,
                    SUBSTRING_INDEX(GROUP_CONCAT(TOKEN_SUBSCRIPTION ORDER BY GRANT_DATE DESC), ',', 1) AS end_subscription

                FROM ticket_token
                WHERE USER_ID = %s
                GROUP BY DATE(GRANT_DATE)
                ORDER BY GRANT_DATE DESC
            """, (user_id,))
            return cursor.fetchall()
    finally:
        connection.close()





# 토큰 차감 기록 일별 가져오기
def get_token_usage_history(user_id: int):
    conn = None
    try:
        conn = get_re_db_connection()

        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            sql = """
                -- 1) 사용 기록 (TOKEN_USAGE)
                SELECT
                    'use' AS event_type,
                    updated_at AS event_time,   -- 언제 썼는지
                    NULL AS purchase_id,
                    0 AS purchased_tokens,
                    used_tokens
                FROM TOKEN_USAGE
                WHERE user_id = %s

                UNION ALL

                -- 2) 구매 기록 (TOKEN_PURCHASE)
                SELECT
                    'purchase' AS event_type,
                    created_at AS event_time,   -- 언제 결제(구매)했는지
                    purchase_id,
                    COALESCE(purchased_tokens, 0) AS purchased_tokens,
                    0 AS used_tokens
                FROM TOKEN_PURCHASE
                WHERE user_id = %s
                AND transaction_type <> 'fail'

                ORDER BY event_time DESC
            """
            cur.execute(sql, (user_id, user_id))
            rows = cur.fetchall()
            return rows

    except Exception as e:
        logger.error(f"[get_token_history] DB error: {e}")
        return []
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


