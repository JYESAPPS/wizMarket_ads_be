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
               origin1, origin2, origin3, 
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
    attachments: tuple[Optional[str], Optional[str], Optional[str]],
    origins: tuple[Optional[str], Optional[str], Optional[str]],
) -> Dict[str, Any]:
    sql_ins = """
        INSERT INTO help
            (name, email, phone, category, title, content,
             attachment1, origin1, attachment2, origin2, attachment3, origin3, status)
        VALUES (%s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s)
    """
    sql_sel = """
        SELECT id, name, email, phone, category, title, content,
               attachment1, attachment2, attachment3,
               origin1, origin2, origin3,
               status, answer, answered_at,
               created_at, updated_at
        FROM help
        WHERE id = %s
        LIMIT 1
    """

    # 🔹 기본값 정리
    email = payload.email or ""       # None, "" → ""
    phone = payload.phone or ""       # 필요 없으면 그냥 payload.phone 써도 됨

    a1, a2, a3 = attachments or (None, None, None)
    o1, o2, o3 = origins or (None, None, None)

    conn = get_re_db_connection()
    cur = None
    try:
        cur = conn.cursor()
        cur.execute(
            sql_ins,
            (
                payload.name,
                email,
                phone,
                payload.category,
                payload.title,
                payload.content,
                a1, o1,
                a2, o2,
                a3, o3,
                "pending",   # 🔹 status
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

        # phone이 NULL이면 None으로 유지 (이미 DictCursor에서 None일 것)
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



# 앱 버전 문의 내역 불러오기
def get_help_list_app(name: str, phone: str) -> List[Dict[str, Any]]:
    """
    앱용 문의 리스트 조회.
    - name, phone 필수
    - created_at 내림차순
    """
    conn = get_re_db_connection()
    cur = None

    sql = """
    SELECT
        id,
        name,
        phone,
        category,
        title,
        content,
        attachment1,
        attachment2,
        attachment3,
        status,
        created_at
    FROM help
    WHERE name = %s
      AND REPLACE(REPLACE(phone, '-', ''), ' ', '') = %s
    ORDER BY created_at DESC
    """

    try:
        cur = conn.cursor()
        # phone 은 항상 "01049171768" 형식으로 들어온다고 가정
        cur.execute(sql, (name, phone))
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description]
        result = [dict(zip(columns, row)) for row in rows]
        return result
    finally:
        close_cursor(cur)
        close_connection(conn)