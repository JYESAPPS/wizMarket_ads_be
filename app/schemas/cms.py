from typing import Optional, List
from fastapi import Query
from pydantic import BaseModel

class BVItem(BaseModel):
    id: int
    user_id: int
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
