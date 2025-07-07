from app.crud.ads_plan import (
    get_plan_list as crud_get_plan_list,
    insert_fee as crud_insert_fee,
    delete_fee as crud_delete_fee
)




def get_plan_list():
    list = crud_get_plan_list()

    return list

def insert_fee(request):
    ticket_name = request.ticket_name
    ticket_price = request.ticket_price
    ticket_type = request.ticket_type  # ← 오타 수정
    billing_cycle = request.billing_cycle  # Optional[str]
    token_amount = request.token_amount
    print(billing_cycle)
    # 예: 유효성 체크
    if ticket_type == "subscription" and not billing_cycle:
        raise ValueError("구독 상품에는 billing_cycle이 필요합니다.")

    crud_insert_fee(ticket_name, ticket_price, ticket_type, billing_cycle, token_amount)

def delete_fee(ticket_id):
    crud_delete_fee(ticket_id)