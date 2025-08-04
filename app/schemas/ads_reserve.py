from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class ReserveCreate(BaseModel):
    user_id: str
    start_date: date
    end_date: date
    repeat_type: str  # daily, weekly, monthly
    repeat_count: int
    upload_times: List[str]
    weekly_days: Optional[List[str]] = None  # ["Mon", "Wed"]
    monthly_days: Optional[List[str]] = None  # ["2025-08-30", "2025-09-02"]

    class Config:
        orm_mode = True
