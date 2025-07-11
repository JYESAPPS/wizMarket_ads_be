from app.crud.ads_ticket import (
    get_cycle as crud_get_cycle,
    insert_payment as crud_insert_payment,
    get_token_amount as crud_get_token_amount,
    get_latest_token_onetime as crud_get_latest_token_onetime,
    insert_onetime as crud_insert_onetime,
    get_history as crud_get_history,
    get_latest_token_subscription as crud_get_latest_token_subscription
)

from datetime import datetime
from dateutil.relativedelta import relativedelta


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
    token_amount = crud_get_token_amount(ticket_id)

    #단건의 경우
    if request.type=="basic":
        grant_date = datetime.fromisoformat(request.payment_date.replace("Z", "+00:00")).date()
        token_onetime = crud_get_latest_token_onetime(user_id) + token_amount
        #삽입
        crud_insert_onetime(user_id, ticket_id, token_amount, token_onetime, grant_date)
           
    # 정기권의 경우 월별로 지급
    else: 
        print("regular")
    # grant_date : 구매 일자부터 종료일자까지 달별로 지급
    # token_grant
    # token_sub 
    # valid_until : 지급 일자+1달

#결제 내역 조회
def get_history(user_id):
    data = crud_get_history(user_id)
    return data

# 사용자의 단건&정기 토큰 반환
def get_token(user_id):
    onetime = crud_get_latest_token_onetime(user_id)
    subscription = crud_get_latest_token_subscription(user_id)

    return {
        "onetime": onetime,
        "subscription": subscription["sub"],
        "valid_until": subscription["valid"]
    }
