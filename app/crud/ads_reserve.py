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
        cursor = connection.cursor()

        insert_query = """
            INSERT INTO user_reserve (
                user_id,
                repeat_type,
                repeat_count,
                start_date,
                end_date,
                upload_times,
                weekly_days,
                monthly_days
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            insert_query,
            (
                int(request.user_id),
                request.repeat_type,
                request.repeat_count,
                request.start_date,
                request.end_date,
                json.dumps(request.upload_times),
                json.dumps(request.weekly_days) if request.weekly_days else None,
                json.dumps(request.monthly_days) if request.monthly_days else None,
            ),
        )

        commit(connection)

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
                    REPEAT_TYPE,
                    REPEAT_COUNT,
                    START_DATE,
                    END_DATE,
                    UPLOAD_TIMES,
                    WEEKLY_DAYS,
                    MONTHLY_DAYS,
                    IS_ACTIVE,
                    CREATED_AT
                FROM USER_RESERVE
                WHERE USER_ID = %s;
            """
            cursor.execute(select_query, (user_id,))
            rows = cursor.fetchall()

            if not rows:
                return []

            
            return [
                ReserveGetList(
                    reserve_id = row["RESERVE_ID"],
                    repeat_type=row["REPEAT_TYPE"],
                    repeat_count=row["REPEAT_COUNT"],
                    start_date=row["START_DATE"],
                    end_date=row["END_DATE"],
                    upload_times=json.loads(row["UPLOAD_TIMES"]),   # ✅ 여기만 수정
                    weekly_days=json.loads(row["WEEKLY_DAYS"]) if row["WEEKLY_DAYS"] else None,
                    monthly_days=json.loads(row["MONTHLY_DAYS"]) if row["MONTHLY_DAYS"] else None,
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



def update_reserve_status(request):
    reserve_id = request.reserve_id
    connection = get_re_db_connection()
    try:
        with connection.cursor() as cursor:
            update_sql = """
                UPDATE USER_RESERVE
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



