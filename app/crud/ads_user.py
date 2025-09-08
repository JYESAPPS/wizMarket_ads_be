import pymysql
from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)


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
                STORE_BUSINESS_NUMBER, STORE_NAME, ROAD_NAME, BIZ_MAIN_CATEGORY_ID, 
                BIZ_SUB_CATEGORY_ID, BIZ_DETAIL_CATEGORY_REP_NAME
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