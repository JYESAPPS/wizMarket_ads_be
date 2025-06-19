from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
import random
import pymysql

# 선택 된 스타일 값에서 랜덤 이미지 뽑기
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
    
# 모든 이미지 리스트 가져오기
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
    

def insert_upload_record(
    user_id,
    age,
    alert_check,
    data_range,
    repeat,
    style,
    title,
    channel,
    upload_time,
    image_path
):
    if not upload_time:
        upload_time = "00:00"

    age = int(age)
    channel = int(channel)
    style = int(style)
    start_date = data_range[0]
    end_date = data_range[1]

    connection = get_re_db_connection()
    cursor = connection.cursor()

    try:
        insert_query = """
        INSERT INTO user_record (
            user_id, age, alert_check, start_date, end_date, repeat_time, style, title, channel, upload_time, image_path
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            insert_query,
            (
                user_id,
                age,
                alert_check,
                start_date,
                end_date,
                repeat,
                style,
                title,
                channel,
                upload_time,
                image_path
            )
        )
        commit(connection)
        return True
    except Exception as e:
        print("DB 저장 중 오류:", e)
        rollback(connection)
        return False
    finally:
        close_cursor(cursor)
        close_connection(connection)

def get_user_info(user_id):
    try:
        connection = get_re_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:  # ✅ DictCursor 사용
            cursor.execute("SELECT nickname, gender, birth_year FROM USER_INFO WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()

        if not row:
            return None

        return row  # ✅ 딕셔너리 접근

    except Exception as e:
        print(f"회원 정보 오류: {e}")
        return None

def get_user_record(user_id):
    try:
        connection = get_re_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:  # ✅ DictCursor 사용
            cursor.execute("SELECT age, style, title, channel, image_path FROM user_record WHERE user_id = %s", (user_id,))
            rows = cursor.fetchall()

        if not rows:
            return None

        return rows  # ✅ 딕셔너리 접근

    except Exception as e:
        print(f"회원 기록 정보 오류: {e}")
        return None