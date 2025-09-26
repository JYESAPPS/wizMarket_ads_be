from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
import random
import logging
import pymysql
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from fastapi import HTTPException

logger = logging.getLogger(__name__)
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
            cursor.execute("SELECT nickname, phone, gender, birth_year, profile_image, register_tag, custom_menu, insta_account, kakao_account, blog_account, band_account, x_account, address FROM USER_INFO WHERE user_id = %s", (user_id,))
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
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:  # ✅ DictCursor 사용 # and upload_check = 1 
            cursor.execute("SELECT start_date, end_date, age, style, title, channel, upload_type, image_path FROM user_record WHERE user_id = %s", (user_id,))
            rows = cursor.fetchall()

        if not rows:
            return None

        return rows  # ✅ 딕셔너리 접근

    except Exception as e:
        print(f"회원 기록 정보 오류: {e}")
        return None
    
def get_user_record_this_month(user_id):

    try:
        # today = datetime.today()
        # month_start = today.replace(day=1)
        # next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        # month_end = next_month - timedelta(days=1)

        connection = get_re_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT start_date, end_date, repeat_time, age, style, title, channel, image_path
                FROM user_record
                WHERE user_id = %s
            """
            cursor.execute(query, (user_id))
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
    register_tag = request.register_tag

    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO USER_INFO (user_id, nickname, birth_year, gender, phone, register_tag)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, nickname, birth_year, gender, phone, register_tag))
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
    register_tag = request.register_tag
    insta_account = request.insta_account
    kakao_account = request.kakao_account
    blog_account = request.blog_account
    band_account = request.band_account
    x_account = request.x_account
    updated_at = datetime.now()

    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = """
                UPDATE USER_INFO
                SET nickname = %s,
                    birth_year = %s,
                    gender = %s,
                    phone = %s,
                    register_tag = %s,
                    insta_account = %s,
                    kakao_account = %s,
                    blog_account = %s,
                    band_account = %s,
                    x_account = %s,
                    updated_at = %s
                WHERE user_id = %s
            """
            cursor.execute(sql, (nickname, birth_year, gender, phone, register_tag, insta_account, kakao_account, blog_account, band_account, x_account, updated_at, user_id))

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


def get_store_info(store_business_number):
    try:
        connection = get_re_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT STORE_NAME, ROAD_NAME
                FROM REPORT
                WHERE STORE_BUSINESS_NUMBER = %s
            """, (store_business_number,))  # ✅ 쉼표 추가로 튜플로 만들어야 함
            row = cursor.fetchone()

        if not row:
            return None

        return row

    except Exception as e:
        print(f"매장 정보 오류: {e}")
        return None

# 유저 정보가 존재하는지 확인
def user_info_exists_by_sbn(store_business_number: str) -> bool:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM wiz_report.`user` u
                JOIN wiz_report.user_info ui ON ui.user_id = u.user_id
                WHERE u.store_business_number = %s
                LIMIT 1
                """,
                (store_business_number,)
            )
            return cur.fetchone() is not None
    finally:
        conn.close()

def update_user_custom_menu(menu: str, store_business_number: str) -> bool:
    connection = get_db_connection()
    try:
        with connection.cursor() as cur:
            cur.execute(
                """
                UPDATE wiz_report.user_info ui
                JOIN wiz_report.`user` u ON ui.user_id = u.user_id
                SET ui.custom_menu = %s,
                    ui.updated_at = NOW()
                WHERE u.store_business_number = %s
                """,
                (menu, store_business_number)
            )
            affected = cur.rowcount
        connection.commit()
        # print(f"유저 커스텀 메뉴 업데이트 성공: {affected}개")
        return affected
    except Exception as e:
        connection.rollback()
        print(f"유저 커스텀 메뉴 업데이트 오류: {e}")
        return False
    finally:
        cur.close()
        connection.close()

def insert_user_custom_menu(menu: str, store_business_number: str) -> int:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("USE `wiz_report`")
            cur.execute("SELECT DATABASE(), @@hostname, CURRENT_USER(), @@read_only")
            print("[DBCTX]", cur.fetchone())
            cur.execute(
                """
                INSERT INTO user_info (user_id, custom_menu)
                SELECT u.user_id, %s
                FROM user u
                LEFT JOIN user_info ui ON ui.user_id = u.user_id
                WHERE u.store_business_number = %s;
                """,
                (menu, store_business_number)
            )
            inserted = cur.rowcount
        conn.commit()
        # print(f"유저 커스텀 메뉴 삽입 성공: {inserted}개")
        return inserted
    except Exception:
        conn.rollback()
        print("유저 커스텀 메뉴 삽입 오류")
        raise
    finally:
        conn.close()


def update_register_tag(user_id: int, register_tag: str) -> bool:
    conn = get_re_db_connection()  # PRIMARY DB
    try:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO user_info (user_id, register_tag, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    register_tag = VALUES(register_tag),
                    updated_at = VALUES(updated_at)
            """
            cur.execute(sql, (user_id, register_tag))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()





