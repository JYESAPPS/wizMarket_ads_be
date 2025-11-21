from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
from app.schemas.ads_reserve import ReserveGetList
from typing import List
import pymysql
import logging
import uuid
import json

logger = logging.getLogger(__name__)



def insert_reserve(request):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor) 

        insert_query = """
            INSERT INTO user_reserve (
                user_id,
                title,
                repeat_type,
                repeat_count,
                start_date,
                end_date,
                upload_times,
                weekly_days,
                monthly_days,
                straight
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            insert_query,
            (
                int(request.user_id),
                request.title,
                request.repeat_type,
                request.repeat_count,
                request.start_date,
                request.end_date,
                json.dumps(request.upload_times),
                json.dumps(request.weekly_days) if request.weekly_days else None,
                json.dumps(request.monthly_days) if request.monthly_days else None,
                request.straight
            ),
        )

        reserve_id = cursor.lastrowid  # ✅ 방금 삽입된 PK 가져오기
        commit(connection)

        select_query = """
            SELECT 
                RESERVE_ID AS reserve_id,
                TITLE AS title,
                REPEAT_TYPE AS repeat_type,
                REPEAT_COUNT AS repeat_count,
                START_DATE AS start_date,
                END_DATE AS end_date,
                UPLOAD_TIMES AS upload_times,
                WEEKLY_DAYS AS weekly_days,
                MONTHLY_DAYS AS monthly_days,
                IS_ACTIVE AS is_active,
                CREATED_AT AS created_at,
                STRAIGHT AS straight
            FROM user_reserve
            WHERE RESERVE_ID = %s;

        """
        cursor.execute(select_query, (reserve_id,))
        new_item = cursor.fetchone()
        return new_item

    except Exception as e:
        rollback(connection)
        print(f"❌ 예약 저장 오류: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)




def get_user_reserve_list(request):
    user_id = request.user_id
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        if connection.open:
            select_query = """
                SELECT 
                    RESERVE_ID,
                    TITLE,
                    REPEAT_TYPE,
                    REPEAT_COUNT,
                    START_DATE,
                    END_DATE,
                    UPLOAD_TIMES,
                    WEEKLY_DAYS,
                    MONTHLY_DAYS,
                    STRAIGHT,
                    IS_ACTIVE,
                    CREATED_AT
                FROM user_reserve
                WHERE USER_ID = %s;
            """
            cursor.execute(select_query, (user_id,))
            rows = cursor.fetchall()

            if not rows:
                return []

            
            return [
                ReserveGetList(
                    reserve_id = row["RESERVE_ID"],
                    title = row["TITLE"],
                    repeat_type=row["REPEAT_TYPE"],
                    repeat_count=row["REPEAT_COUNT"],
                    start_date=row["START_DATE"],
                    end_date=row["END_DATE"],
                    upload_times=json.loads(row["UPLOAD_TIMES"]),
                    weekly_days=json.loads(row["WEEKLY_DAYS"]) if row["WEEKLY_DAYS"] else None,
                    monthly_days=json.loads(row["MONTHLY_DAYS"]) if row["MONTHLY_DAYS"] else None,
                    straight=row["STRAIGHT"],
                    is_active=row["IS_ACTIVE"],
                    created_at = row["CREATED_AT"]
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

def get_reserve_push(request):
    user_id = request.user_id
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        if connection.open:
            select_query = """
                SELECT 
                    RESERVE
                FROM USER_PUSH
                WHERE USER_ID = %s
            """
            cursor.execute(select_query, (user_id))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=500, detail="데이터베이스 조회에 실패했습니다.")

            value = row.get("RESERVE")
            return bool(int(value)) if value is not None else False 

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
    except Exception as e:
        logger.error(f"Unexpected Error in get_push: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류가 발생했습니다.")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def update_push_consent(request):
    user_id = request.user_id
    connection = get_re_db_connection()
    try:
        with connection.cursor() as cursor:
            update_sql = """
                UPDATE USER_PUSH
                SET RESERVE = 1
                WHERE USER_ID = %s
            """
            cursor.execute(update_sql, (user_id))
            connection.commit()
        return True
    except Exception as e:
        logger.error(f"상태 변경 실패: {e}")
        raise HTTPException(status_code=500, detail="수신 여부 변경 실패")
    finally:
        connection.close()


def update_reserve_status(request):
    reserve_id = request.reserve_id
    connection = get_re_db_connection()
    try:
        with connection.cursor() as cursor:
            update_sql = """
                UPDATE user_reserve
                SET IS_ACTIVE = CASE WHEN IS_ACTIVE = 1 THEN 0 ELSE 1 END
                WHERE RESERVE_ID = %s
            """
            cursor.execute(update_sql, (reserve_id,))
            connection.commit()
        return True
    except Exception as e:
        logger.error(f"상태 토글 실패: {e}")
        raise HTTPException(status_code=500, detail="상태 변경 실패")
    finally:
        connection.close()


def delete_reserve(request):
    reserve_id = request.reserve_id
    connection = get_re_db_connection()
    try:
        with connection.cursor() as cursor:
            update_sql = """
                DELETE FROM user_reserve
                WHERE RESERVE_ID = %s
            """
            cursor.execute(update_sql, (reserve_id,))
            connection.commit()
        return True
    except Exception as e:
        logger.error(f"상태 토글 실패: {e}")
        raise HTTPException(status_code=500, detail="상태 변경 실패")
    finally:
        connection.close()


def update_reserve(request):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        update_query = """
            UPDATE user_reserve
            SET
                title = %s,
                repeat_type = %s,
                repeat_count = %s,
                start_date = %s,
                end_date = %s,
                upload_times = %s,
                weekly_days = %s,
                monthly_days = %s,
                straight = %s
            WHERE reserve_id = %s
        """

        cursor.execute(
            update_query,
            (
                request.title,
                request.repeat_type,
                request.repeat_count,
                request.start_date,
                request.end_date,
                json.dumps(request.upload_times),
                json.dumps(request.weekly_days) if request.weekly_days else None,
                json.dumps(request.monthly_days) if request.monthly_days else None,
                request.straight,
                request.reserve_id,
            ),
        )

        commit(connection)

        # 수정된 데이터 다시 조회해서 반환
        select_query = """
            SELECT 
                RESERVE_ID AS reserve_id,
                REPEAT_TYPE AS repeat_type,
                REPEAT_COUNT AS repeat_count,
                START_DATE AS start_date,
                END_DATE AS end_date,
                UPLOAD_TIMES AS upload_times,
                WEEKLY_DAYS AS weekly_days,
                MONTHLY_DAYS AS monthly_days,
                IS_ACTIVE AS is_active,
                CREATED_AT AS created_at
            FROM user_reserve
            WHERE RESERVE_ID = %s;
        """
        cursor.execute(select_query, (request.reserve_id,))
        updated_item = cursor.fetchone()
        return updated_item

    except Exception as e:
        rollback(connection)
        print(f"❌ 예약 수정 오류: {e}")
        raise HTTPException(status_code=500, detail="예약 수정 실패")
    finally:
        close_cursor(cursor)
        close_connection(connection)





