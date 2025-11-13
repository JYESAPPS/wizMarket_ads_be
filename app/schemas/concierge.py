from pydantic import BaseModel
from typing import Optional


class IsConcierge(BaseModel):
    store_name: str
    road_address: str

    class Config:
        from_attributes = True