from typing import Optional
from app.db.dbctx import re_db_dict
from app.core.security import hash_password

def get_user_by_username(username: str) -> Optional[dict]:
    with re_db_dict() as (conn, cur):
        cur.execute("SELECT * FROM admin_user WHERE username=%s", (username,))
        return cur.fetchone()

def get_user_by_id(user_id: int) -> Optional[dict]:
    with re_db_dict() as (conn, cur):
        cur.execute("SELECT * FROM admin_user WHERE id=%s", (user_id,))
        return cur.fetchone()

def create_admin_user(username: str, email: str|None, role: str, temp_password: str) -> int:
    with re_db_dict() as (conn, cur):
        cur.execute("""
            INSERT INTO admin_user (username, admin_uid, email, password_hash, role, must_change_password, is_active)
            VALUES (%s,%s,%s,%s,%s,1,1)
        """, (username, email, hash_password(temp_password), role))
        conn.commit()
        return cur.lastrowid

def set_password(user_id: int, new_password: str):
    with re_db_dict() as (conn, cur):
        cur.execute("""
            UPDATE admin_user
               SET password_hash=%s, must_change_password=0
             WHERE id=%s
        """, (hash_password(new_password), user_id))

def touch_last_login(user_id: int):
    with re_db_dict() as (conn, cur):
        cur.execute("UPDATE admin_user SET last_login_at=NOW() WHERE id=%s", (user_id,))


def get_admin_list():
    with re_db_dict() as (conn, cur):
        cur.execute("""
            SELECT id, username, email, admin_uid, role, is_active, must_change_password, created_at, last_login_at, phone, department, position
              FROM admin_user
             ORDER BY created_at DESC
        """)
        return cur.fetchall()

def delete_admin(admin_id: int):
    with re_db_dict() as (conn, cur):
        cur.execute("DELETE FROM admin_user WHERE id=%s", (admin_id,))
        conn.commit() 
    return cur.rowcount

def get_admin_detail(admin_id: int) -> Optional[dict]:
    with re_db_dict() as (conn, cur):
        cur.execute("""
            SELECT id, username, email, admin_uid, phone, department, position,
                   role, is_active, visit_count, created_at, last_login_at
              FROM admin_user
             WHERE id=%s
        """, (admin_id,))
        return cur.fetchone()

