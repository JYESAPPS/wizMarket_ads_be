from app.crud.ads import (
    select_ads_init_info as crud_select_ads_init_info,
    insert_ads as crud_insert_ads,
    insert_ads_image as crud_insert_ads_image,
    delete_status as crud_delete_status,
    update_ads as crud_update_ads,
    update_ads_image as crud_update_ads_image,

)
from app.schemas.ads import(
    AdsInitInfoOutPut, AdsInitInfo, WeatherInfo
)

from fastapi import HTTPException
import logging
import os
from dotenv import load_dotenv
import requests
from openai import OpenAI
import os



logger = logging.getLogger(__name__)
load_dotenv()

# OpenAI API 키 설정
api_key = os.getenv("GPT_KEY")
client = OpenAI(api_key=api_key)


# 초기 데이터 가져오기
def select_ads_init_info(store_business_number: str) -> AdsInitInfoOutPut:
    try:
        raw_data = crud_select_ads_init_info(store_business_number)

        # 최대 매출 요일 계산
        sales_day_columns = [
            ("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_MON", raw_data.commercial_district_average_percent_mon),
            ("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_TUE", raw_data.commercial_district_average_percent_tue),
            ("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_WED", raw_data.commercial_district_average_percent_wed),
            ("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_THU", raw_data.commercial_district_average_percent_thu),
            ("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_FRI", raw_data.commercial_district_average_percent_fri),
            ("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_SAT", raw_data.commercial_district_average_percent_sat),
            ("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_SUN", raw_data.commercial_district_average_percent_sun)
        ]
        # None을 0으로 대체하되, 모두 None인지 확인
        if all(value is None for _, value in sales_day_columns):
            max_sales_day = (None, None)  # 모든 값이 None인 경우
        else:
            # None은 0으로 대체하여 계산
            max_sales_day = max(sales_day_columns, key=lambda x: x[1] or 0)  # (컬럼명, 값)

        # 최대 매출 시간대 계산 
        sales_time_columns = [
            ("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_06_09", raw_data.commercial_district_average_percent_06_09),
            ("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_09_12", raw_data.commercial_district_average_percent_09_12),
            ("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_12_15", raw_data.commercial_district_average_percent_12_15),
            ("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_15_18", raw_data.commercial_district_average_percent_15_18),
            ("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_18_21", raw_data.commercial_district_average_percent_18_21),
            ("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_21_24", raw_data.commercial_district_average_percent_21_24)
        ]
        if all(value is None for _, value in sales_time_columns):
            max_sales_time = (None, None) 
        else:
            max_sales_time = max(sales_time_columns, key=lambda x: x[1] or 0) 

        # 최대 남성 연령대 계산
        male_age_columns = [
            ("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_20S", raw_data.commercial_district_avg_client_per_m_20s),
            ("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_30S", raw_data.commercial_district_avg_client_per_m_30s),
            ("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_40S", raw_data.commercial_district_avg_client_per_m_40s),
            ("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_50S", raw_data.commercial_district_avg_client_per_m_50s),
            ("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_60_OVER", raw_data.commercial_district_avg_client_per_m_60_over)
        ]
        if all(value is None for _, value in male_age_columns):
            max_male_age = (None, None)  
        else:
            max_male_age = max(male_age_columns, key=lambda x: x[1] or 0) 

        # 최대 여성 연령대 계산
        female_age_columns = [
            ("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_20S", raw_data.commercial_district_avg_client_per_f_20s),
            ("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_30S", raw_data.commercial_district_avg_client_per_f_30s),
            ("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_40S", raw_data.commercial_district_avg_client_per_f_40s),
            ("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_50S", raw_data.commercial_district_avg_client_per_f_50s),
            ("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_60_OVER", raw_data.commercial_district_avg_client_per_f_60_over)
        ]
        if all(value is None for _, value in female_age_columns):
            max_female_age = (None, None)  
        else:
            max_female_age = max(female_age_columns, key=lambda x: x[1] or 0) 


        wether_main_temp = get_weather_info_by_lat_lng(raw_data.latitude, raw_data.longitude)
        wether_main = translate_weather_id_to_main(wether_main_temp.id)

        # 결과 반환
        return AdsInitInfoOutPut(
            store_business_number=raw_data.store_business_number,
            store_name=raw_data.store_name,
            road_name=raw_data.road_name,
            city_name=raw_data.city_name,
            district_name=raw_data.district_name,
            sub_district_name=raw_data.sub_district_name,
            latitude = raw_data.latitude,
            longitude = raw_data.longitude,
            detail_category_name=raw_data.detail_category_name,
            loc_info_average_sales_k=raw_data.loc_info_average_sales_k,
            commercial_district_max_sales_day=max_sales_day,  
            commercial_district_max_sales_time=max_sales_time,
            commercial_district_max_sales_m_age=max_male_age,  
            commercial_district_max_sales_f_age=max_female_age,  
            id = wether_main_temp.id,
            main = wether_main,
            temp = wether_main_temp.temp
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Service ads_list Error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Service ads_list Error: {str(e)}"
        )


