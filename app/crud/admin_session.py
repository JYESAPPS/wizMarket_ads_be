# app/crud/admin_session.py
from app.db.dbctx import re_db_dict
from app.core.security import hash_token  # ✅ 변경: hash_password -> hash_token

def insert_session(user_id: int, session_id: str, refresh_token_raw: str,
                   ip: str|None, ua: str|None, idle_minutes: int = 30, absolute_hours: int = 12):
    with re_db_dict() as (conn, cur):
        cur.execute("""
            INSERT INTO admin_session
                (user_id, session_id, refresh_token_hash, ip_address, user_agent,
                 idle_expires_at, absolute_expires_at)
            VALUES
                (%s, %s, %s, %s, %s,
                 DATE_ADD(UTC_TIMESTAMP(), INTERVAL %s MINUTE),
                 DATE_ADD(UTC_TIMESTAMP(), INTERVAL %s HOUR))
        """, (
            user_id,
            session_id,
            hash_token(refresh_token_raw),  # ✅ 여기!
            ip, ua, idle_minutes, absolute_hours
        ))
