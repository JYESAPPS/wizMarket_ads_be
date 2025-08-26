from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
from typing import List
import pymysql
import logging

logger = logging.getLogger(__name__)


def insert_business_verification(
    user_id,
    original_filename,
    saved_filename,
    saved_path,    
    content_type,
    size_bytes
) -> int:
    conn = None
    cursor = None
    try:
        conn = get_re_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
        INSERT INTO business_verification
            (user_id, original_filename, saved_filename, saved_path, content_type, size_bytes, status, created_at)
        VALUES
            (%s, %s, %s, %s, %s, %s, 'pending', NOW())
        """
        cursor.execute(sql, (
            user_id,
            original_filename,
            saved_filename,
            saved_path,          # 가능하면 상대경로를 권장
            content_type,
            size_bytes,
        ))

        new_id = cursor.lastrowid
        commit(conn)
        return new_id

    except Exception as e:
        if conn:
            rollback(conn)
        logger.error(f"insert_business_verification error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if cursor:
            close_cursor(cursor)
        if conn:
            close_connection(conn)
