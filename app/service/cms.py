from app.crud.cms import (
    insert_business_verification as crud_insert_business_verification,
    cms_list_verifications as crud_cms_list_verifications,
    cms_approve_verification as crud_cms_approve_verification,
    cms_reject_verification as crud_cms_reject_verification,
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

