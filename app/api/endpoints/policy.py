# app/api/ads_policy.py
from typing import List
from fastapi import APIRouter, Query
from pydantic import BaseModel
from datetime import date, datetime

from app.service.policy import service_get_policy_versions

router = APIRouter(
    prefix="/policy",
    tags=["ads_policy"],
)


class PolicyVersionOut(BaseModel):
    policy_id: int
    type: str
    version_label: str
    component_key: str
    is_active: bool
    effective_date: date
    created_at: datetime | None = None


@router.get("/list", response_model=List[PolicyVersionOut])
def get_policy_version_list(
    type: str = Query(..., regex="^(TOS|PRIVACY|PERMISSION)$")
):
    """
    정책 버전 리스트 조회
    - type: 'TOS' | 'PRIVACY' | 'PERMISSION'
    """
    rows = service_get_policy_versions(type)
    return rows
