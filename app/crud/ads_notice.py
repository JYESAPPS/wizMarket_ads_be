from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
from app.schemas.ads_notice import AdsNotice
from typing import List, Optional
import pymysql
import logging

logger = logging.getLogger(__name__)

def get_notice(include_hidden: bool = False):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        where = "" if include_hidden else "WHERE NOTICE_POST = 'Y'"
        select_query = f"""
            SELECT 
                NOTICE_NO, NOTICE_POST, NOTICE_TYPE, NOTICE_TITLE, NOTICE_CONTENT,
                NOTICE_FILE, NOTICE_IMAGES, VIEWS, CREATED_AT, UPDATED_AT
            FROM notice
            {where}
            ORDER BY CREATED_AT DESC;
        """
        cursor.execute(select_query)
        rows = cursor.fetchall()

        return [
            AdsNotice(
                notice_no=row["NOTICE_NO"],
                notice_post=row["NOTICE_POST"],
                notice_type=row["NOTICE_TYPE"],
                notice_title=row["NOTICE_TITLE"],
                notice_content=row["NOTICE_CONTENT"],
                notice_file=row["NOTICE_FILE"],
                notice_images=row["NOTICE_IMAGES"],
                views=row["VIEWS"],
                created_at=row["CREATED_AT"],
                updated_at=row["UPDATED_AT"],
            ) for row in rows
        ]

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
    finally:
        if cursor:
            cursor.close()

def create_notice(notice_post: str, notice_type: str, notice_title: str, notice_content: str, notice_file: Optional[str] = None, notice_images_json: str = "[]"):
    connection = get_re_db_connection()
    cursor = None

    try:
        cursor = connection.cursor()

        insert_query = """
            INSERT INTO NOTICE (NOTICE_POST, NOTICE_TYPE, NOTICE_TITLE, NOTICE_CONTENT, NOTICE_FILE, NOTICE_IMAGES)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (notice_post or "Y", notice_type, notice_title, notice_content, notice_file, notice_images_json or "[]"))
        notice_id = cursor.lastrowid # 신규 공지사항 ID 가져오기
        commit(connection)  # 커스텀 commit 사용

        return notice_id

    except pymysql.MySQLError as e:
        rollback(connection)  # 커스텀 rollback 사용
        print(f"Database error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)

def update_notice_set_file(notice_no, path: str):
    connection = get_re_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                UPDATE NOTICE
                SET NOTICE_FILE=%s, UPDATED_AT=NOW()
                WHERE NOTICE_NO=%s
            """
            cursor.execute(sql, (path, notice_no))
        commit(connection)
    finally:
        close_connection(connection)

def update_notice_clear_file(notice_no):
    connection = get_re_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                UPDATE NOTICE
                SET NOTICE_FILE=NULL, UPDATED_AT=NOW()
                WHERE NOTICE_NO=%s
            """
            cursor.execute(sql, (notice_no,))
        commit(connection)
    finally:
        close_connection(connection)

def update_notice(notice_no, notice_post, notice_type, notice_title, notice_content, notice_file):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor()

        update_query = """
            UPDATE NOTICE
            SET NOTICE_POST = %s,
                NOTICE_TYPE = %s,
                NOTICE_TITLE = %s,
                NOTICE_CONTENT = %s,
                UPDATED_AT = NOW()
            WHERE NOTICE_NO = %s
        """

        cursor.execute(update_query, (notice_post or "Y", notice_type, notice_title, notice_content, notice_no))
        commit(connection)  # 커스텀 commit 사용

    except pymysql.MySQLError as e:
        rollback(connection)  # 커스텀 rollback 사용
        print(f"Database error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)

def delete_notice(notice_no: int):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor()

        delete_query = """
            DELETE FROM NOTICE WHERE NOTICE_NO = %s
        """
        
        cursor.execute(delete_query, (notice_no,))
        commit(connection)  # 커스텀 commit 사용

    except pymysql.MySQLError as e:
        rollback(connection)  # 커스텀 rollback 사용
        print(f"Database error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)


def get_notice_read(user_id):
    try:
        user_id = int(user_id)
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            # 안 읽은 공지사항 목록 가져오기 (읽음 기록 없는 공지)
            cursor.execute("""
                SELECT N.notice_no, N.notice_title, N.notice_content
                FROM notice N
                WHERE N.notice_no NOT IN (
                    SELECT notice_no FROM notice_read WHERE user_id = %s
                )
                ORDER BY N.created_at DESC
            """, (user_id,))
            unread = cursor.fetchall()

        # 리스트로 반환
        result = [
            {
                "notice_no": row[0],
                "notice_title": row[1],
                "notice_content": row[2]
            }
            for row in unread
        ]
        return {"success": True, "unread_notices": result, "count": len(result)}

    except Exception as e:
        print(f"공지 읽음 여부 조회 오류: {e}")
        return {"success": False, "message": "조회 중 오류 발생"}


def insert_notice_read(user_id: str, notice_no: int):
    connection = get_re_db_connection()
    try:
        with connection.cursor() as cursor:
            # 1) 공지 노출 여부 확인
            cursor.execute("SELECT notice_post FROM NOTICE WHERE notice_no = %s", (notice_no,))
            row = cursor.fetchone()
            if not row:
                return False # 공지 없음
            if row[0] != 'Y':
                return True   # 숨김 공지는 기록하지 않음(배지 영향 없음)

            # 2) 중복/경쟁조건 방지: UPSERT
            cursor.execute("""
                INSERT INTO NOTICE_READ (user_id, notice_no, read_at)
                VALUES (%s, %s, NOW())
                ON DUPLICATE KEY UPDATE read_at = NOW()
            """, (user_id, notice_no))

        connection.commit()
        return True
    except Exception as e:
        try:
            connection.rollback()
        except:
            pass
        print(f"insert_notice_read error: {e}")
        return False
    finally:
        try:
            connection.close()
        except:
            pass
    # with connection.cursor() as cursor:
    #     # 중복 방지: 이미 존재하면 insert 안 함
    #     cursor.execute("""
    #         SELECT COUNT(*) FROM NOTICE_READ
    #         WHERE user_id = %s AND notice_no = %s
    #     """, (user_id, notice_no))
    #     count = cursor.fetchone()[0]

    #     if count == 0:
    #         cursor.execute("""
    #             INSERT INTO NOTICE_READ (user_id, notice_no, read_at)
    #             VALUES (%s, %s, NOW())
    #         """, (user_id, notice_no))
    #         connection.commit()



def notice_views(notice_no: int) -> int:
    conn = get_re_db_connection()
    cur = conn.cursor()
    try:
        cur = conn.cursor()
        sql = "UPDATE notice SET views = views + 1 WHERE notice_no = %s"
        cur.execute(sql, (notice_no,))
        affected = cur.rowcount
        commit(conn)  # 없다면 conn.commit()
        return affected
    except Exception:
        rollback(conn)  # 없다면 conn.rollback()
        raise
    finally:
        if cur:
            close_cursor(cur)  # 없다면 cur.close()
        close_connection(conn)  # 없다면 conn.close()