def update_user_status_only(user_id: int, status: str) -> bool:
    """
    user.status 만 갱신
    """
    conn = get_re_db_connection()
    cur = conn.cursor()
    try:
        conn.autocommit(False)
        sql = """
            UPDATE user
               SET status = %s,
                   updated_at = NOW()
             WHERE user_id = %s
        """
        cur.execute(sql, (status, user_id))
        if cur.rowcount == 0:
            conn.rollback()
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
        conn.commit()
        return True
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.exception(f"[crud_update_user_status_only] {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류")
    finally:
        cur.close()
        conn.close()



CHANNEL_TO_COLUMN = {
    "인스타그램": "insta_account",
    "블로그": "blog_account",
    "X": "x_account",
    "네이버밴드": "band_account",
    "카카오": "kakao_account",
    "카카오톡": "kakao_account",
    # "페이스북": 없음 → 스킵(테이블에 컬럼이 없음)
    "페이스북": None,
}

def _map_accounts_to_columns(accounts: List[Dict[str, str]]) -> Dict[str, str]:
    """
    전달된 accounts를 user_info의 컬럼 딕셔너리로 변환.
    - 정의된 컬럼만 포함
    - '페이스북'은 컬럼이 없으므로 무시
    - 마지막 값이 우선(중복 채널 입력 방지)
    """
    colmap: Dict[str, str] = {}
    for item in accounts:
        ch = item.get("channel", "").strip()
        acc = item.get("account", "").strip()
        col = CHANNEL_TO_COLUMN.get(ch)
        if col:
            colmap[col] = acc
        elif col is None and ch:  # 매핑 없음(예: 페이스북)
            logger.warning(f"[user_info] Unsupported channel, skipped: {ch}")
    return colmap


def upsert_user_info_accounts(user_id: int, accounts: List[Dict[str, str]]) -> bool:
    """
    user_info 테이블에 필요한 계정 컬럼만 동적 UPSERT.
    - UNIQUE KEY(user_id) 가정.
    - 제공되지 않은 컬럼은 건드리지 않음(= NULL로 덮어쓰지 않음).
    - INSERT 시 제공한 컬럼만 넣고, DUPLICATE 시 제공한 컬럼만 UPDATE.
    """
    colmap = _map_accounts_to_columns(accounts)
    if not colmap:
        return True  # 업데이트할 계정 없음

    conn = get_re_db_connection()
    cur = conn.cursor()
    try:
        conn.autocommit(False)

        # 동적 INSERT ... ON DUPLICATE KEY UPDATE
        cols: List[str] = ["user_id"] + list(colmap.keys())
        placeholders = ", ".join(["%s"] * len(cols))
        insert_cols = ", ".join(cols)
        update_clause = ", ".join([f"{c}=VALUES({c})" for c in colmap.keys()] + ["updated_at=NOW()"])

        sql = f"""
            INSERT INTO user_info ({insert_cols})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_clause}
        """

        params: Tuple = tuple([user_id] + list(colmap.values()))
        cur.execute(sql, params)

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        logger.exception(f"[crud_upsert_user_info_accounts] {e}")
        raise HTTPException(status_code=500, detail="user_info 저장 실패")
    finally:
        cur.close()
        conn.close()


