from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from datetime import datetime

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
        from_attributes = True



class ReserveGet(BaseModel):
    user_id: int



class ReserveGetList(BaseModel):
    reserve_id : int
    repeat_type : str
    repeat_count : int
    start_date : date
    end_date : date
    upload_times: List[str]
    weekly_days: Optional[List[str]] = None  # ["Mon", "Wed"]
    monthly_days: Optional[List[str]] = None  # ["2025-08-30", "2025-09-02"]
    is_active : int
    created_at : datetime


class ReserveUpdateStatus(BaseModel):
    reserve_id : int


class ReserveDelete(BaseModel):
    reserve_id : int


class ReserveUpdate(BaseModel):
    reserve_id : int
    user_id: str
    start_date: date
    end_date: date
    repeat_type: str  # daily, weekly, monthly
    repeat_count: int
    upload_times: List[str]
    weekly_days: Optional[List[str]] = None  # ["Mon", "Wed"]
    monthly_days: Optional[List[str]] = None  # ["2025-08-30", "2025-09-02"]

    class Config:
        from_attributes = True