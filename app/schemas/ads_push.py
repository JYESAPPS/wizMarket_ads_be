from pydantic import BaseModel
from typing import Optional
from datetime import date

class PushRequest(BaseModel):
    token: str
    title: str
    body: str


class AllUserDeviceToken(BaseModel):
    user_id: int
    device_token: Optional[str] = None 

    class Config:
        from_attributes = True



class UserReserve(BaseModel):
    user_id: int
    start_date: date
    end_date: date
    upload_times: str
    repeat_type: str
    weekly_days: Optional[str] = None
    monthly_days: Optional[str] = None