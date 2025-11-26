# app/crud/token.py
from datetime import date
from typing import Optional

import pymysql  # DictCursor 타입용 (서비스에서 이미 DictCursor로 만들고 들어옴)


# 1) 구독/정기(비단건) 쪽에서 차감 후보 찾기
def crud_get_latest_subscription_purchase(
    cursor: pymysql.cursors.Cursor,
    user_id: int,
    today: date,
) -> Optional[dict]:
    """
    tansaction_type != '단건' 이면서,
    - remaining_tokens > 0
    - (start_date, end_date 기준으로 오늘 사용 가능)
    인 것 중에서 '가장 최근' 한 건 조회
    """
    sql = """
        SELECT
            purchase_id,
            user_id,
            ticket_id,
            tansaction_type,
            purchased_tokens,
            remaining_tokens,
            start_date,
            end_date,
            created_at,
            updated_at
        FROM TOKEN_PURCHASE
        WHERE user_id = %s
          AND tansaction_type <> '단건'
          AND remaining_tokens > 0
          AND (start_date IS NULL OR start_date <= %s)
          AND (end_date   IS NULL OR end_date   >= %s)
        ORDER BY
            start_date DESC,
            created_at DESC,
            purchase_id DESC
        LIMIT 1
    """
    cursor.execute(sql, (user_id, today, today))
    row = cursor.fetchone()
    return row  # DictCursor 이면 dict, 아니면 tuple


# 2) 단건 쪽에서 차감 후보 찾기
def crud_get_latest_onetime_purchase(
    cursor: pymysql.cursors.Cursor,
    user_id: int,
) -> Optional[dict]:
    """
    tansaction_type = '단건'
    - remaining_tokens > 0
    인 것 중에서 '가장 최근' 한 건 조회
    """
    sql = """
        SELECT
            purchase_id,
            user_id,
            ticket_id,
            tansaction_type,
            purchased_tokens,
            remaining_tokens,
            start_date,
            end_date,
            created_at,
            updated_at
        FROM TOKEN_PURCHASE
        WHERE user_id = %s
          AND tansaction_type = '단건'
          AND remaining_tokens > 0
        ORDER BY
            created_at DESC,
            purchase_id DESC
        LIMIT 1
    """
    cursor.execute(sql, (user_id,))
    row = cursor.fetchone()
    return row


# 3) TOKEN_PURCHASE 한 건에서 remaining_tokens 1개 차감
def crud_decrement_purchase_token(
    cursor: pymysql.cursors.Cursor,
    purchase_id: int,
) -> bool:
    """
    특정 purchase_id 의 remaining_tokens 를 1 감소.
    - remaining_tokens > 0 인 경우에만 감소
    - 성공 시 True, 차감할 수 없으면 False
    """
    sql = """
        UPDATE TOKEN_PURCHASE
        SET remaining_tokens = remaining_tokens - 1
        WHERE purchase_id = %s
          AND remaining_tokens > 0
    """
    cursor.execute(sql, (purchase_id,))
    # rowcount 가 1이면 실제로 1줄 업데이트 된 것 → 차감 성공
    return cursor.rowcount == 1


# 4) TOKEN_USAGE upsert (하루 사용량 누적)
def crud_upsert_token_usage(
    cursor: pymysql.cursors.Cursor,
    user_id: int,
    usage_date: date,
    used_delta: int,
) -> None:
    """
    TOKEN_USAGE에 (user_id, usage_date) 기준으로 used_tokens를 누적.
    - 없으면 INSERT
    - 있으면 used_tokens += used_delta
    """
    sql = """
        INSERT INTO TOKEN_USAGE (user_id, usage_date, used_tokens)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            used_tokens = used_tokens + VALUES(used_tokens)
    """
    cursor.execute(sql, (user_id, usage_date, used_delta))


# 5) 전체 남은 토큰 합계 조회 (옵션)
def crud_get_user_total_remaining_tokens(
    cursor: pymysql.cursors.Cursor,
    user_id: int,
) -> int:
    """
    해당 유저의 TOKEN_PURCHASE 남은 토큰 전체 합계 조회.
    """
    sql = """
        SELECT COALESCE(SUM(remaining_tokens), 0) AS total_remaining
        FROM TOKEN_PURCHASE
        WHERE user_id = %s
    """
    cursor.execute(sql, (user_id,))
    row = cursor.fetchone()

    if not row:
        return 0

    # DictCursor 기준
    if isinstance(row, dict):
        return int(row.get("total_remaining") or 0)

    # tuple 등 다른 커서일 경우 대비
    return int(row[0] or 0)
