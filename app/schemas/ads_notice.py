from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class AdsNotice(BaseModel):
    notice_no: int
    notice_post: str = "Y"
    notice_push: str = "Y"
    notice_type: str = "일반"
    notice_title: str
    notice_content: str
    notice_file: Optional[str] = None
    notice_images: Optional[list[str]] = []
    views: int = 0
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class AdsNoticeCreateRequest(BaseModel):
    notice_post: str = "Y"
    notice_type: str = "일반"
    notice_title: str
    notice_content: str

class AdsNoticeUpdateRequest(BaseModel):
    notice_no: int
    notice_post: str = "Y"
    notice_type: str = "일반"
    notice_title: str
    notice_content: str
    notice_file: Optional[str] = None
    updated_at: datetime

class AdsNoticeDeleteRequest(BaseModel):
    notice_no: int

class AdsNoticeReadInsertRequest(BaseModel):
    user_id: str
    notice_no: int