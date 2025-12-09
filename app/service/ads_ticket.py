from app.crud.ads_ticket import (
    get_cycle as crud_get_cycle,
    insert_payment as crud_insert_payment,
    get_token_amount as crud_get_token_amount,
    get_latest_token_onetime as crud_get_latest_token_onetime,
    insert_onetime as crud_insert_onetime,
    insest_monthly as crud_insest_monthly,
    insest_yearly as crud_insest_yearly,
    get_history_100 as crud_get_history_100,
    get_history as crud_get_history,
    get_valid_history as crud_get_valid_history,
    get_latest_token_subscription as crud_get_latest_token_subscription,
    # get_valid_ticket as crud_get_valid_ticket,
    # insert_payment_history as crud_insert_token_deduction_history,
    # insert_token_deduction_history as crud_insert_token_deduction_history,
    get_token_deduction_history as crud_get_token_deduction_history,
    get_subscription_info as crud_get_subscription_info,
    update_subscription_info as crud_update_subscription_info,
    # get_token_onetime as crud_get_token_onetime,
    upsert_token_usage as crud_upsert_token_usage,
    get_valid_ticket as crud_get_valid_ticket,
    get_token_onetime as crud_get_token_onetime,
    get_token_usage_history as crud_get_token_usage_history,
    get_purchase_history as crud_get_purchase_history,
)
from app.crud.ads_token_deduct import (
    crud_get_latest_subscription_purchase,
    crud_get_latest_onetime_purchase,
    crud_decrement_purchase_token,
    crud_upsert_token_usage,
    crud_get_user_total_remaining_tokens,
)

from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import date
from fastapi import HTTPException
from app.db.connect import (
    commit, close_connection, rollback, close_cursor, get_re_db_connection
)
import pymysql
from typing import Optional


# ticket_payment에 추가
def insert_payment(request):
    user_id = request.user_id
    payment_method = request.payment_method
    payment_date = datetime.fromisoformat(request.payment_date.replace("Z", "+00:00")).date()

    ticket_id = request.ticket_id
    # ticket_id로 기한 조회해 단건/정기 구분
    cycle = crud_get_cycle(ticket_id)
    if cycle:    
        expire_date = payment_date+relativedelta(months=cycle) # +기한
    else:
        expire_date = None

    # DB 추가 로직
    crud_insert_payment(user_id, ticket_id, payment_method, payment_date, expire_date)

#ticket_token에 추가
def insert_token(request):
    user_id = request.user_id
    ticket_id = request.ticket_id
    # 지급 토큰 수량 조회
    token_amount = crud_get_token_amount(ticket_id)
    # print(request)

    # 지급 일자
    grant_date = datetime.fromisoformat(request.payment_date.replace("Z", "+00:00")).date()

    # 단건 토큰 + 지급 토큰 = 지급 후 단건 토큰 개수
    token_onetime = crud_get_latest_token_onetime(user_id)
    subscription_info = crud_get_latest_token_subscription(user_id)
    token_subscription = subscription_info["sub"]

    #단건의 경우
    if request.plan_type=="basic":
        token_onetime = token_onetime + token_amount
        #삽입
        crud_insert_onetime(user_id, ticket_id, token_amount, token_subscription, token_onetime, grant_date)
           
    # 정기권의 경우 월별로 지급
    else: 
        # if request.billing_cycle == "없음":
        #     crud_insert_onetime(user_id, ticket_id, token_amount, token_onetime, grant_date)

        # 월 구독
        if request.billing_cycle == "월간":
            token_subscription = token_subscription + token_amount
            crud_insest_monthly(user_id, ticket_id, token_amount, token_subscription, token_onetime, grant_date)

        # 년구독
        elif request.billing_cycle == "연간":
            token_amount = token_amount * 12
            token_subscription = token_subscription + token_amount
            crud_insest_yearly(user_id, ticket_id, token_amount, token_subscription, token_onetime, grant_date) 

    # grant_date : 구매 일자부터 종료일자까지 달별로 지급
    # token_grant
    # token_sub 
    # valid_until : 지급 일자+1달

def update_subscription_info(user_id, plan_type):
    # 기존 구독 상품 조회
    subscrtiption_type = crud_get_subscription_info(user_id)

    # if 구독 있음 && basic은 update 안함
    if subscrtiption_type and plan_type == "basic":
        return

    # if 구독 없음: 바로 입력
    else:
        crud_update_subscription_info(user_id, plan_type)

# 100개 결제 내역 조회
def get_history_100(user_id):
    status = crud_get_history_100(user_id)
    return status


#결제 내역 조회
def get_history(user_id):
    all_history = crud_get_history(user_id)
    valid_history = crud_get_valid_history(user_id)
    purchase_history = crud_get_purchase_history(user_id)
    return {"all": all_history, "valid": valid_history, "purchase": purchase_history}




# 사용자의 단건&정기 토큰 반환
def get_token(user_id):
    conn = get_re_db_connection()
    cursor = None

    try:
        # ✅ 실제 커서 생성
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        total_remaining = crud_get_user_total_remaining_tokens(
            cursor=cursor,
            user_id=user_id,
        )

        return {
            "user_id": user_id,
            "remaining_tokens_total": total_remaining,
        }

    finally:
        if cursor is not None:
            close_cursor(cursor)
        close_connection(conn)




