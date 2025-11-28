# app/schemas/policy.py
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PolicyVersionListItem(BaseModel):
    policy_id: int
    policy_type: str
    version_label: str
    effective_date: date
    is_active: bool

    class Config:
        orm_mode = True


class PolicyDetail(BaseModel):
    policy_id: int
    policy_type: str
    version_label: str
    effective_date: date
    title: str
    content_html: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class PolicyCreate(BaseModel):
    policy_type: str = Field(..., description="TOS / PRIVACY / PERMISSION")
    version_label: str
    effective_date: date
    title: str
    content_html: str
    is_active: bool = True
