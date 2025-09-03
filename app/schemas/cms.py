from typing import Optional, List, Literal
from fastapi import Query
from pydantic import BaseModel, Field
from datetime import datetime

BVStatus = Literal["pending", "approved", "rejected"]

class BVItem(BaseModel):
    id: int
    user_id: int
    business_name: str
    business_number: str
    original_filename: str
    saved_filename: str
    saved_path: str
    content_type: str
    size_bytes: int
    status: str
    notes: Optional[str] = None
    reviewer_id: Optional[int] = None
    created_at: str
    reviewed_at: Optional[str] = None

class BVListResponse(BaseModel):
    ok: bool
    page: int
    page_size: int
    total: int
    items: List[BVItem]

class BVApproveResponse(BaseModel):
    ok: bool
    id: int
    status: BVStatus
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None


class BVRejectRequest(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=255)