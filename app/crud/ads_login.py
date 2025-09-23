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


def insert_user_sns(email: str | None, provider: str, provider_id: str):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    logger = logging.getLogger(__name__)

    try:
        if connection.open:
            # ✅ 업서트: email 또는 (login_provider, provider_id) UNIQUE에 걸리면 업데이트
            upsert_sql = """
                INSERT INTO user (email, login_provider, provider_id, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, 1, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    login_provider = VALUES(login_provider),
                    provider_id    = VALUES(provider_id),
                    is_active      = VALUES(is_active),
                    updated_at     = NOW()
            """
            cursor.execute(upsert_sql, (email, provider, provider_id))
            connection.commit()

            # 새로 삽입이면 lastrowid 존재, 기존행 업데이트면 0 또는 None
            user_id = cursor.lastrowid
            if not user_id:
                # ✅ 기존 레코드 id 조회 (email 우선, 없으면 provider+provider_id)
                if email:
                    cursor.execute("SELECT user_id FROM user WHERE email = %s LIMIT 1", (email,))
                else:
                    cursor.execute(
                        "SELECT user_id FROM user WHERE login_provider = %s AND provider_id = %s LIMIT 1",
                        (provider, provider_id),
                    )
                row = cursor.fetchone()
                user_id = row["id"] if row else None

            if not user_id:
                raise HTTPException(status_code=500, detail="사용자 식별 실패")

            return user_id

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="회원 가입 중 DB 오류 발생")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류")
    finally:
        try: cursor.close()
        except: pass
        try: connection.close()
        except: pass




# 다중 기기 처리
def upsert_user_device(
    user_id: int,
    installation_id: str,
    device_token: str | None = None,
):
    connection = get_re_db_connection()
    cursor = connection.cursor()
    logger = logging.getLogger(__name__)

    try:
        sql = """
        INSERT INTO user_device
            (user_id, platform, installation_id, device_token, is_active, last_seen, created_at, updated_at)
        VALUES
            (%s, 'android', %s, %s, 1, NOW(), NOW(), NOW())
        ON DUPLICATE KEY UPDATE
            user_id      = VALUES(user_id),        -- 계정 전환 시 소유자 재귀속
            platform     = 'android',
            device_token = COALESCE(VALUES(device_token), device_token),  -- None이면 기존 유지
            is_active    = 1,
            last_seen    = NOW(),
            updated_at   = NOW()
        """
        cursor.execute(sql, (user_id, installation_id, device_token))
        connection.commit()
        return True
    except pymysql.MySQLError as e:
        connection.rollback()
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="디바이스 업서트 실패")
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




def update_device_token(
    user_id: int,
    device_token: str,
    platform: str = "android",
) -> bool:
    conn = get_re_db_connection()
    cur = conn.cursor()
    logger = logging.getLogger(__name__)

    try:
        conn.autocommit(False)


            # ✅ 권장 경로: (user_id, platform, device_fingerprint)로 upsert
        sql = """
            INSERT INTO user_device (
                user_id, platform, device_token,
                is_active, last_seen, created_at, updated_at
            ) VALUES (%s, %s, %s, 1, NOW(), NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                device_token = VALUES(device_token),
                is_active    = 1,
                last_seen    = NOW(),
                updated_at   = NOW();
            """
        cur.execute(sql, (user_id, platform, device_token))


        conn.commit()
        return True

    except pymysql.MySQLError as e:
        conn.rollback()
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="DB 오류 발생")
    except Exception as e:
        conn.rollback()
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류")
    finally:
        cur.close()
        conn.close()





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


# user_info에 성명, 생년월일 삽입
def insert_init_info(user_id, name, birth):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO USER_INFO (user_id, name, birth_year)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (user_id, name, birth))
        connection.commit()
        return True  # ✅ 성공 시 True 반환

    except Exception as e:
        print(f"회원 정보 삽입 오류: {e}")
        return False

# user_info: 성명, 생년월일 수정
def update_init_info(user_id, name, birth):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = """
                UPDATE USER_INFO
                SET name = %s,
                    birth_year = %s
                WHERE user_id = %s
            """
            cursor.execute(sql, (name, birth, user_id))

        connection.commit()
        return True  # ✅ 성공 시 True 반환

    except Exception as e:
        print(f"회원 정보 업데이트 오류: {e}")
        return False
    
# 인증 성공
def update_verified(user_id):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = """
                UPDATE USER_INFO
                SET verified = 1
                WHERE user_id = %s
            """
            cursor.execute(sql, (user_id))

        connection.commit()
        return True 

    except Exception as e:
        print(f"회원 정보 업데이트 오류: {e}")
        return False

# permission_confirmed 조회 
def get_permission_confirmed(user_id: int):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = """
                SELECT permission_confirmed FROM `user` WHERE user_id = %s
            """
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]  # 0 또는 1 반환
            else:
                return 0
    except Exception as e:
        print(f"permission_confirmed 조회 오류: {e}")
        return False

# permission_confirmed 업데이트
def update_permission_confirmed(user_id: int):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = """UPDATE `user` SET permission_confirmed = 1 WHERE user_id = %s"""
            cursor.execute(sql, (user_id,))
        connection.commit()
        return True
    except Exception as e:
        print(f"permission_confirmed 조회 오류: {e}")
        return False