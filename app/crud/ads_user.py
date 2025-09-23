import pymysql
import logging
from fastapi import HTTPException
from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)

logger = logging.getLogger(__name__)

def check_user_id(user_id: str):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM USER WHERE user_id = %s", (user_id,))
            exists = cursor.fetchone()

        return exists
    except Exception as e:
        print(f"중복 검사 오류: {e}")
        return {"available": False}
    

def register_user(user_id, password):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            # 중복 체크
            cursor.execute("SELECT * FROM USER WHERE user_id = %s", (user_id,))
            if cursor.fetchone():
                return {"success": False, "message": "이미 존재하는 아이디입니다."}

            cursor.execute(
                "INSERT INTO USER (user_id, password) VALUES (%s, %s)",
                (user_id, password)
            )
            connection.commit()

        return {"success": True}

    except Exception as e:
        print(f"회원가입 오류: {e}")
        return {"success": False, "message": "서버 오류"}
    

# 매장 조회 : 가게명 LIKE, 도로명 ==
def get_store(store_name, road_name):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        # 입력 정리
        sn = (store_name or "").strip()
        rn = (road_name or "").strip()

        # LIKE 패턴 생성 (%,_ 이스케이프 + 양쪽 %)
        def to_like(s: str) -> str:
            s = s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            return f"%{s}%"

        where, params = [], []
        if sn:
            where.append("STORE_NAME LIKE %s")
            params.append(to_like(sn))
        if rn:
            where.append("ROAD_NAME LIKE %s")
            params.append(to_like(rn))

        if not where:
            return []

        select_query = f"""
            SELECT
                STORE_BUSINESS_NUMBER, STORE_NAME, ROAD_NAME, FLOOR_INFO, 
                BIZ_MAIN_CATEGORY_ID, BIZ_SUB_CATEGORY_ID, BIZ_DETAIL_CATEGORY_REP_NAME
            FROM REPORT
            WHERE {" AND ".join(where)}
            ORDER BY STORE_NAME ASC
        """

        cursor.execute(select_query, tuple(params))
        rows = cursor.fetchall()
        return rows

    finally:
        if cursor:
            cursor.close()
        connection.close()


# business_verification에 대표자, 사업자등록번호 추가
def insert_business_info(
        user_id,
        business_name,
        business_number
):
    conn = get_re_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        sql = """
        INSERT INTO business_verification
            (user_id, business_name, business_number, status, created_at)
        VALUES
            (%s, %s, %s, 'pending', NOW())
        """
        cursor.execute(sql, (
            user_id,
            business_name,
            business_number,
        ))

        commit(conn)
        return True

    except Exception as e:
        if conn:
            rollback(conn)
        logger.error(f"insert_business_verification error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if cursor:
            close_cursor(cursor)
        if conn:
            close_connection(conn)

# user TB에 store_business_number 업데이트
def update_user(user_id, store_business_number, status):
    connection = get_re_db_connection()
    cursor = connection.cursor()

    try:
        connection.autocommit(False)

        sql_user = """
            UPDATE user
               SET  store_business_number = %s,
                    status = %s,
                    updated_at = NOW()
             WHERE user_id = %s
        """
        cursor.execute(sql_user, (store_business_number, status, user_id))

        if cursor.rowcount == 0:
            connection.rollback()
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
        
        connection.commit()
        return True
    
    except Exception as e:
        connection.rollback()
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류")
    finally:
        cursor.close()
        connection.close()