from pydantic import BaseModel
from typing import Optional, List,Tuple, Union
from datetime import datetime 
from fastapi import UploadFile, File
from datetime import date


class ImageItem(BaseModel):
    path: str

class AutoApp(BaseModel):
    store_business_number: str
    city_name: str
    district_name: str
    sub_district_name: str
    road_name: str
    latitude: float
    longitude: float

    store_name: str
    detail_category_name: str

    commercial_district_max_sales_day: Optional[List[Optional[Union[str, float]]]] = None
    commercial_district_max_sales_f_age: Optional[List[Optional[Union[str, float]]]] = None
    commercial_district_max_sales_m_age: Optional[List[Optional[Union[str, float]]]] = None
    commercial_district_max_sales_time: Optional[List[Optional[Union[str, float]]]] = None
    loc_info_average_sales_k:Optional[int]
    
    main: str
    temp: float
    
    id: int
    image_list: List[ImageItem]
    
    
    
    
    
    
    

