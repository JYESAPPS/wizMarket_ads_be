# app/crud/policy.py (이 파일 하나로 정리 추천)
from typing import List, Dict, Any
import pymysql
from app.db.connect import (
    get_re_db_connection,
    close_connection,
    close_cursor,
)

def crud_get_policy_versions(policy_type: str) -> List[Dict[str, Any]]:
    """
    특정 타입(TOS / PRIVACY / PERMISSION)의 정책 버전 목록 조회
    dict 리스트로 리턴 (service에서 r["..."]로 접근 가능하도록)
    """
    conn = get_re_db_connection()
    # ✅ DictCursor 사용해서 바로 dict 반환
    cur = conn.cursor(pymysql.cursors.DictCursor)

    try:
        sql = """
            SELECT
                policy_id,
                type,
                version_label,
                component_key,
                is_active,
                effective_date,
                created_at
            FROM ads_policy_version
            WHERE type = %s
            ORDER BY effective_date DESC, policy_id DESC
        """
        cur.execute(sql, (policy_type,))
        rows = cur.fetchall()   # 이미 List[Dict[str, Any]]
        return rows

    finally:
        close_cursor(cur)
        close_connection(conn)


def crud_get_policy_detail(policy_id: int) -> Dict[str, Any]:
    """
    policy_id 단일 정책 메타 정보 조회
    """
    conn = get_re_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    try:
        sql = """
            SELECT
                policy_id,
                type,
                version_label,
                component_key,
                is_active,
                effective_date,
                created_at
            FROM ads_policy_version
            WHERE policy_id = %s
        """
        cur.execute(sql, (policy_id,))
        row = cur.fetchone()  # Dict 또는 None
        return row or {}

    finally:
        close_cursor(cur)
        close_connection(conn)



