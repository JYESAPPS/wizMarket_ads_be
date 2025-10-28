from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
from app.schemas.ads_push import AllUserDeviceToken, UserReserve
from typing import List
import pymysql
import logging
from datetime import datetime
import pytz
import json

logger = logging.getLogger(__name__)



def select_user_id_token() -> List[AllUserDeviceToken]:
    conn = get_re_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    try:
        sql = """
            SELECT
                USER_ID,
                TRIM(DEVICE_TOKEN) AS DEVICE_TOKEN
            FROM USER_DEVICE
            WHERE USER_ID IS NOT NULL
              AND DEVICE_TOKEN IS NOT NULL
              AND DEVICE_TOKEN <> '';
        """
        cur.execute(sql)
        rows = cur.fetchall() or []
        # None-safe 추가 방어막 (이중 안전)
        result = []
        for r in rows:
            uid = r.get("USER_ID")
            tok = r.get("DEVICE_TOKEN")
            if uid is None or tok is None or tok == "":
                continue
            result.append(AllUserDeviceToken(user_id=int(uid), device_token=str(tok)))
        return result
    except pymysql.MySQLError as e:
        # 스케줄러에서 터지지 않게: 로그만 남기고 빈 리스트
        print(f"[select_user_id_token] MySQL Error: {e}")
        return []
    except Exception as e:
        print(f"[select_user_id_token] Unexpected Error: {e}")
        return []
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass


def select_recent_id_token() -> List[AllUserDeviceToken]:
    conn = get_re_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    try:
        sql = """
            SELECT ud.USER_ID, TRIM(ud.DEVICE_TOKEN) AS DEVICE_TOKEN
            FROM wiz_report.user_device AS ud
            JOIN (
            SELECT USER_ID, MAX(last_seen) AS max_last_seen
            FROM wiz_report.user_device
            WHERE USER_ID IS NOT NULL
                AND DEVICE_TOKEN IS NOT NULL
                AND TRIM(DEVICE_TOKEN) <> ''
            GROUP BY USER_ID
            ) s
            ON ud.USER_ID = s.USER_ID
            AND ud.last_seen = s.max_last_seen;
        """
        cur.execute(sql)
        rows = cur.fetchall() or []
        # None-safe 추가 방어막 (이중 안전)
        result = []
        for r in rows:
            uid = r.get("USER_ID")
            tok = r.get("DEVICE_TOKEN")
            if uid is None or tok is None or tok == "":
                continue
            result.append(AllUserDeviceToken(user_id=int(uid), device_token=str(tok)))
        return result
    except pymysql.MySQLError as e:
        # 스케줄러에서 터지지 않게: 로그만 남기고 빈 리스트
        print(f"[select_recent_id_token] MySQL Error: {e}")
        return []
    except Exception as e:
        print(f"[select_recent_id_token] Unexpected Error: {e}")
        return []
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass


def crud_get_user_reserves(user_id: int) -> list[UserReserve]:
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        if connection.open:
            today_str = datetime.now().strftime("%Y-%m-%d")
            query = """
                SELECT *
                FROM user_reserve
                WHERE user_id = %s AND end_date >= %s
            """
            cursor.execute(query, (user_id, today_str))
            rows = cursor.fetchall()

            return [UserReserve(**row) for row in rows]

    except Exception as e:
        logger.error(f"[예약 조회 오류] {e}")
        raise HTTPException(status_code=500, detail="예약 정보 조회 실패")
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()




def is_user_due_for_push(user_id: int) -> bool:
    now = datetime.now(pytz.timezone("Asia/Seoul"))
    today = now.date()
    current_time_str = now.strftime("%H:%M")   # 예: "14:00"
    current_weekday = now.strftime("%a")       # 예: "Mon"
    today_str = today.strftime("%Y-%m-%d")

    # 1. 예약 정보 가져오기
    reserves = crud_get_user_reserves(user_id)
    # print(reserves)
    for reserve in reserves:
        # 날짜 유효성 검사
        if not (reserve.start_date <= today <= reserve.end_date):
            continue

        # 시간 조건 확인
        try:
            upload_times = json.loads(reserve.upload_times)  # ex: ["10:00", "14:00"]
        except Exception:
            continue

        if current_time_str not in upload_times:
            continue

        # 반복 조건 확인
        if reserve.repeat_type == "daily":
            # print("매일 조건")
            return True

        elif reserve.repeat_type == "weekly":
            try:
                weekly_days = json.loads(reserve.weekly_days)  # ex: ["Mon", "Wed"]
                if current_weekday in weekly_days:
                    return True
            except Exception:
                continue

        elif reserve.repeat_type == "monthly":
            try:
                monthly_days = json.loads(reserve.monthly_days)  # ex: [1, 10, 25]
                if today_str in monthly_days:
                    return True
            except Exception:
                continue

    return False