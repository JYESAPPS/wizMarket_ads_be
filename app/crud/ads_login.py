from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from dotenv import load_dotenv
import pymysql
from fastapi import HTTPException
import logging
from app.schemas.ads import AdsInitInfo, RandomImage
import random
from typing import List, Optional

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


def insert_user_sns(email: str, provider: str, provider_id: str, device_token : str):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    logger = logging.getLogger(__name__)

    try:
        if connection.open:
            insert_query = """
                INSERT INTO user (email, login_provider, provider_id, is_active, device_token, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """
            cursor.execute(insert_query, (email, provider, provider_id, 1, device_token))
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



def get_user_by_id(user_id: int):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    logger = logging.getLogger(__name__)

    try:
        if connection.open:
            query = """
                SELECT *
                FROM user
                WHERE user_id = %s
            """
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()

            if not user:
                raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

            return user

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="DB 오류 발생")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류")
    finally:
        cursor.close()
        connection.close()



def update_user(
    user_id: int,
    store_business_number: str,
    register_tag: str,
    insta_account: Optional[str] = None,
):
    connection = get_re_db_connection()
    cursor = connection.cursor()
    logger = logging.getLogger(__name__)

    try:
        # 트랜잭션 시작
        connection.autocommit(False)

        # 1) user TB: store_business_number만 업데이트
        sql_user = """
            UPDATE user
               SET store_business_number = %s,
                   updated_at = NOW()
             WHERE user_id = %s
        """
        cursor.execute(sql_user, (store_business_number, user_id))
        if cursor.rowcount == 0:
            connection.rollback()
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

        # 2) user_info TB: register_tag / insta_account 업데이트
        #    insta_account가 비어있으면 register_tag만 업데이트
        if insta_account not in (None, ""):
            sql_info = """
                UPDATE user_info
                   SET register_tag = %s,
                       insta_account = %s,
                       updated_at = NOW()
                 WHERE user_id = %s
            """
            params_info = (register_tag, insta_account, user_id)
        else:
            sql_info = """
                UPDATE user_info
                   SET register_tag = %s,
                       updated_at = NOW()
                 WHERE user_id = %s
            """
            params_info = (register_tag, user_id)

        cursor.execute(sql_info, params_info)

        # user_info에 행이 아직 없다면(신규 유저 등) INSERT로 보완
        if cursor.rowcount == 0:
            if insta_account not in (None, ""):
                sql_insert = """
                    INSERT INTO user_info (user_id, register_tag, insta_account, created_at, updated_at)
                    VALUES (%s, %s, %s, NOW(), NOW())
                """
                cursor.execute(sql_insert, (user_id, register_tag, insta_account))
            else:
                sql_insert = """
                    INSERT INTO user_info (user_id, register_tag, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                """
                cursor.execute(sql_insert, (user_id, register_tag))

        connection.commit()
        return True

    except pymysql.MySQLError as e:
        connection.rollback()
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="DB 오류 발생")
    except Exception as e:
        connection.rollback()
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류")
    finally:
        cursor.close()
        connection.close()





def select_insta_account(store_business_number: str):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    logger = logging.getLogger(__name__)

    try:
        if connection.open:
            query = """
                SELECT insta_account
                FROM user
                WHERE store_business_number = %s
            """
            cursor.execute(query, (store_business_number,))
            result = cursor.fetchone()

            if not result:
                return None

            return result['insta_account']

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="DB 오류 발생")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류")
    finally:
        cursor.close()
        connection.close()




def update_device_token(user_id: int, device_token: str):
    connection = get_re_db_connection()
    cursor = connection.cursor()
    logger = logging.getLogger(__name__)

    try:
        if connection.open:
            update_query = """
                UPDATE user
                SET device_token = %s, updated_at = NOW()
                WHERE user_id = %s
            """
            cursor.execute(update_query, (device_token, user_id))

        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

        return True

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="DB 오류 발생")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류")
    finally:
        cursor.close()
        connection.close()




def select_user_id(store_business_number):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    logger = logging.getLogger(__name__)

    try:
        if connection.open:
            query = """
                SELECT user_id
                FROM user
                WHERE store_business_number = %s
            """
            cursor.execute(query, (store_business_number,))
            result = cursor.fetchone()

            if not result:
                return None

            return result['user_id']

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="DB 오류 발생")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류")
    finally:
        cursor.close()
        connection.close()



