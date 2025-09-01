from app.crud.cms import (
    insert_business_verification as crud_insert_business_verification,
    cms_list_verifications as crud_cms_list_verifications
)
from typing import Optional, Dict, Any


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