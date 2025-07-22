from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
from app.schemas.ads_faq import AdsFaqList, AdsTagList
from typing import List
import pymysql
import logging

logger = logging.getLogger(__name__)



def get_faq() -> List[AdsFaqList]:
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        if connection.open:
            select_query = """
                SELECT 
                    c.faq_category_id AS category_id,
                    c.name AS category_name,
                    f.faq_id AS faq_id,
                    f.question,
                    f.answer
                FROM faq_category c
                LEFT JOIN faq f ON c.faq_category_id = f.faq_category_id
                WHERE f.is_active = TRUE
            """
            cursor.execute(select_query)
            rows = cursor.fetchall()

            if not rows:
                return []

            return [
                AdsFaqList(
                    category_id=row["category_id"],
                    category_name=row["category_name"],
                    faq_id=row["faq_id"],
                    question=row["question"],
                    answer=row["answer"]
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

def get_tag() -> List[AdsTagList]:
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        if connection.open:
            select_query = """
                SELECT 
                    name
                FROM faq_category
            """
            cursor.execute(select_query)
            rows = cursor.fetchall()

            if not rows:
                return []

            return [
                AdsTagList(
                    name=row["name"]
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





def create_faq(question: str, answer: str, category_name: str):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor()

        # 1️⃣ 카테고리 ID 조회
        select_query = "SELECT faq_category_id FROM faq_category WHERE name = %s"
        cursor.execute(select_query, (category_name,))
        result = cursor.fetchone()

        # 2️⃣ 없으면 카테고리 새로 추가
        if result:
            category_id = result[0]
        else:
            insert_category_query = "INSERT INTO faq_category (name) VALUES (%s)"
            cursor.execute(insert_category_query, (category_name,))
            category_id = cursor.lastrowid  # 방금 삽입한 ID 가져오기

        # 3️⃣ FAQ 등록
        insert_faq_query = """
            INSERT INTO faq (faq_category_id, question, answer, is_active)
            VALUES (%s, %s, %s, TRUE)
        """
        cursor.execute(insert_faq_query, (category_id, question, answer))

        commit(connection)

    except pymysql.MySQLError as e:
        rollback(connection)
        print(f"DB 오류 발생: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)
