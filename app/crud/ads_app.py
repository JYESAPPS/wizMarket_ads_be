from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
import random
import pymysql
from datetime import datetime, timedelta


# 선택 된 스타일 값에서 랜덤 이미지 뽑기
def select_random_image(style):
    try:
        connection = get_re_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:  # ✅ DictCursor 사용
            cursor.execute("SELECT PROMPT FROM thumbnail WHERE design_id = %s", (style,))
            rows = cursor.fetchall()

        if not rows:
            return None

        return random.choice(rows)["PROMPT"]  # ✅ 딕셔너리 접근

    except Exception as e:
        print(f"랜덤 이미지 선택 오류: {e}")
        return None
    
# 모든 이미지 리스트 가져오기
def get_style_image(category_id: int):
    try:
        connection = get_re_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1차 시도: 주어진 category_id로 조회
            cursor.execute("""
                SELECT 
                    t.design_id, 
                    t.prompt, 
                    tp.image_path AS path
                FROM thumbnail t
                JOIN thumbnail_path tp ON t.thumbnail_id = tp.thumbnail_id
                WHERE t.category_id = %s
            """, (category_id,))
            rows = cursor.fetchall()

            # 2차 시도: 기본 category_id (249) fallback
            if not rows:
                print(f"[WARN] category_id={category_id}에 해당하는 데이터 없음. 기본 category_id=249로 fallback.")
                cursor.execute("""
                    SELECT 
                        t.design_id, 
                        t.prompt, 
                        tp.image_path AS path
                    FROM thumbnail t
                    JOIN thumbnail_path tp ON t.thumbnail_id = tp.thumbnail_id
                    WHERE t.category_id = 249
                """)
                rows = cursor.fetchall()

        return rows if rows else None

    except Exception as e:
        print(f"썸네일 이미지 조회 오류: {e}")
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
    image_path,
    upload_type
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
            user_id, age, alert_check, start_date, end_date, repeat_time, style, title, channel, upload_time, image_path, upload_type
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                image_path,
                upload_type
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
            cursor.execute("SELECT nickname, gender, birth_year, profile_image FROM USER_INFO WHERE user_id = %s", (user_id,))
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
            cursor.execute("SELECT start_date, end_date, age, style, title, channel, upload_type, image_path FROM user_record WHERE user_id = %s and upload_check = 1", (user_id,))
            rows = cursor.fetchall()

        if not rows:
            return None

        return rows  # ✅ 딕셔너리 접근

    except Exception as e:
        print(f"회원 기록 정보 오류: {e}")
        return None
    
def get_user_record_this_month(user_id):

    try:
        today = datetime.today()
        month_start = today.replace(day=1)
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_end = next_month - timedelta(days=1)

        connection = get_re_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT start_date, end_date, repeat_time, age, style, title, channel, image_path
                FROM user_record
                WHERE user_id = %s
                AND end_date >= %s
                AND start_date <= %s
            """
            cursor.execute(query, (user_id, month_start.strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d")))
            rows = cursor.fetchall()

        if not rows:
            return None

        return rows

    except Exception as e:
        print(f"이번달 회원 기록 정보 오류: {e}")
        return None
    

# 헤더 메인페이지 유저 프로필 가져오기
def get_user_profile(user_id):
    try:
        connection = get_re_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:  # ✅ DictCursor 사용
            cursor.execute("SELECT profile_image FROM USER_INFO WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()

        if not row:
            return None

        return row  # ✅ 딕셔너리 접근

    except Exception as e:
        print(f"회원 정보 오류: {e}")
        return None

# 유저 정보 추가
def insert_user_info(user_id, request):
    nickname = request.nickname
    birth_year = request.birth_year
    gender = request.gender
    phone = request.phone

    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO USER_INFO (user_id, nickname, birth_year, gender, phone)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, nickname, birth_year, gender, phone))
        connection.commit()
        return True  # ✅ 성공 시 True 반환

    except Exception as e:
        print(f"회원 정보 삽입 오류: {e}")
        return False

# 유저 정보 수정
def update_user_info(user_id, request):
    nickname = request.nickname
    birth_year = request.birth_year
    gender = request.gender
    phone = request.phone

    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = """
                UPDATE USER_INFO
                SET nickname = %s,
                    birth_year = %s,
                    gender = %s,
                    phone = %s
                WHERE user_id = %s
            """
            cursor.execute(sql, (nickname, birth_year, gender, phone, user_id))
        connection.commit()
        return True  # ✅ 성공 시 True 반환

    except Exception as e:
        print(f"회원 정보 업데이트 오류: {e}")
        return False


# 자동 업로드 포스팅 정보 가져오기
def get_user_recent_reco(request):
    user_id = int(request.user_id)
    upload_type = request.type
    try:
        connection = get_re_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT user_record_id, start_date, end_date, age, style, title, channel, image_path, repeat_time, upload_time, alert_check
                FROM user_record
                WHERE user_id = %s 
                    AND upload_type = %s
                    AND upload_check = 1
                    AND end_date >= CURDATE()  -- 오늘 포함 이후만
                ORDER BY start_date DESC
            """, (user_id, upload_type))
            rows = cursor.fetchall()

        if not rows:
            return None

        return rows

    except Exception as e:
        print(f"회원 기록 정보 오류: {e}")
        return None

# 유저 기록 게시물 1개 업데이트
def update_user_reco(user_id, request):
    
    alert_check = 1 if request.alert_check else 0  # ✅ 변환
    start_date = request.start_date
    end_date = request.end_date
    repeat_time = request.repeat_time
    user_record_id = request.user_record_id

    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = """
                UPDATE USER_RECORD
                SET alert_check = %s,
                    start_date = %s,
                    end_date = %s,
                    repeat_time = %s
                WHERE user_id = %s
                AND user_record_id = %s
            """
            cursor.execute(sql, (alert_check, start_date, end_date, repeat_time, user_id, user_record_id))
        connection.commit()
        return True

    except Exception as e:
        print(f"회원 기록 정보 업데이트 오류: {e}")
        return False
    

# 유저 기록 게시물 1개 삭제 처리
def delete_user_reco(user_id, request):
    
    user_record_id = request.user_record_id

    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = """
                UPDATE USER_RECORD
                SET upload_check = 0
                WHERE user_id = %s
                AND user_record_id = %s
            """
            cursor.execute(sql, (user_id, user_record_id))
        connection.commit()
        return True

    except Exception as e:
        print(f"회원 기록 정보 삭제 오류: {e}")
        return False

