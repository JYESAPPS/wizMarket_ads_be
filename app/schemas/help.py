from typing import Optional, Literal
from pydantic import BaseModel
from datetime import datetime

class HelpCreate(BaseModel):
    user_id: Optional[int] = None
    name: str
    email: str
    phone: Optional[str] = None
    category: str
    content: str
    consent_personal: bool

class HelpStatusUpdate(BaseModel):
    status: Literal["pending", "answered", "closed"]

class HelpOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    name: str
    email: str
    phone: Optional[str] = None        # DB가 NULL일 수 있으므로 Optional
    category: str
    content: str
    attachment1: Optional[str] = None
    attachment2: Optional[str] = None
    attachment3: Optional[str] = None
    status: Literal["pending", "answered", "closed"]
    created_at: datetime
    updated_at: datetime
    # consent_personal을 응답에 꼭 노출할 필요가 없으면 생략해도 OK
