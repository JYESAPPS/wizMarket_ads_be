from typing import Optional, Literal
from pydantic import BaseModel
from datetime import datetime

class HelpCreate(BaseModel):
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    category: str
    title: Optional[str] = None
    content: str

class HelpStatusUpdate(BaseModel):
    status: Literal["pending", "answered", "closed"]
    answer: Optional[str] = None

class HelpOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None        # DB가 NULL일 수 있으므로 Optional
    category: str
    title: Optional[str] = None
    content: str
    answer: Optional[str] = None
    answered_at: Optional[datetime] = None
    attachment1: Optional[str] = None
    attachment2: Optional[str] = None
    attachment3: Optional[str] = None
    status: Literal["pending", "answered", "closed"]
    created_at: datetime
    updated_at: datetime
    # consent_personal을 응답에 꼭 노출할 필요가 없으면 생략해도 OK
