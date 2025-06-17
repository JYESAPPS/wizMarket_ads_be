from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
import random
import pymysql

def select_random_image(style):
    try:
        connection = get_re_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:  # ✅ DictCursor 사용
            cursor.execute("SELECT PROMPT FROM IMAGE WHERE design_id = %s", (style,))
            rows = cursor.fetchall()

        if not rows:
            return None

        return random.choice(rows)["PROMPT"]  # ✅ 딕셔너리 접근

    except Exception as e:
        print(f"랜덤 이미지 선택 오류: {e}")
        return None
    

def get_style_image():
    try:
        connection = get_re_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:  # ✅ DictCursor 사용
            cursor.execute("SELECT DESIGN_ID, PROMPT, PATH FROM IMAGE")
            rows = cursor.fetchall()

        if not rows:
            return None

        return rows

    except Exception as e:
        print(f"랜덤 이미지 선택 오류: {e}")
        return None