import pymysql.cursors
from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
import pymysql
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# token_purchase 삽입 (구매)
def insert_purchase(user, ticket, type, purchased, remaining, start, end):
    connection = get_re_db_connection()

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
            ) VALUES (%s, %s, %s, %s, %s, %s, %s);
        """

        cursor.execute(insert_query, (user, ticket, type, purchased, remaining, start, end))
        commit(connection)  # 커스텀 commit 사용

    except pymysql.MySQLError as e:
        rollback(connection)  # 커스텀 rollback 사용
        print(f"Database error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)


# 사용자의 만료되지 않은 가장 최근 구독 내역 확인
def get_lastest_subscription(user_id):
    try:
        connection = get_re_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT transaction_type, remaining_tokens
                FROM TOKEN_PURCHASE
                WHERE user_id = %s
                AND transaction_type IN ('subscription', 'change')
                AND end_date >= CURDATE()
                ORDER BY purchase_id DESC
                LIMIT 1;
            """, (user_id))
            result = cursor.fetchone()

        if result is None:
            return {"transaction_type": None, "remaining_tokens": 0}
        
        return {
            "transaction_type": result["transaction_type"],
            "remaining_tokens": result["remaining_tokens"],
        }
            
    except Exception as e:
        logger.error(f"get_subscription_error: {e}")
        return []
    finally:
        connection.close()     


# 사용자의 가장 최근 기록 (단건 제외)
def get_lastest_history(user_id):
    try:
        connection = get_re_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT
                    transaction_type
                FROM TOKEN_PURCHASE
                WHERE user_id = %s
                AND transaction_type <> 'one_time'
                ORDER BY purchase_id DESC
                LIMIT 1;
            """, (user_id))
            result = cursor.fetchone()

        if result is None:
            return None
        return result["transaction_type"]
            
    except Exception as e:
        logger.error(f"get_subscription_error: {e}")
        return []
    finally:
        connection.close()
