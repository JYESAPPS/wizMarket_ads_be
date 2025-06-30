from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)

def ads_login(email: str, temp_pw: str):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT user_id FROM USER WHERE email = %s AND temp_pw = %s"
            cursor.execute(sql, (email, temp_pw))
            user = cursor.fetchone()

        return user[0] if user else None

    except Exception as e:
        print(f"로그인 조회 오류: {e}")
        return None

def get_category():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT detail_category_name FROM business_area_category"
            cursor.execute(sql)
            rows = cursor.fetchall()

        return [row[0] for row in rows] if rows else None

    except Exception as e:
        print(f"목록 조회 오류: {e}")
        return None
