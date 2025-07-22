from pydantic import BaseModel
from datetime import datetime

class AdsFaqList(BaseModel):
    category_id: int
    category_name: str
    faq_id: int
    question: str
    answer: str

    class Config:
        from_attributes = True


class AdsTagList(BaseModel):
    name: str

    class Config:
        from_attributes = True


class AdsFAQCreateRequest(BaseModel):
    question: str
    answer: str
    name : str