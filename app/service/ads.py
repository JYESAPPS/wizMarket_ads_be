from app.crud.ads import (
    select_ads_init_info as crud_select_ads_init_info,
    select_custom_menu as crud_select_custom_menu,
    insert_ads as crud_insert_ads,
    insert_ads_image as crud_insert_ads_image,
    delete_status as crud_delete_status,
    update_ads as crud_update_ads,
    update_ads_image as crud_update_ads_image,
    random_image_list as crud_random_image_list,
    get_category_id as crud_get_category_id,
    update_popup as crud_update_popup,
    update_re_popup as crud_update_re_popup,
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
from datetime import datetime
import re

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


# 유저가 설정한 커스텀 메뉴 가져오기
def select_custom_menu(user_id):
    register_tag, custom_menu = crud_select_custom_menu(user_id)
    return register_tag, custom_menu


# 카테고리 별 랜덤 이미지 가져오기
def random_design_style(init_info, design_id):


    category_id = crud_get_category_id(init_info.detail_category_name)
    random_image_list = crud_random_image_list(category_id, design_id)
    return random_image_list


# 나이 값 추천 or 꺼내기
def select_ai_age(init_info, custom_menu):
    age_tuple = init_info.commercial_district_max_sales_f_age
    age_map = {
        "COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_10S": "10대",
        "COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_20S": "20대",
        "COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_30S": "30대",
        "COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_40S": "40대",
        "COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_50S": "50대",
        "COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_60_OVER": "60대 이상",
    }
    if not age_tuple or age_tuple[0] is None:
        gpt_content = f''' 
            당신은 온라인 광고 콘텐츠 기획자입니다. 아래 조건을 바탕으로 SNS 또는 디지털 홍보에 적합한 콘텐츠를 제작하려고 합니다.
            현재 계절과 요일, 날짜 및 세부업종을 반영하여 주고객층을 선택 후 숫자 하나만 답해주세요.
            
            ex) 1
        '''
        formattedToday = datetime.today().strftime("%Y-%m-%d")
        
        content = f"""[매장 정보]  
        - 매장명: {init_info.store_name}  
        - 업종: {init_info.detail_category_name} 
        - 세부 업종: {custom_menu}
        - 주소: {init_info.road_name}
        - 일시: {formattedToday}


        [연령대]
        1. 10대 2. 20대 3. 30대 4. 40대 5. 50대 6. 60대 이상

        """

        client = OpenAI(api_key=os.getenv("GPT_KEY"))
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": gpt_content},
                {"role": "user", "content": content},
            ],
        )
        report = completion.choices[0].message.content.strip()
        match = re.search(r"\d+", report)
        number = match.group() if match else None

        number_to_age = {
            "1": "10대",
            "2": "20대",
            "3": "30대",
            "4": "40대",
            "5": "50대",
            "6": "60대 이상",
        }
        return number_to_age.get(number, "기타")
    
    return age_map.get(age_tuple[0], "기타")