# 사용자가 구매한 정보 + 남은 토큰 반환
def get_valid_ticket(user_id: int) -> dict:
    conn = get_re_db_connection()
    cursor = None

    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 1) 남은 토큰 합계
        total_remaining = crud_get_user_total_remaining_tokens(
            cursor=cursor,
            user_id=user_id,
        )

        # 2) 구독 상품 정보 우선
        valid_ticket = crud_get_valid_ticket(cursor, user_id)

        # 3) 구독이 없으면 단건 상품 정보
        if valid_ticket is None:
            valid_ticket = crud_get_token_onetime(cursor, user_id)

        return {
            "ticket_name": valid_ticket["ticket_name"] if valid_ticket else None,
            "token_amount": total_remaining,
            "billing_cycle": valid_ticket["billing_cycle"] if valid_ticket else None,
        }

    finally:
        if cursor is not None:
            close_cursor(cursor)
        close_connection(conn)


class NoTokenError(Exception):
    """사용 가능한 토큰이 없을 때 사용하는 도메인 예외"""
    pass


def deduct_token(user_id: int, usage_date: Optional[date] = None) -> dict:
    """
    TOKEN_PURCHASE / TOKEN_USAGE 기반 토큰 차감 서비스.

    로직:
      1) tansaction_type != '단건' 인 구매(구독/정기)에서 남은 토큰 차감 시도
      2) 실패 시, tansaction_type = '단건' 인 구매에서 차감 시도
      3) 둘 다 실패하면 NoTokenError 발생
      4) 성공 시 TOKEN_USAGE(usage_date 기준)에 used_tokens += 1 (upsert)

    모든 작업은 하나의 커넥션 + 하나의 트랜잭션 안에서 처리.
    """
    if usage_date is None:
        usage_date = date.today()

    conn = get_re_db_connection()
    cursor = None

    try:
        # 필요하면 autocommit 꺼주기 (환경에 따라 생략 가능)
        try:
            conn.autocommit(False)
        except AttributeError:
            # 어떤 커넥터는 autocommit 속성이 없을 수 있으니 안전하게 무시
            pass

        # Dict 형태로 결과를 받고 싶다면 DictCursor 사용
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        today = usage_date

        # 1) 구독/정기(비단건) 쪽에서 차감 가능한 가장 최근 purchase 찾기
        subscription_purchase = crud_get_latest_subscription_purchase(
            cursor=cursor,
            user_id=user_id,
            today=today,
        )

        # 2) 단건 쪽에서 차감 가능한 가장 최근 purchase 찾기
        onetime_purchase = crud_get_latest_onetime_purchase(
            cursor=cursor,
            user_id=user_id,
        )

        used_type: Optional[str] = None
        used_purchase: Optional[dict] = None

        # 3-A) 구독/정기에서 먼저 차감 시도
        if subscription_purchase is not None:
            ok = crud_decrement_purchase_token(
                cursor=cursor,
                purchase_id=subscription_purchase["purchase_id"],
            )
            if ok:
                used_type = "subscription"
                used_purchase = subscription_purchase

        # 3-B) 구독에서 못 뺐으면(행이 없거나 UPDATE 실패) 단건에서 재시도
        if used_purchase is None and onetime_purchase is not None:
            ok = crud_decrement_purchase_token(
                cursor=cursor,
                purchase_id=onetime_purchase["purchase_id"],
            )
            if ok:
                used_type = "onetime"
                used_purchase = onetime_purchase

        # 3-C) 둘 다 실패 → 사용 가능한 토큰 없음
        if used_purchase is None:
            raise NoTokenError("사용 가능한 토큰이 없습니다.")

        # 4) TOKEN_USAGE upsert (같은 트랜잭션 안에서)
        crud_upsert_token_usage(
            cursor=cursor,
            user_id=user_id,
            usage_date=today,
            used_delta=1,
        )

        # 5) (옵션) 전체 남은 토큰 합계 조회
        total_remaining = crud_get_user_total_remaining_tokens(
            cursor=cursor,
            user_id=user_id,
        )

        # 6) 커밋
        commit(conn)

        return {
            "user_id": user_id,
            "used_type": used_type,               # "subscription" / "onetime"
            "used_tokens": 1,
            "usage_date": today.isoformat(),
            "purchase_id": used_purchase["purchase_id"],
            "remaining_tokens_total": total_remaining,
        }

    except Exception:
        # NoTokenError 포함 모든 예외 롤백 후 다시 던짐
        rollback(conn)
        raise
    finally:
        if cursor is not None:
            close_cursor(cursor)
        close_connection(conn)



def get_token_deduction_history(user_id: int):
    rows = crud_get_token_deduction_history(user_id)

    result = []
    running_total = 0

    for row in rows:
        deducted = row["total_deducted"]
        granted = int(row["total_granted"] or 0)
        remaining_onetime = int(row["end_onetime"] or 0)
        remaining_subscription = int(row["end_subscription"] or 0)
        running_total += deducted  # 누적 차감량
        
        result.append({
            "grant_date": row["grant_date"],
            "deducted": deducted,
            "granted": granted,
            "running_total": running_total,
            "remaining_onetime": remaining_onetime,
            "remaining_subscription": remaining_subscription,
        })

    return result



def get_token_usage_history(user_id):
    return crud_get_token_usage_history(user_id)


