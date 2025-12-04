import os
import base64
import requests
from fastapi import HTTPException
import re
from typing import Optional, Dict, Any, List
from app.crud.ads_user import (
    check_user_id as crud_check_user_id,
    register_user as crud_register_user,
    update_user_name_phone as crud_update_user_name_phone,
    get_store as crud_get_store,
    insert_business_info as crud_insert_business_info,
    update_user as crud_update_user,
    stop_user as crud_stop_user,
    unstop_user as crud_unstop_user,
    
)

from app.crud.ads_app import (
    update_register_tag as crud_update_register_tag,
    update_user_status_only as crud_update_user_status_only,
    upsert_user_info_accounts as crud_upsert_user_info_accounts,
    logout_user as crud_logout_user,
    delete_user as crud_delete_user,
    insert_delete_reason as crud_insert_delete_reason
)

from app.crud.concierge import (
    normalize_addr_full
)


def check_user_id(user_id):
    exists = crud_check_user_id(user_id)
    return exists

def register_user(user_id, password):
    crud_register_user(user_id, password)



# 본인인증 후 user 업데이트
def update_user_name_phone(user_id, name, phone):
    crud_update_user_name_phone(user_id, name, phone)




# 매장 조회
def get_store(store_name, road_name):
    # 주소 정규화
    normalized_road = normalize_addr_full(road_name)

    # 주소 검색
    rows = crud_get_store(store_name, normalized_road)

    if rows and len(rows) > 0:
        # 성공: rows 배열 그대로 store_info에
        return {
            "result": "success",
            "store_info": rows,
        }
    else:
        # 실패: ROAD_NAME_ADDRESS만 담아서 반환
        return {
            "result": False,
            "store_info": {
                "ROAD_NAME_ADDRESS": normalized_road,
            },
        }


# 기존 매장 관련 정보 등록
def register_store_info(request, store_business_number):
    user_id = request.user_id

    # 사업자 정보 (번호, 대표자)는 business_verification
    success1 = crud_insert_business_info(user_id, request.business_name, request.business_number)

    # store_business_number를 userTB에 업데이트
    success2 = crud_update_user(user_id, store_business_number, request.status)

    # register_tag를 user_info TB에 업데이트
    success3 = crud_update_register_tag(user_id, request.register_tag)

    return success1 and success2 and success3



def register_sns(req):
    user_id = req.user_id
    status = (req.status or "").strip().lower()

    # 1) 유저 상태 업데이트
    ok = crud_update_user_status_only(user_id=user_id, status=status)
    if not ok:
        raise HTTPException(status_code=500, detail="유저 상태 업데이트 실패")

    # 2) 계정이 있으면 UPSERT (없으면 스킵)
    # 2) user_info에 SNS 계정 업서트 (있을 때만)
    accounts = req.accounts or []
    clean: List[Dict[str, str]] = []
    for a in accounts:
        ch = (a.channel or "").strip()
        acc = (a.account or "").strip()
        if ch and acc:
            clean.append({"channel": ch, "account": acc})

    if clean:
        crud_upsert_user_info_accounts(user_id=user_id, accounts=clean)

    return {"success": True}



#  로그 아웃
def logout_user(user_id: str):
    # 탈퇴 로직 구현 (예: DB에서 사용자 삭제)
    success = crud_logout_user(user_id)

    # success = True  # 실제로는 탈퇴 성공 여부에 따라 설정

    return success



# 회원 정지
def stop_user(user_id: str, reason: str):
    sucess = crud_stop_user(user_id, reason)
    return sucess


# 회원 정지 해제
def unstop_user(user_id: str):
    sucess = crud_unstop_user(user_id)
    return sucess




# 탈퇴 사유 인서트
def insert_delete_reason(reason_id, reason_label, reason_detail):
    crud_insert_delete_reason(reason_id, reason_label, reason_detail)


def delete_user(user_id: str):
    # 탈퇴 로직 구현 (예: DB에서 사용자 삭제)
    success = crud_delete_user(user_id)

    # success = True  # 실제로는 탈퇴 성공 여부에 따라 설정

    return success
