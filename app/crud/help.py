from typing import Optional, List, Dict, Any, Tuple
import pymysql
from app.db.connect import (  
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from app.schemas.help import HelpCreate, HelpOut, HelpStatusUpdate

# 목록
def list_help(status: Optional[str], limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    sql_base = """
        SELECT id, name, email, phone, category, title, content,
               attachment1, attachment2, attachment3,
               status, answer, answered_at,
               created_at, updated_at
        FROM help
    """

    # 동적 WHERE 절 구성
    where_clauses = []
    params: list[Any] = []

    if status:
        where_clauses.append("status = %s")
        params.append(status)

    if where_clauses:
        sql_base += " WHERE " + " AND ".join(where_clauses)

    sql_base += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    conn = get_re_db_connection()
    cur = None
    try:
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(sql_base, params)
        rows = cur.fetchall() or []
        return rows
    finally:
        close_cursor(cur)
        close_connection(conn)

# 상세
def get_help(help_id: int) -> Optional[Dict[str, Any]]:
    sql = """
        SELECT id, name, email, phone, category, title, content,
               attachment1, attachment2, attachment3,
               status, answer, answered_at,
               created_at, updated_at
          FROM help
         WHERE id = %s
         LIMIT 1
    """
    conn = get_re_db_connection()  # ← 통일
    cur = None
    try:
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(sql, (help_id,))
        row = cur.fetchone()
        return row
    finally:
        close_cursor(cur)
        close_connection(conn)

# 생성
def insert_help(
    *,
    payload: HelpCreate,
    attachments: Tuple[Optional[str], Optional[str], Optional[str]],
) -> Dict[str, Any]:
    sql_ins = """
        INSERT INTO help
            (name, email, phone, category, title, content,
             attachment1, attachment2, attachment3, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
    """
    sql_sel = """
        SELECT id, name, email, phone, category, title, content,
               attachment1, attachment2, attachment3,
               status, answer, answered_at,
               created_at, updated_at
        FROM help
        WHERE id = %s
        LIMIT 1
    """
    a1, a2, a3 = attachments
    conn = get_re_db_connection()  # ← 통일
    cur = None
    try:
        cur = conn.cursor()
        cur.execute(
            sql_ins,
            (
                payload.name,          # ← 컬럼 순서와 정확히 매칭
                payload.email,
                payload.phone,
                payload.category,
                payload.title,
                payload.content,
                a1, a2, a3
            ),
        )
        new_id = cur.lastrowid
        commit(conn)
        close_cursor(cur)

        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(sql_sel, (new_id,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError("inserted row not found")
        if row.get("phone") is None:
            row["phone"] = None
        return row
    except Exception:
        rollback(conn)
        raise
    finally:
        close_cursor(cur)
        close_connection(conn)

# 상태 변경
def update_help_status(help_id: int, status: str, answer: Optional[str] = None):
    conn = get_re_db_connection()
    cur = None
    sql = """
    UPDATE help
    SET
        status = %s,
        answer = CASE WHEN %s = 'answered' THEN %s
                      WHEN %s = 'pending'  THEN NULL
                      ELSE answer END,
        answered_at = CASE WHEN %s = 'answered' THEN NOW()
                           WHEN %s = 'pending'  THEN NULL
                           ELSE answered_at END,
        updated_at = NOW()
    WHERE id = %s
    """
    try:
        cur = conn.cursor()
        cur.execute(sql, (status, status, answer, status, status, status, help_id))
        if cur.rowcount == 0:
            rollback(conn)
            return None
        commit(conn)
    finally:
        close_cursor(cur)
        close_connection(conn)
    return get_help(help_id)  # get_help도 re_db 사용 중
