from pydantic import BaseModel
from typing import Optional, List,Tuple, Union
from datetime import datetime 
from fastapi import UploadFile, File
from datetime import date


class ImageItem(BaseModel):
    path: str


class ImageItemMain(BaseModel):
    path: str
    design_id : int
    prompt : str

class ImageUploadRequest(BaseModel):
    image_base64: str


class StoreInfo(BaseModel):
    store_business_number: str


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
    register_tag: str

    commercial_district_max_sales_day: Optional[List[Optional[Union[str, float]]]] = None
    commercial_district_max_sales_f_age: Optional[List[Optional[Union[str, float]]]] = None
    commercial_district_max_sales_m_age: Optional[List[Optional[Union[str, float]]]] = None
    commercial_district_max_sales_time: Optional[List[Optional[Union[str, float]]]] = None
    loc_info_average_sales_k:Optional[int]
    
    main: str
    temp: float
    
    id: int
    image_list: List[ImageItem]


class AutoAppMain(BaseModel):
    store_business_number: str
    city_name: str
    district_name: str
    sub_district_name: str
    road_name: str
    latitude: float
    longitude: float

    store_name: str
    # custom_menu: Optional[str] = None
    register_tag: Optional[str] = None
    detail_category_name: str

    commercial_district_max_sales_day: Optional[List[Optional[Union[str, float]]]] = None
    commercial_district_max_sales_f_age: Optional[List[Optional[Union[str, float]]]] = None
    commercial_district_max_sales_m_age: Optional[List[Optional[Union[str, float]]]] = None
    commercial_district_max_sales_time: Optional[List[Optional[Union[str, float]]]] = None
    loc_info_average_sales_k:Optional[int]
    
    main: str
    temp: float


    image_list: ImageItemMain

    ai_age : str
    ai_data: Optional[List[int]] = None
    user_id: Optional[int] = None

    


class AutoAppRegen(BaseModel):
    store_business_number: str
    store_name: str
    detail_category_name: str
    custom_menu: Optional[str] = None
    register_tag: Optional[str] = None
    road_name: str
    district_name: str

    style:str
    channel : str
    age : Optional[str]
    prompt : str
    title : str
    ad_text: Optional[str]

    main: str
    temp: float


class AutoAppSave(BaseModel):
    age: str
    alert_check: bool
    channel : str
    repeat : str
    style : str
    title : str
    upload_time : Optional[str]
    user_id : int
    date_range: List[str] 
    image: str | None = None
    type: str



class AutoGenCopy(BaseModel):
    category: str
    title: str
    store_name : str
    main: str
    temp: float
    road_name : str


class ManualGenCopy(BaseModel):
    category: str
    age: str
    channel: str
    subChannel: Optional[str]
    theme: str
    store_name : str
    main: str
    temp: float
    road_name : str


class EventGenCopy(BaseModel):
    category: str
    # age: str
    # channel: str
    # subChannel: Optional[str]
    # resister_tag: str
    theme: str
    store_name : str
    weather: str
    temp: float
    road_name : str
    custom_text: Optional[str] = None
    

class ManualImageListAIReco(BaseModel):
    category: Optional[str]
    age: str
    channel: str
    subChannel: Optional[str]
    customText: Optional[str]
    customMenu: Optional[str]
    theme: str
    store_name : str
    road_name : str
    detail_category_name : str


class ManualApp(BaseModel):
    store_business_number: str
    prompt : str
    main: str
    temp: float
    style : int
    category: Optional[str]
    age: str
    channel: str
    subChannel: Optional[str]
    customText: Optional[str]
    customMenu: Optional[str]
    theme: str
    store_name : str
    road_name : str
    district_name: str
    detail_category_name : str

    
class UserInfo(BaseModel):
    userId : str
    register_tag: Optional[str] = None

class UserInfoInsert(BaseModel):
    user_id: Optional[str] = None
    birth_year: Optional[int] = None
    gender: Optional[str] = None
    nickname: Optional[str] = None
    phone: Optional[str] = None
    profile_image: Optional[str] = None
    custom_menu: Optional[str] = None
    insta_account: Optional[str] = None
    kakao_account: Optional[str] = None
    blog_account: Optional[str] = None
    band_account: Optional[str] = None
    x_account: Optional[str] = None
    address: Optional[str] = None

class UserInfoUpdate(BaseModel):
    user_id: Optional[str] = None
    birth_year: Optional[int] = None
    gender: Optional[str] = None
    nickname: Optional[str] = None
    phone: Optional[str] = None
    profile_image: Optional[str] = None
    register_tag: Optional[str] = None
    insta_account: Optional[str] = None
    kakao_account: Optional[str] = None
    blog_account: Optional[str] = None
    band_account: Optional[str] = None
    x_account: Optional[str] = None
    address: Optional[str] = None


class UserRecentRecord(BaseModel):
    user_id : str
    type : str

class UserRecoUpdate(BaseModel):
    user_id: str
    alert_check: bool
    start_date: str
    end_date: str
    repeat_time: str
    user_record_id: int

class UserRecoDelete(BaseModel):
    user_id: str
    user_record_id: int

class ImageList(BaseModel):
    detail_category_name: str