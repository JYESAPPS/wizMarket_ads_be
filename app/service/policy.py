# app/service/policy_service.py
from typing import List, Dict, Any
from app.crud.policy import crud_get_policy_versions

def service_get_policy_versions(policy_type: str) -> List[Dict[str, Any]]:
    """
    정책 버전 목록 반환 (프론트 셀렉트 박스용)
    """
    # 필요하면 여기서 추가 가공 가능
    rows = crud_get_policy_versions(policy_type)

    # 예: is_active를 bool로 보장
    for r in rows:
        r["is_active"] = bool(r.get("is_active", 0))
    return rows
