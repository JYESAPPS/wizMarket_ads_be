

from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
from app.schemas.ads_plan import PlanList
from typing import List
import pymysql
import logging

logger = logging.getLogger(__name__)


def get_plan_list() -> List[PlanList]:
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        if connection.open:
            select_query = """
                SELECT 
                    TICKET_ID, TICKET_NAME, TICKET_PRICE, TICKET_TYPE, BILLING_CYCLE, TOKEN_AMOUNT
                FROM TICKET
                WHERE TICKET_NAME = '테스트 이용권';
            """
            cursor.execute(select_query)
            rows = cursor.fetchall()

            if not rows:
                return []

            return [
                PlanList(
                    TICKET_ID=row["TICKET_ID"],
                    TICKET_NAME=row["TICKET_NAME"],
                    TICKET_PRICE=row["TICKET_PRICE"],
                    TICKET_TYPE=row["TICKET_TYPE"],
                    BILLING_CYCLE=row["BILLING_CYCLE"],
                    TOKEN_AMOUNT=row["TOKEN_AMOUNT"],
                ) for row in rows
            ]

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



def insert_fee(ticket_name, ticket_price, ticket_type, billing_cycle, token_amount):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor()
        billing_cycle = None if ticket_type == "베이직" else billing_cycle

        insert_query = """
            INSERT INTO TICKET (TICKET_NAME, TICKET_PRICE, TICKET_TYPE, BILLING_CYCLE, TOKEN_AMOUNT)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (ticket_name, ticket_price, ticket_type, billing_cycle, token_amount))
        commit(connection)  # 커스텀 commit 사용

    except pymysql.MySQLError as e:
        rollback(connection)  # 커스텀 rollback 사용
        print(f"Database error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)





def delete_fee(ticket_id: int):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor()

        delete_query = """
            DELETE FROM TICKET
            WHERE TICKET_ID = %s
        """
        cursor.execute(delete_query, (ticket_id,))
        commit(connection)  # 커스텀 commit 사용

    except pymysql.MySQLError as e:
        rollback(connection)
        print(f"Database error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)
