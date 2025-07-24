from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from dotenv import load_dotenv
import pymysql
from fastapi import HTTPException
import logging
from app.schemas.ads import AdsInitInfo, RandomImage
import random
from typing import List

def ads_login(email: str, temp_pw: str):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT user_id, type, store_business_number FROM USER WHERE email = %s AND temp_pw = %s"
            cursor.execute(sql, (email, temp_pw))
            user = cursor.fetchone()

        return user if user else None

    except Exception as e:
        print(f"로그인 조회 오류: {e}")
        return None

def get_category():
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT id, name FROM detail_category"
            cursor.execute(sql)
            rows = cursor.fetchall()

        # ✅ id와 name 모두 포함하여 리턴
        return [{"id": row[0], "name": row[1]} for row in rows] if rows else []

    except Exception as e:
        print(f"목록 조회 오류: {e}")
        return []



def get_image_list(category_id: int):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    logger = logging.getLogger(__name__)

    try:
        if connection.open:
            # 카테고리 ID에 따라 썸네일 이미지 조회
            select_query = """
                SELECT tp.image_path, t.design_id, t.prompt
                FROM thumbnail t
                JOIN thumbnail_path tp ON t.thumbnail_id = tp.thumbnail_id
                WHERE t.category_id = %s
            """
            cursor.execute(select_query, (category_id,))
            rows = cursor.fetchall()

            if not rows:
                raise HTTPException(
                    status_code=404,
                    detail="해당 카테고리 및 디자인에 대한 이미지가 존재하지 않습니다."
                )

            return rows

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="DB 오류 발생")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류")
    finally:
        cursor.close()
        connection.close()




def get_user_by_provider(login_provider: str, provider_id: str):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    logger = logging.getLogger(__name__)

    try:
        if connection.open:
            query = """
                SELECT *
                FROM user
                WHERE login_provider = %s AND provider_id = %s
            """
            cursor.execute(query, (login_provider, provider_id))
            user = cursor.fetchone()

            return user  # dict 형태

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="DB 오류 발생")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류")
    finally:
        cursor.close()
        connection.close()


def insert_user_kakao(email: str, provider: str, provider_id: str):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    logger = logging.getLogger(__name__)

    try:
        if connection.open:
            insert_query = """
                INSERT INTO user (email, login_provider, provider_id, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """
            cursor.execute(insert_query, (email, provider, provider_id, 1))
            connection.commit()

            # ✅ 방금 삽입한 user_id 가져오기
            user_id = cursor.lastrowid
            return user_id

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="회원 가입 중 DB 오류 발생")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류")
    finally:
        cursor.close()
        connection.close()


def update_user_token(user_id: int, access_token: str, refresh_token: str):
    connection = get_re_db_connection()
    cursor = connection.cursor()
    logger = logging.getLogger(__name__)

    try:
        if connection.open:
            update_query = """
                UPDATE user
                SET access_token = %s,
                    refresh_token = %s,
                    updated_at = NOW()
                WHERE user_id = %s
            """
            cursor.execute(update_query, (access_token, refresh_token, user_id))
            connection.commit()
    except Exception as e:
        logger.error(f"토큰 저장 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="토큰 저장 실패")
    finally:
        cursor.close()
        connection.close()
