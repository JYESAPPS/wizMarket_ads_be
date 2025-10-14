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
    get_latest_token_subscription as crud_get_latest_token_subscription,
    get_valid_ticket as crud_get_valid_ticket,
    # insert_payment_history as crud_insert_token_deduction_history,
    insert_token_deduction_history as crud_insert_token_deduction_history,
    get_token_deduction_history as crud_get_token_deduction_history,
    update_subscription_info as crud_update_subscription_info,
)

from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import date
from fastapi import HTTPException


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

def update_subscription_info(user_id, plan_type):
    crud_update_subscription_info(user_id, plan_type)


    # grant_date : 구매 일자부터 종료일자까지 달별로 지급
    # token_grant
    # token_sub 
    # valid_until : 지급 일자+1달


# 100개 결제 내역 조회
def get_history_100(user_id):
    status = crud_get_history_100(user_id)
    return status


#결제 내역 조회
def get_history(user_id):
    data = crud_get_history(user_id)
    return data

# 사용자의 단건&정기 토큰 반환
def get_token(user_id):
    onetime = crud_get_latest_token_onetime(user_id) or 0
    subscription = crud_get_latest_token_subscription(user_id) or {}

    return {
        "onetime": onetime,
        "subscription": subscription.get("sub", 0),
        "valid_until": subscription.get("valid")
        # "subscription": subscription["sub"],
        # "valid_until": subscription["valid"]
    }

# 사용자 티켓 & 토큰 호출
def get_valid_ticket(user_id):
    #
    onetime = crud_get_latest_token_onetime(user_id)
    subscription = crud_get_latest_token_subscription(user_id)
    valid_ticket = crud_get_valid_ticket(user_id)

    return {
        "ticket_name": valid_ticket["ticket_name"] if valid_ticket else None,
        "token_amount": onetime + (subscription["sub"] or 0)
    }

# 차감 함수
def deduct_token(user_id):
    sub_data  = crud_get_latest_token_subscription(user_id) # 정기 토큰 + 만료일
    token_onetime = crud_get_latest_token_onetime(user_id) # 단건 토큰

    token_subscription = sub_data["sub"]
    valid_until = sub_data["valid"]

    # None 대응
    if sub_data is None:
        token_subscription = 0
        valid_until = None
    else:
        token_subscription = sub_data.get("sub") or 0
        valid_until = sub_data.get("valid")

    if token_onetime is None:
        token_onetime = 0

    total = token_subscription + token_onetime
    if total < 1:
        raise ValueError("사용 가능한 토큰이 없습니다.")
    
    # 차감
    used_type = None
    if token_subscription > 0:
        token_subscription -= 1
        used_type = "subscription"
    elif token_onetime > 0:
        token_onetime -= 1
        used_type = "onetime"

    # 차감 기록 DB 저장
    crud_insert_token_deduction_history(
        user_id=user_id,
        token_grant=1,
        token_subscription=token_subscription,
        token_onetime=token_onetime,
        valid_until=valid_until,
        grant_date=datetime.now()
    )

    return {
        'user_id': user_id,
        'used_type': used_type,
        'token_subscription': token_subscription,
        'token_onetime': token_onetime,
        "remaining_tokens": token_subscription + token_onetime,
        "total_tokens": total
    }

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