# 초기 AI 추천 값 가져오기
def select_ai_data(init_info, ai_age, custom_menu):

    # design_map = {
    #     1: "3D감성",
    #     2: "포토실사",
    #     3: "캐릭터/만화",
    #     4: "레트로",
    #     5: "AI모델",
    #     6: "예술",
    # }

    # channel_map = {
    #     1: "카카오톡",
    #     2: "인스타그램 스토리",
    #     3: "안스타그램 피드",
    #     4: "네이버 블로그"
    # }

    # day_map = {
    #     1: "월요일",
    #     2: "화요일",
    #     3: "수요일",
    #     4: "목요일",
    #     5: "금요일",
    #     6: "토요일",
    #     7: "일요일",
    # }

    # time_map = {
    #     1: "오전",
    #     2: "점심",
    #     3: "오후",
    #     4: "저녁",
    #     5: "밤",
    #     6: "심야",
    #     7: "새벽",
    # }

    
    gpt_content = f''' 
        - 연령대별 행동패턴인자,업종별 행동패턴 인자, 해당지역 최고 인구분포 {ai_age}, 주요고객 {ai_age}를 참고
        - 현재 계절과 요일, 날짜, 세부업종을 반영하여 주고객층을 선별하고 오늘 어떤 마케팅을 하면 좋을지 아래 조건대로 추천해주세요.
        - 단, 특정 시즌/기념일(예: 발렌타인데이 2월 14일, 화이트데이 3월14일, 블랙데이 4월14일, 빼빼로데이 11월 11일, 크리스마스 12월 25일, 추석, 설날 등) 에는 이벤트 선택
        - 매장 홍보 / 상품 소개 / 이벤트 / 감사 인사: 연말, 설날, 추석 인사 콘텐츠
         디자인 선호 스타일, 카피문구 선호 스타일, 자주 이용하는 채널, 홍보 주제, 매장 방문 선호 요일, 매장 방문 선호 시간대 선택 후 
        숫자로만 답해주세요.
        대답은 숫자 조합으로만 해주세요
        ex) 5, 4, 1, 1, 6, 4
    '''
    formattedToday = datetime.today().strftime("%Y-%m-%d")
    
    content = f"""[매장 정보]  
    - 매장명: {init_info.store_name}  
    - 업종: {init_info.detail_category_name} 
    - 세부 업종: {custom_menu}
    - 주소: {init_info.road_name}
    - 일시: {formattedToday}

    [디자인 스타일]  
    ※ 고객층에 적합한 하나의 카테고리 선택 
    - 1. 3D감성 2. 포토실사 5. AI모델 6. 예술 

    [카피문구 스타일]  
    - 1. 설명중심 2. 스토리중심 3. 유행어 4. 품격 5. 전문용어 6. 단축어(급식체) 7. 농담, 8. 영어, 9. 감성, 10. 개조식, 11. 경어체, 12. 반말체, 13. 대화체, 14. 한자성어, 15. 문답체 

    [채널]  
    ※ 고객층에 적합한 채널 1개 선택 
    1. 카카오톡 2. 인스타 스토리 3. 인스타 게시물 6. 네이버 밴드

    [홍보 주제]  
    ※ 아래 중 하나를 조건에 따라 선택. 
    - 단, 특정 시즌/기념일 이벤트(예: 발렌타인데이 2월 14일, 화이트데이 3월14일, 블랙데이 4월14일, 빼빼로데이 11월 11일, 크리스마스 12월 25일, 추석, 설날 등)엔 이벤트 선택
    1. 매장 홍보 2. 상품 소개 3. 이벤트 

    [선호 요일]  
    ※ 고객층에 적합한 요일 1개 선택 
    1. 월 2. 화 3. 수 4. 목 5. 금 6. 토 7. 일 

    [선호 시간대]  
    ※ 고객층에 적합한 시간대 1개 선택 
    1. 오전 2. 점심 3. 오후 4. 저녁 5. 밤 6. 심야 7.새벽
    """

    client = OpenAI(api_key=os.getenv("GPT_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": gpt_content},
            {"role": "user", "content": content},
        ],
    )
    report = completion.choices[0].message.content

    numbers = re.findall(r"\d+", report) 
    selected = list(map(int, numbers))

    if not selected:
        selected = [4, 4, 1, 1, 6, 4]
    
    if selected[0] > 6 or selected[0] < 1:
        selected[0] = 1

    if not 1 <= selected[2] <= 3:
        selected[2] = 1
    
    if not 1 <= selected[3] <= 3:
        selected[3] = 1

    init_ai_reco = selected

    # design_text = design_map.get(init_ai_reco[0])
    # channel_text = channel_map.get(init_ai_reco[2])
    # day_text = day_map.get(init_ai_reco[4], "정보 없음")
    # time_text = time_map.get(init_ai_reco[5], "정보 없음")

    # gpt_content = f''' 
    #     매장명의 현재 계절, 날씨, 주고객층, 세부업종을 반영하여 오늘 어떤 마케팅을 하면 좋을지 추천해주세요. 문장은 다음과 같이 짧게 한 문장으로 해주세요.
    #     - 날씨, 주 고객층에게 채널 이름과 디자인 스타일을 언급하며 마케팅해보세요 라는 말로 끝나게끔 해주세요.
    # '''

    # content = f"""[매장 정보]  
    #     - 매장명: {init_info.store_name}  
    #     - 업종: {init_info.detail_category_name} 
    #     - 주소: {init_info.road_name}
    #     - 일시: {formattedToday}
    #     - 고객 층 : {ai_age}
    #     - 선호 채널 : {channel_text}
    #     - 선호 디자인 : {design_text}
    #     - 날씨 : {init_info.main}, {init_info.temp}도
    #     - 최고 매출 요일 : {day_text}
    #     - 최고 매출 시간 : {time_text}
    # """

    # client = OpenAI(api_key=os.getenv("GPT_KEY"))
    # completion = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[
    #         {"role": "system", "content": gpt_content},
    #         {"role": "user", "content": content},
    #     ],
    # )
    # today_tip = completion.choices[0].message.content

    return init_ai_reco






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


def update_popup(user_id: int, popup: bool):
    crud_update_popup(user_id, popup)

def update_re_popup(user_id: int, re_popup: bool):
    crud_update_re_popup(user_id, re_popup)
