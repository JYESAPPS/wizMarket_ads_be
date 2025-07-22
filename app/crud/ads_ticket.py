import pymysql.cursors
from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
import pymysql
import logging
from datetime import datetime

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
            cursor.execute(select_query, (ticket_id))
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
            cursor.execute(select_query, (ticket_id))
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
        cursor.execute(query, (user_id))
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
def insert_onetime(user_id, ticket_id, token_grant, token_onetime, grant_date):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor()
        insert_query = """
            INSERT INTO ticket_token (GRANT_TYPE, USER_ID, TICKET_ID, TOKEN_GRANT, TOKEN_ONETIME, GRANT_DATE)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        #grant_type은 토큰 지급일 때 1, 소모일 때 0 
        cursor.execute(insert_query, (1, user_id, ticket_id, token_grant, token_onetime, grant_date))
        commit(connection)  # 커스텀 commit 사용

    except pymysql.MySQLError as e:
        rollback(connection)  # 커스텀 rollback 사용
        print(f"Database error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)

#사용자의 결제 내역 조회
def get_history(user_id):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT t.TICKET_NAME, t.TICKET_PRICE, p.PAYMENT_DATE, p.EXPIRE_DATE
                FROM ticket t 
                JOIN ticket_payment p
                ON t.TICKET_ID = p.TICKET_ID
                WHERE p.USER_ID = %s
                ORDER BY p.PAYMENT_DATE DESC
            """, (user_id))
            rows = cursor.fetchall()
            return rows

    except Exception as e:
        logger.error(f"get_history error: {e}")
        return []
    finally:
        connection.close()
    
def get_valid_ticket(user_id):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT t.TICKET_NAME, p.EXPIRE_DATE
                FROM ticket_payment p
                JOIN ticket t
                ON t.TICKET_ID = p.TICKET_ID           
                WHERE p.USER_ID = %s
                AND p.EXPIRE_DATE IS NOT NULL
                AND p.EXPIRE_DATE >= CURDATE()
                ORDER BY p.EXPIRE_DATE DESC
                LIMIT 1
            """, (user_id))
            result = cursor.fetchone()

        if result is None:
            return None
        return {
            "ticket_name": result[0],
            "expire": result[1]
        }
            
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
def insert_payment_history(user_id: int, ticket_id: int = 1, payment_method: str = "deduct"):
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

# 토큰 차감 시 ticket_token에 기록
def insert_token_deduction_history(user_id: int, ticket_id: int, token_grant: int, token_subscription: int, token_onetime: int, valid_until, grant_date):
    connection = get_re_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO ticket_token (
                    GRANT_TYPE, USER_ID, TICKET_ID, TOKEN_GRANT, TOKEN_SUBSCRIPTION, TOKEN_ONETIME, VALID_UNTIL, GRANT_DATE
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                0,  # GRANT_TYPE = 0 for deduction
                user_id,
                ticket_id,
                token_grant,
                token_subscription,
                token_onetime,
                valid_until,
                grant_date
            ))
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise RuntimeError(f"차감 기록 실패: {e}")
    finally:
        connection.close()