from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
from app.schemas.ads_notice import AdsNotice
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