def get_weather_info_by_lat_lng(
    lat: float, lng: float, lang: str = "kr"
) -> WeatherInfo:
    try:
        apikey = os.getenv("OPENWEATHERMAP_API_KEY")
        if not apikey:
            raise HTTPException(
                status_code=500,
                detail="Weather API key not found in environment variables.",
            )
        api_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={apikey}&lang={lang}&units=metric"
        # logger.info(f"Requesting weather data for lat={lat}, lng={lng}")
        weather_response = requests.get(api_url)
        weather_data = weather_response.json()
        if weather_response.status_code != 200:
            error_msg = (
                f"Weather API Error: {weather_data.get('message', 'Unknown error')}"
            )
            logger.error(error_msg)
            raise HTTPException(
                status_code=weather_response.status_code, detail=error_msg
            )
        weather_info = WeatherInfo(
            id = weather_data["weather"][0]["id"],
            main=weather_data["weather"][0]["main"],
            temp=weather_data["main"]["temp"],
        )
        return weather_info
    except requests.RequestException as e:
        error_msg = f"Failed to fetch weather data: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=503, detail=error_msg)
    except (KeyError, ValueError) as e:
        error_msg = f"Error processing weather data: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"Weather service error: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# 날씨 id 값 따라 한글 번역
def translate_weather_id_to_main(weather_id: int) -> str:
    if 200 <= weather_id < 300:
        return "뇌우"  # Thunderstorm
    elif 300 <= weather_id < 400:
        return "이슬비"  # Drizzle
    elif 500 <= weather_id < 600:
        return "비"  # Rain
    elif 600 <= weather_id < 700:
        return "눈"  # Snow
    elif 700 <= weather_id < 800:
        return "안개"  # Atmosphere (mist, fog, etc.)
    elif weather_id == 800:
        return "맑음"  # Clear
    elif 801 <= weather_id < 900:
        return "구름"  # Clouds
    else:
        return "알 수 없음"  # Unknown case


# DB 저장
def insert_ads(store_business_number: str, use_option: str, title: str, detail_title: str, content: str, image_url: str, final_image_url: str):
    # 글 먼저 저장
    ads_pk = crud_insert_ads(store_business_number, use_option, title, detail_title, content)

    # 글 pk 로 이미지 저장
    crud_insert_ads_image(ads_pk, image_url, final_image_url)

    return ads_pk


# ADS 삭제처리
def delete_status(ads_id: int):
    try:
        # CRUD 레이어에 값을 전달하여 업데이트 작업 수행
        success = crud_delete_status(ads_id)
        if not success:
            raise HTTPException(status_code=404, detail="Content not found for updating")
    except Exception as e:
        print(f"Service error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    


# ADS 수정 처리
def update_ads(store_business_number: str, use_option: str, title: str, detail_title: str, content: str, image_url: str, final_image_url: str):
    # 글 먼저 저장
    ads_id = crud_update_ads(store_business_number, use_option, title, detail_title, content)

    # 글 pk 로 이미지 저장
    crud_update_ads_image(ads_id, image_url, final_image_url)



