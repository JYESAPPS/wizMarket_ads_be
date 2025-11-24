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

def create_admin_user(data) -> int:
    with re_db_dict() as (conn, cur):

        is_active = data.is_active
        role = data.role
        name = data.name
        admin_id = data.admin_id
        phone = data.phone
        temp_password = data.temp_password
        email = data.email
        department = data.department
        position = data.position


        cur.execute("""
            INSERT INTO admin_user (username, name, email, password_hash, role, must_change_password, is_active, phone, department, position)
            VALUES (%s, %s, %s, %s, %s, 1, %s, %s, %s, %s)
        """, (admin_id, name, email, hash_password(temp_password), role, is_active, phone, department, position))
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
            SELECT id, username, name, email, phone, role, is_active, created_at, last_login_at
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
            SELECT id, username, name, email, phone, department, position,
                   role, is_active, visit_count, created_at, last_login_at
              FROM admin_user
             WHERE id=%s
        """, (admin_id,))
        return cur.fetchone()


def update_admin_info(admin_id, request):
    with re_db_dict() as (conn, cur):

        is_active = request.is_active
        role = request.role
        name = request.name
        phone = request.phone
        email = request.email
        department = request.department
        position = request.position

        cur.execute("""
            UPDATE ADMIN_USER
            SET
                is_active = %s,
                role = %s,
                name = %s,
                phone = %s,
                email = %s,
                department = %s,
                position = %s
            WHERE id=%s
        """, (is_active, role, name, phone, email, department, position, admin_id,))
        conn.commit() 
    return cur.rowcount



