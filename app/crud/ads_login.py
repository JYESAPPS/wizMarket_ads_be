from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)

def ads_login(user_id: str, password: str):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM USER WHERE user_id = %s AND password = %s"
            cursor.execute(sql, (user_id, password))
            user = cursor.fetchone()
        return user
    except Exception as e:
        print(f"로그인 조회 오류: {e}")
        return None
