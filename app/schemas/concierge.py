from pydantic import BaseModel
from typing import Optional


class IsConcierge(BaseModel):
    store_name: str
    road_address: str

    class Config:
        from_attributes = True


class AddConciergeStore(BaseModel):
    user_id : int
    road_name : str
    store_name: str 

    large_category_code: str 
    medium_category_code: str 
    small_category_code: str

    menu_1: str


class ConciergeUploadRequest(BaseModel):
    image: str  # data:image/png;base64,... or 순수 base64