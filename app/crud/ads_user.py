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