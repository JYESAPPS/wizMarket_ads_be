from pydantic import BaseModel
from typing import Optional, List,Tuple
from datetime import datetime 
from fastapi import UploadFile, File
from datetime import date


class AdsList(BaseModel):
    local_store_content_id: int
    store_business_number: str
    store_name:str
    road_name:str
    status: str
    title :str
    content :str
    created_at:datetime  

    class Config:
        from_attributes = True


# 등록 모달 창 열 때 기본 정보 가져오기
class AdsInitInfo(BaseModel):
    store_business_number: str
    store_name:str
    road_name:str
    city_name: str
    district_name: str
    sub_district_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    detail_category_name: str
    loc_info_average_sales_k: Optional[float] = None
    commercial_district_average_percent_mon : Optional[float]= None
    commercial_district_average_percent_tue : Optional[float]= None
    commercial_district_average_percent_wed : Optional[float]= None
    commercial_district_average_percent_thu : Optional[float]= None
    commercial_district_average_percent_fri : Optional[float]= None
    commercial_district_average_percent_sat : Optional[float]= None
    commercial_district_average_percent_sun : Optional[float]= None

    commercial_district_average_percent_06_09: Optional[float]= None
    commercial_district_average_percent_09_12: Optional[float]= None
    commercial_district_average_percent_12_15: Optional[float]= None
    commercial_district_average_percent_15_18: Optional[float]= None
    commercial_district_average_percent_18_21: Optional[float]= None
    commercial_district_average_percent_21_24: Optional[float]= None

    commercial_district_avg_client_per_m_20s: Optional[float]= None
    commercial_district_avg_client_per_m_30s: Optional[float]= None
    commercial_district_avg_client_per_m_40s: Optional[float]= None
    commercial_district_avg_client_per_m_50s: Optional[float]= None
    commercial_district_avg_client_per_m_60_over: Optional[float]= None

    commercial_district_avg_client_per_f_20s: Optional[float]= None
    commercial_district_avg_client_per_f_30s: Optional[float]= None
    commercial_district_avg_client_per_f_40s: Optional[float]= None
    commercial_district_avg_client_per_f_50s: Optional[float]= None
    commercial_district_avg_client_per_f_60_over: Optional[float]= None

    class Config:
        from_attributes = True

class RandomImage(BaseModel):
    path: str
    prompt: str
    design_id : int



# 등록 모달 창 열 때 기본 정보 MAX 값으로 내보내기
class AdsInitInfoOutPut(BaseModel):
    store_business_number: str
    store_name: str
    road_name: str
    city_name: str
    district_name: str
    sub_district_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    detail_category_name: str
    loc_info_average_sales_k: Optional[float] = None
    commercial_district_max_sales_day: Optional[Tuple[Optional[str], Optional[float]]] = (None, None)
    commercial_district_max_sales_time: Optional[Tuple[Optional[str], Optional[float]]] = (None, None)
    commercial_district_max_sales_m_age: Optional[Tuple[Optional[str], Optional[float]]] = (None, None)
    commercial_district_max_sales_f_age: Optional[Tuple[Optional[str], Optional[float]]] = (None, None)
    id : int
    main: Optional[str] = None
    temp: Optional[float] = None






# 날씨 조회
class WeatherInfo(BaseModel):
    id: int
    main: str
    temp: float

    class Config:
        from_attributes = True


class LocalStoreInfoWeaterInfoOutput(BaseModel):
    localStoreInfo: AdsInitInfoOutPut
    weatherInfo: WeatherInfo

    class Config:
        from_attributes = True

class InstaAccount(BaseModel):
    posts: int
    followers: int
    following: int


class AdsInitInfoOutPutWithImages(BaseModel):
    store_business_number: str
    store_name: str
    road_name: str
    city_name: str
    district_name: str
    sub_district_name: str
    latitude: float
    longitude: float
    detail_category_name: str
    loc_info_average_sales_k: float
    commercial_district_max_sales_day: tuple | None
    commercial_district_max_sales_time: tuple | None
    commercial_district_max_sales_m_age: tuple | None
    commercial_district_max_sales_f_age: tuple | None
    id: int
    main: str
    temp: float
    image_list: List[RandomImage]  # ✅ 여기에 추가
    all_image_list: List[RandomImage]
    insta_info: Optional[InstaAccount] = None  # ← 추가

# 문구 생성
class AdsContentRequest(BaseModel):
    prompt : str
    gpt_role: str
    detail_content: str




# 광고 채널 추천용
class AdsSuggestChannelRequest(BaseModel):
    male_base:str
    female_base:str
    store_name: str
    road_name: str
    tag: str
    title: str


# 프론트에서 이미지 처리 테스트용
class AdsImageTestFront(BaseModel):
    male_base:str
    female_base:str
    store_name: str
    road_name: str
    tag: str
    weather: str
    temp: float
    gpt_role: str
    detail_content: Optional[str]







# 시드 이미지 전달 테스트
class AdsTemplateSeedImage(BaseModel):
    gpt_role: str
    weather: str
    temp: float
    male_base: str
    female_base: str
    store_name: str
    road_name: str
    tag: str
    use_option: str
    title: str
    ai_model_option: str
    seed_prompt : str
    detail_content: Optional[str]
    example_image: str


# 테스트 문구 생성
class AdsContentNewRequest(BaseModel):
    role : str
    prompt : str




class AdsGenerateContentOutPut(BaseModel):
    content: str


# 이미지 모델 테스트
class AdsDrawingModelTest(BaseModel):
    prompt : str
    version: str
    ratio : str


# 이미지 모델 테스트
class MidTest(BaseModel):
    prompt : str
    ratio : str



# 이미지 생성
class AdsImageRequest(BaseModel):
    use_option: str
    ai_model_option: str
    ai_prompt: str
    ai_mid_prompt: str
    

class AdsGenerateImageOutPut(BaseModel):
    image: Optional[list] = None



# ADS 삭제
class AdsDeleteRequest(BaseModel):
    ads_id : int



class AdsSpecificInitInfo(BaseModel):
    use_option: str
    title: str
    content: str
    store_business_number:str

    class Config:
        from_attributes = True

class AdsSpecificInitImage(BaseModel):
    ads_final_image_url: Optional[str]

    class Config:
        from_attributes = True

class AdsSpecificInitStoreName(BaseModel):
    store_name: Optional[str]

    class Config:
        from_attributes = True

# 유튜브 인증
class AuthCallbackRequest(BaseModel):
    code: str





# 카카오 임시 저장
class KaKaoTempInsert(BaseModel):
    title: str
    content: str
    storeName: str
    roadName: str
    imageUrl: str

# 카카오 임시 저장 데이터 불러오기
class KaKaoTempGet(BaseModel):
    share_id: str

# 음악 생성 데이터 불러오기
class MusicGet(BaseModel):
    taskId: str


class Story(BaseModel):
    story_role: str
    example_image: str


