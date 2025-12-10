from app.crud.ads_ticket import (
    get_cycle as crud_get_cycle,
    get_token_amount as crud_get_token_amount,
)

from app.crud.ads_token_purchase import (
    insert_purchase as crud_insert_purchase,
    get_lastest_subscription as crud_get_lastest_subscription,
    get_lastest_history as crud_get_lastest_history,
)


from datetime import datetime
from dateutil.relativedelta import relativedelta


# token_purchase 추가
def insert_purchase(request):
    user = request.user_id
    ticket = request.ticket_id

    type = request.type
    start = None
    end = None

    if ticket:
        # 구독 갱신 주기 조회
        cycle = crud_get_cycle(ticket)

        # 지급 토큰 개수 조회
        purchased = crud_get_token_amount(ticket)
        remaining = purchased

    if cycle:
        type = "subscription"
        # 가장 최근 구독과 토큰
        recent_subscription = crud_get_lastest_subscription(user)
        recent_token = recent_subscription["remaining_tokens"]

        # 구독권 구매일 시 시작/종료 날짜
        start = datetime.now()
        end = start + relativedelta(month=cycle)

        recent_type = crud_get_lastest_history(user)
        
        if recent_type in ("subscription", "change", "unsubscribe"):
            remaining = purchased + recent_token

            if recent_type != "unsubscribe":
                type = "change"

    if type == "fail":
        remaining = 0

    crud_insert_purchase(user, ticket, type, purchased, remaining, start, end)

