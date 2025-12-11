from pydantic import BaseModel
from typing import Optional, List


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



class ConciergeExcelRow(BaseModel):
    # 프론트에서 오는 키 그대로(camelCase) 받아도 되고,
    # snake_case로 받으려면 프론트에서 맞춰주면 됨.
    name: Optional[str] = ""
    phone: Optional[str] = ""
    store_name: Optional[str] = ""   # 가게 이름
    road_name: Optional[str] = ""    # 도로명 주소
    menu_1: Optional[str] = ""
    menu_2: Optional[str] = ""
    menu_3: Optional[str] = ""
    blog: Optional[str] = ""
    instagram : Optional[str] = ""
    reco_product : Optional[str] = ""
    reco_reason : Optional[str] = ""
    expect_effect : Optional[str] = ""
    additional_suggest : Optional[str] = ""


class ConciergeExcelUploadRequest(BaseModel):
    rows: List[ConciergeExcelRow]


# 삭제 요청
class ConciergeDeleteRequest(BaseModel):
    ids: List[int]