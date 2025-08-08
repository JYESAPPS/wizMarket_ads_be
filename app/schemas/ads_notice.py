from pydantic import BaseModel
from datetime import datetime

class AdsNotice(BaseModel):
    notice_no: int
    notice_title: str
    notice_content: str
    created_at: datetime  

    class Config:
        from_attributes = True


class AdsNoticeCreateRequest(BaseModel):
    notice_title: str
    notice_content: str

class AdsNoticeUpdateRequest(BaseModel):
    notice_no: int
    notice_title: str
    notice_content: str

class AdsNoticeDeleteRequest(BaseModel):
    notice_no: int

class AdsNoticeReadInsertRequest(BaseModel):
    user_id: str
    notice_no: int