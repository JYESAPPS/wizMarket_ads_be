from app.crud.cms import (
    insert_business_verification as crud_insert_business_verification,
    cms_list_verifications as crud_cms_list_verifications,
    cms_approve_verification as crud_cms_approve_verification,
    cms_reject_verification as crud_cms_reject_verification,
    cms_get_user_list as crud_get_user_list,
    cms_get_deleted_user_list as crud_get_deleted_user_list,
    cms_get_user_detail as crud_get_user_detail,
    cms_get_user_payments as crud_cms_get_user_payments,
    get_business_verification as crud_get_business_verification,
    cms_marketing_agree as crud_cms_marketing_agree,
)
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

# 사업자 등록증 제출
def insert_business_verification(
        user_id,
        original,
        saved_name,
        dest_path,    
        content_type,
        size_bytes,
        bs_name,
        bs_number
):
    crud_insert_business_verification(
        user_id,
        original,
        saved_name,
        dest_path,    
        content_type,
        size_bytes,
        bs_name,
        bs_number
    )


# 사업자 등록증 목록 조회
def cms_list_verifications(
    user_id: Optional[int],
    status: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    page: int,
    page_size: int,
) -> Dict[str, Any]:
    """
    비즈니스 로직을 추가할 수 있는 레이어.
    ex) 날짜 유효성, 기본값 보정, 추가 가공 등
    """
    # 날짜 포맷 검증 등 필요 시 여기에 추가
    # 예: yyyy-mm-dd 체크, date_from <= date_to 여부 등

    total, items = crud_cms_list_verifications(
        user_id=user_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )

    return {
        "ok": True,
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": items,
    }


def cms_approve_verification(id : int) -> None:
    affected = crud_cms_approve_verification(id)
    if affected == 0:
        # 이미 approved/rejected이거나 id가 없음 — 프론트는 alert(detail) 사용
        # 필요 시 404/409를 구분하고 싶다면 여기서 한번 더 SELECT 하거나 메시지 바꾸기
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 처리되었거나 존재하지 않는 항목입니다."
        )
    # 성공 시 반환 없음 (204)



def cms_reject_verification(id: int, notes: str | None) -> None:
    affected = crud_cms_reject_verification(id, notes)
    if affected == 0:
        # 이미 처리됐거나 없는 항목
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 처리되었거나 존재하지 않는 항목입니다."
        )
    # 성공 시 바디 없이 204


def cms_get_user_list():
    rows = crud_get_user_list()  # list[tuple]
    users = []
    for r in rows:
        (user_id, email, login_provider, created_at, status, nickname,
        platform, last_seen,
        ticket_name, ticket_id, payment_date) = r

        users.append({
            "user_id": user_id,
            "email": email,
            "login_provider": login_provider,
            "created_at": created_at,
            "status": status,
            "nickname": nickname,
            "platform": platform,
            "last_seen": last_seen,
            "ticket_name": ticket_name,
            "ticket_id": ticket_id,
            "payment_date": payment_date,
        })
    return users


def cms_get_deleted_user_list():
    rows = crud_get_deleted_user_list()  # list[tuple]
    users = []
    for r in rows:
        (user_id, email, login_provider, created_at, status, nickname,
        platform, last_seen,
        ticket_name, ticket_id, payment_date) = r

        users.append({
            "user_id": user_id,
            "email": email,
            "login_provider": login_provider,
            "created_at": created_at,
            "status": status,
            "nickname": nickname,
            "platform": platform,
            "last_seen": last_seen,
            "ticket_name": ticket_name,
            "ticket_id": ticket_id,
            "payment_date": payment_date,
        })
    return users



def cms_get_user_detail(user_id):
    row = crud_get_user_detail(user_id)
    if not row:
        return None
    
    (user_id, email, login_provider, created_at, status, stop_reason, nickname, phone, birth_year, register_tag, subscription_type, platform, last_seen,
    store_name, large_cat, medium_cat, small_cat, industry_name, road_name_address,) = row

    return {
        "user_id": user_id,
        "email": email,
        "login_provider": login_provider,
        "created_at": created_at,
        "status": status,
        "stop_reason": stop_reason,
        "nickname": nickname,
        "phone": phone,
        "birth_year": birth_year,
        "register_tag": register_tag,
        "subscription_type": subscription_type,
        "register_tag": register_tag,
        "platform": platform,
        "last_seen": last_seen,
        "store_name": store_name,
        "large_category_name": large_cat,
        "medium_category_name": medium_cat,
        "small_category_name": small_cat,
        "industry_name": industry_name,
        "road_name_address": road_name_address,
    }

def cms_get_user_payments(user_id):
    rows = crud_cms_get_user_payments(user_id)

    payments = []

    for (
        payment_id, u_id, ticket_id,
        ticket_name, ticket_price, billing_cycle,
        payment_date, expire_date, next_renewal, is_valid
    ) in rows:
        payments.append({
            "payment_id": int(payment_id) if payment_id is not None else None,
            "user_id": int(u_id) if u_id is not None else None,
            "ticket_id": int(ticket_id) if ticket_id is not None else None,
            "ticket_name": ticket_name,
            "ticket_price": float(ticket_price) if ticket_price is not None else None,
            "billing_cycle": int(billing_cycle) if billing_cycle is not None else None,
            "payment_date": payment_date.isoformat() if payment_date else None,
            "expire_date": expire_date.isoformat() if expire_date else None,
            "next_renewal": next_renewal.isoformat() if next_renewal else None,
            "is_valid": int(is_valid) if is_valid is not None else 0,
        })

    return payments 


def get_business_verification(user_id):
    return crud_get_business_verification(user_id)

def cms_marketing_agree(user_id: int, agree: bool):
    return crud_cms_marketing_agree(user_id, agree)