def delete_user(user_id: str) -> bool:

    conn = get_re_db_connection()
    cur = conn.cursor()
    try:
        conn.autocommit(False)

        # 1) user 삭제
        user_sql = '''
            UPDATE user
            SET status='deleted', is_active=0,
                access_token=NULL, refresh_token=NULL, 
                permission_confirmed=0, updated_at=NOW()
            WHERE user_id = %s;
        '''
        cur.execute(user_sql, (user_id,))
        # 2) user_device 삭제
        user_info_sql = '''
            UPDATE user_device
            SET is_active=0, device_token=NULL, last_seen=NOW(), updated_at=NOW()
            WHERE user_id = %s;
        '''
        cur.execute(user_info_sql, (user_id,))

        # 3) user_reserve 삭제
        user_reserve_sql = '''
            UPDATE user_reserve
            SET is_active=0, updated_at=NOW()
            WHERE user_id = %s;
        '''
        cur.execute(user_reserve_sql, (user_id,))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.exception(f"[crud_delete_user] {e}")
        return False




def upsert_user_info(user_id, request):
    # user_id가 str이어도 캐스팅만 해주면 됨
    uid = int(request.user_id)

    # 필요 필드만 꺼냄 (없으면 None)
    g = lambda k: getattr(request, k, None)
    nickname, phone, gender, birth_year = g("nickname"), g("phone"), g("gender"), g("birth_year")
    register_tag = g("register_tag")
    insta, kakao, blog, band, xacc = g("insta_account"), g("kakao_account"), g("blog_account"), g("band_account"), g("x_account")
    marketing_agree = g("marketing_agree")
    if marketing_agree in (None, "", " "):
        marketing_agree = 0

    verified = g("verified")
    if verified in (None, "", " "):
        verified = 0

    name = g("name")

    conn = get_re_db_connection()
    try:
        with conn.cursor() as cur:
            sql = """
            INSERT INTO wiz_report.USER_INFO (
              user_id, nickname, phone, gender, birth_year,
              profile_image, marketing_agree, created_at, updated_at,
              register_tag, custom_menu, insta_account, kakao_account,
              blog_account, band_account, x_account, verified, name, address
            )
            VALUES (
              %s, %s, %s, %s, %s,
              NULL, %s, NOW(), NULL,
              %s, NULL, %s, %s,
              %s, %s, %s, %s, %s,
              (SELECT ls.ROAD_NAME_ADDRESS
                 FROM test.local_store ls
                WHERE ls.STORE_BUSINESS_NUMBER = (
                      SELECT u.STORE_BUSINESS_NUMBER
                        FROM wiz_report.user u
                       WHERE u.user_id = %s
                       LIMIT 1
                )
                LIMIT 1
              )
            )
            ON DUPLICATE KEY UPDATE
              nickname        = VALUES(nickname),
              phone           = VALUES(phone),
              gender          = VALUES(gender),
              birth_year      = VALUES(birth_year),
              register_tag    = VALUES(register_tag),
              custom_menu     = VALUES(custom_menu),
              insta_account   = VALUES(insta_account),
              kakao_account   = VALUES(kakao_account),
              blog_account    = VALUES(blog_account),
              band_account    = VALUES(band_account),
              x_account       = VALUES(x_account),
              verified        = VALUES(verified),
              name            = VALUES(name),
              marketing_agree = VALUES(marketing_agree),
              updated_at      = NOW(),
              address         = COALESCE(NULLIF(address, ''), VALUES(address))
            """
            cur.execute(sql, (
                uid, nickname, phone, gender,
                int(birth_year) if birth_year not in (None, "", " ") else None,
                marketing_agree, register_tag,
                insta, kakao, blog, band, xacc, verified, name,
                uid  # 서브쿼리용
            ))
        conn.commit()
        return True, "upserted"
    except Exception as e:
        rollback(conn)
        print(f"[upsert_user_info] {e}")
        return False, "error"
    finally:
        close_connection(conn)