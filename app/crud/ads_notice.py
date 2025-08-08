from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
from app.schemas.ads_notice import AdsNotice
from typing import List
import pymysql
import logging

logger = logging.getLogger(__name__)

def get_notice() -> List[AdsNotice]:
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        if connection.open:
            select_query = """
                SELECT 
                    NOTICE_NO, 
                    NOTICE_TITLE,
                    NOTICE_CONTENT,
                    CREATED_AT
                FROM NOTICE;
            """
            cursor.execute(select_query)
            rows = cursor.fetchall()

            if not rows:
                return []

            return [
                AdsNotice(
                    notice_no=row["NOTICE_NO"],
                    notice_title=row["NOTICE_TITLE"],
                    notice_content=row["NOTICE_CONTENT"],
                    created_at=row["CREATED_AT"],
                ) for row in rows
            ]

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
    except Exception as e:
        logger.error(f"Unexpected Error in get_notice: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류가 발생했습니다.")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def create_notice(notice_title: str, notice_content: str):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor()

        insert_query = """
            INSERT INTO NOTICE (NOTICE_TITLE, NOTICE_CONTENT)
            VALUES (%s, %s)
        """

        cursor.execute(insert_query, (notice_title, notice_content))
        commit(connection)  # 커스텀 commit 사용

    except pymysql.MySQLError as e:
        rollback(connection)  # 커스텀 rollback 사용
        print(f"Database error: {e}")
        raise

    finally:
        close_cursor(cursor)
        close_connection(connection)

def update_notice(notice_no: int, notice_title: str, notice_content: str):
    connection = get_re_db_connection()

    try:
        cursor = connection.cursor()

        update_query = """
            UPDATE NOTICE
            SET NOTICE_TITLE = %s,
                NOTICE_CONTENT = %s
            WHERE NOTICE_NO = %s
        """

        cursor.execute(update_query, (notice_title, notice_content, notice_no))
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
                FROM NOTICE N
                WHERE N.notice_no NOT IN (
                    SELECT notice_no FROM NOTICE_READ WHERE user_id = %s
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
    with connection.cursor() as cursor:
        # 중복 방지: 이미 존재하면 insert 안 함
        cursor.execute("""
            SELECT COUNT(*) FROM NOTICE_READ
            WHERE user_id = %s AND notice_no = %s
        """, (user_id, notice_no))
        count = cursor.fetchone()[0]

        if count == 0:
            cursor.execute("""
                INSERT INTO NOTICE_READ (user_id, notice_no, read_at)
                VALUES (%s, %s, NOW())
            """, (user_id, notice_no))
            connection.commit()