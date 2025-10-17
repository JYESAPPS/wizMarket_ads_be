# app/db/dbctx.py
from contextlib import contextmanager
import pymysql
from pymysql.cursors import DictCursor
from app.db.connect import get_re_db_connection, close_cursor, close_connection, commit, rollback

@contextmanager
def re_db_dict():
    conn = get_re_db_connection()
    cur = None
    try:
        cur = conn.cursor(DictCursor)
        yield conn, cur
        commit(conn)
    except Exception:
        rollback(conn)
        raise
    finally:
        if cur: close_cursor(cur)
        if conn: close_connection(conn)
