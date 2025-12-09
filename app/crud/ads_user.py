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
    


# 본인인증 후 user 이름, 번호 업데이트
def update_user_name_phone(user_id, name, phone):
    
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO USER_INFO (user_id, name, phone)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (user_id, name, phone))
        connection.commit()
        return True  # ✅ 성공 시 True 반환

    except Exception as e:
        print(f"회원 정보 삽입 오류: {e}")
        return False




def stop_user(user_id: str, reason: str) -> bool:

    conn = get_re_db_connection()
    cur = conn.cursor()

    try:
        conn.autocommit(False)
        user_sql = '''
            UPDATE user
            SET status = 'stop', stop_reason = %s, is_active = 0, updated_at = NOW()
            WHERE user_id = %s;
        '''
        cur.execute(user_sql, (reason, user_id))
        conn.commit()
        return True
    
    except Exception as e:
        conn.rollback()
        logger.exception(f"[crud_logout_user] {e}")
        return False


def unstop_user(user_id: str) -> bool:

    conn = get_re_db_connection()
    cur = conn.cursor()

    try:
        conn.autocommit(False)
        user_sql = '''
            UPDATE user
            SET status = 'active', stop_reason = null, is_active = 1, updated_at = NOW()
            WHERE user_id = %s;
        '''
        cur.execute(user_sql, (user_id))
        conn.commit()
        return True
    
    except Exception as e:
        conn.rollback()
        logger.exception(f"[crud_logout_user] {e}")
        return False


# 매장 조회 : 가게명 LIKE, 도로명 == 
# USER TB와 LEFT JOIN해서 이미 가입된 매장 판별
def get_store(store_name, road_name):
    ls_conn = get_db_connection()  # LOCAL_STORE (test 컴포넌트)
    ls_cur = ls_conn.cursor(pymysql.cursors.DictCursor)

    user_conn = None
    user_cur = None

    try:
        # ─ 1) LOCAL_STORE 조회 ─────────────────────────────
        sn = (store_name or "").strip()
        rn = (road_name or "").strip()

        def to_like(s: str) -> str:
            s = s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            return f"%{s}%"

        where, params = [], []
        if sn:
            where.append("STORE_NAME LIKE %s")
            params.append(to_like(sn))
        if rn:
            where.append("ROAD_NAME_ADDRESS = %s")
            params.append(rn)

        if not where:
            return []

        select_query = f"""
            SELECT
                STORE_BUSINESS_NUMBER,
                STORE_NAME,
                ROAD_NAME_ADDRESS,
                FLOOR_INFO,
                LARGE_CATEGORY_NAME,
                MEDIUM_CATEGORY_NAME,
                SMALL_CATEGORY_NAME
            FROM LOCAL_STORE
            WHERE {" AND ".join(where)}
            ORDER BY STORE_NAME ASC
        """
        ls_cur.execute(select_query, tuple(params))
        rows = ls_cur.fetchall()

        if not rows:
            return []

        # ─ 2) store_business_number 모아서 USER 쿼리 ────────
        #   (LEFT JOIN 처럼, 없는 매장은 그대로 user_* None 으로 남김)
        bs_list = list({
            r["STORE_BUSINESS_NUMBER"]
            for r in rows
            if r.get("STORE_BUSINESS_NUMBER")
        })

        if not bs_list:
            return rows

        user_conn = get_re_db_connection()  # wiz_report 스키마
        user_cur = user_conn.cursor(pymysql.cursors.DictCursor)

        placeholders = ",".join(["%s"] * len(bs_list))
        user_query = f"""
            SELECT user_id, store_business_number
            FROM USER
            WHERE store_business_number IN ({placeholders})
        """
        user_cur.execute(user_query, bs_list)
        user_rows = user_cur.fetchall()

        # store_business_number -> user 정보 매핑
        user_map = {}
        for u in user_rows:
            sbn = u["store_business_number"]
            # 한 매장에 여러 user가 있을 수 있으면 여기서 로직 조정(첫번째만 사용 등)
            if sbn not in user_map:
                user_map[sbn] = u

        # ─ 3) LOCAL_STORE row에 user 정보 merge ───────────
        for r in rows:
            sbn = r["STORE_BUSINESS_NUMBER"]
            u = user_map.get(sbn)

            if u:
                r["user_id"] = u["user_id"]
            else:
                # LEFT JOIN에서 NULL 나오는 것과 동일한 효과
                r["user_id"] = None

        return rows

    finally:
        if ls_cur:
            ls_cur.close()
        if ls_conn:
            ls_conn.close()
        if user_cur:
            user_cur.close()
        if user_conn:
            user_conn.close()



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
        logger.error(f"insert_business_verification error: user_id({user_id}) {e}")
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