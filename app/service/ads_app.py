from datetime import datetime
import logging
import os
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
from runwayml import RunwayML
from moviepy import *
from google import genai
from google.genai import types
from io import BytesIO
from app.crud.ads_app import (
    select_random_image as crud_select_random_image,
    get_style_image as crud_get_style_image,
    insert_upload_record as crud_insert_upload_record,
    get_user_info as crud_get_user_info,
    get_user_record as crud_get_user_record,
    get_user_record_this_month as crud_get_user_record_this_month,
    get_user_profile as crud_get_user_profile,
    update_user_info as crud_update_user_info,
    get_user_recent_reco as crud_get_user_recent_reco,
    update_user_reco as crud_update_user_reco,
    delete_user_reco as crud_delete_user_reco
)
from app.crud.ads import (
    get_category_id as crud_get_category_id
)
import base64
from datetime import datetime
from io import BytesIO
import traceback
import io
from fastapi.responses import StreamingResponse
from rembg import remove
import requests
import json
import random


logger = logging.getLogger(__name__)
load_dotenv()

# OpenAI API 키 설정
api_key = os.getenv("GPT_KEY")
client = OpenAI(api_key=api_key)

today = datetime.now()
formattedToday = today.strftime('%Y-%m-%d')

# 남녀 비중 풀어서
def parse_age_gender_info(age_info):
    if not age_info or len(age_info) != 2 or not all(age_info):
        return ""
    
    column, percentage = age_info

    gender = "남자" if "_M_" in column else "여자"

    # 나이 추출 로직
    age_part = column.split("_")[-2:]  # 예: ['60', 'OVER']
    if age_part == ['60', 'OVER']:
        age = "60대"
    else:
        age_raw = age_part[-1]  # '50S'
        age = age_raw.replace("S", "대")

    return f"{gender} {age} ({percentage}%)"


# 옵션 값들 자동 선택 - 성별 값 있음
def generate_option(request):
    

    male_text = parse_age_gender_info(request.commercial_district_max_sales_m_age)
    female_text = parse_age_gender_info(request.commercial_district_max_sales_f_age)

    gpt_role = f''' 
        당신은 온라인 광고 콘텐츠 기획자입니다. 아래 조건을 바탕으로 SNS 또는 디지털 홍보에 적합한 콘텐츠를 제작하려고 합니다.
        홍보 주제, 채널, 디자인 스타일을 선택 후 숫자로만 답해주세요.
        대답은 숫자 조합으로만 해주세요
        ex) 1, 2, 4
    '''
    copyright_prompt = f'''
        1) [기본 정보]  
        - 매장명: {request.store_name}  
        - 업종: {request.detail_category_name} 
        - 주소: {request.road_name}
        - 주요 고객층: {male_text}, {female_text}
        - 일시: {formattedToday}

        [홍보 주제]  
        ※ 아래 중 하나를 조건에 따라 선택. 
        - 단, 특정 시즌/기념일 이벤트 (예: 발렌타인데이, 할로윈 데이, 크리스마스 등) 엔 이벤트만 선택하고 연말, 설날, 추석에만 감사인사를 선택 그외의 날짜엔 선택하지 않음
        1. 매장 홍보 2. 상품 소개 3. 이벤트 

        [채널]  
        ※ 고객층에 적합한 채널 1개 선택 
        1. 카카오톡 2. 인스타그램 스토리 3. 인스타그램 피드 

        [디자인 스타일]  
        ※ 고객층에 적합한 하나의 카테고리 선택 
        - 1. 3D감성 2. 포토실사 3. 캐릭터/만화 4. 레트로 5. AI모델 6. 예술 
        
    '''
    # print(copyright_prompt)

    # gpt 영역
    gpt_content = gpt_role
    content = copyright_prompt
    client = OpenAI(api_key=os.getenv("GPT_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": gpt_content},
            {"role": "user", "content": content},
        ],
    )
    report = completion.choices[0].message.content
    return report


# 옵션 값들 자동 선택 - 성별 값 없음
def generate_option_without_gender(request):
    

    gpt_role = f''' 
        당신은 온라인 광고 콘텐츠 기획자입니다. 아래 조건을 바탕으로 SNS 또는 디지털 홍보에 적합한 콘텐츠를 제작하려고 합니다.
        홍보 주제, 채널, 연령대, 디자인 스타일을 하나씩 만 선택 후 숫자로만 답해주세요.
        대답은 숫자 조합으로만 해주세요
        ex) 1, 2, 4, 4
    '''
    copyright_prompt = f'''
        1) [기본 정보]  
        - 매장명: {request.store_name}  
        - 업종: {request.detail_category_name} 
        - 주소: {request.road_name}
        - 일시: {formattedToday}

        [홍보 주제]  
        ※ 아래 중 하나를 조건에 따라 선택. 
        - 단, 특정 시즌/기념일 이벤트 (예: 발렌타인데이, 할로윈 데이, 크리스마스 등) 엔 이벤트만 선택하고 연말, 설날, 추석에만 감사인사를 선택 그외의 날짜엔 선택하지 않음
        1. 매장 홍보 2. 상품 소개 3. 이벤트 

        [연령대]
        1. 10대 2. 20대 3. 30대 4. 40대 5. 50대 6. 60대 이상

        [채널]  
        ※ 고객층에 적합한 채널 1개 선택 
        1. 카카오톡 2. 인스타그램 스토리 3. 인스타그램 피드 

        [디자인 스타일]  
        ※ 고객층에 적합한 하나의 카테고리 선택 
        - 1. 3D감성 2. 포토실사 3. 캐릭터/만화 4. 레트로 5. AI모델 6. 예술 
        
    '''
    # print(copyright_prompt)

    # gpt 영역
    gpt_content = gpt_role
    content = copyright_prompt
    client = OpenAI(api_key=os.getenv("GPT_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": gpt_content},
            {"role": "user", "content": content},
        ],
    )
    report = completion.choices[0].message.content
    return report




# 선택 된 스타일 값에서 랜덤 이미지 뽑기
def select_random_image(style):
    seed_prompt=crud_select_random_image(style)
    return seed_prompt

# 주어진 시드 프롬프트로 해당하는 이미지 생성
def generate_by_seed_prompt(channel, copyright, detail_category_name, seed_prompt):
    try:
        # gpt 영역
        gpt_role = f"""
            You are a professional prompt writing expert.
        """

        gpt_content = f"""
            프롬프트 스타일 : {seed_prompt}
            주어진 프롬프트 스타일은 유지하며 {copyright}와 {detail_category_name}에 맞게 내용만 바꿔 영문 프롬프트를 작성해주세요.
        """    
        # print(f"시드 프롬프트 : {seed_image_prompt}")

        content = gpt_content
        client = OpenAI(api_key=os.getenv("GPT_KEY"))
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": gpt_role},
                {"role": "user", "content": content},
            ],
        )
        tag_image_prompt = completion.choices[0].message.content
        # print(f"생성 프롬프트 : {tag_image_prompt}")

    except Exception as e:
        return {"error": f"seed 프롬프트 변경 중 오류 발생: {e}"}
    try:
        channel = int(channel) 

        if channel in [1, 2]:
            size = "9:16"
            resize_size = (1024, 1792)
        else :
            size = "1:1"
            resize_size = (1024, 1024)

        key = os.getenv("IMAGEN3_API_SECRET")
        client = genai.Client(api_key=key)
        # Prompt 전달 및 이미지 생성
        response = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=tag_image_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=size,  # 비율 유지
                output_mime_type='image/jpeg'
            )
        )
        # 이미지 열기 및 최종 리사이징
        img_parts = []
        for generated_image in response.generated_images:
            img = Image.open(BytesIO(generated_image.image.image_bytes))

            # 🔥 생성된 후, 최종 크기로 리사이징
            img_resized = img.resize(resize_size, Image.LANCZOS)  # 고품질 리사이징
            img_parts.append(img_resized)

        return img_parts

    except Exception as e:
        return {"error": f"이미지 생성 중 오류 발생: {e}"}
    
# 모든 이미지 리스트 가져오기
def get_style_image(request):
    id = crud_get_category_id(request.detail_category_name)
    image_list = crud_get_style_image(id)
    return image_list

# AI 생성 자동 - 저장
def insert_upload_record(request):
    user_id = request.user_id
    age = request.age
    alert_check = request.alert_check
    data_range = request.date_range
    repeat = request.repeat
    style = request.style
    title = request.title
    channel = request.channel
    upload_time = request.upload_time
    upload_type = request.type

    image_path = save_base64_image(request.image, request.user_id, request.channel)

    success = crud_insert_upload_record(
        user_id,
        age,
        alert_check,
        data_range,
        repeat,
        style,
        title,
        channel,
        upload_time,
        image_path,
        upload_type
    )
    return success

# 이미지 파일 저장 및 경로 설정
def save_base64_image(base64_str, user_id: int, channel_code: str, save_dir="app/uploads/image/user"):
    from datetime import datetime
    import os, base64

    # 채널 매핑
    channel_map = {
        "1": "kakao",
        "2": "story",
        "3": "feed"
    }
    channel_name = channel_map.get(channel_code, "unknown")

    # 저장 디렉토리 생성
    user_folder = f"user_{user_id}"
    full_dir = os.path.join(save_dir, user_folder)
    os.makedirs(full_dir, exist_ok=True)

    # 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{user_id}_{channel_name}_{timestamp}.png"
    file_path = os.path.join(full_dir, filename)

    # base64 디코딩 후 저장
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]

    with open(file_path, "wb") as f:
        f.write(base64.b64decode(base64_str))

    # 리턴용 URL 생성 (로컬 저장 경로 → URL 경로 변환)
    relative_path = file_path.replace("app/", "")  # ex) uploads/image/user/user_1/xxx.png
    url_path = f"http://221.151.48.225:58002/{relative_path.replace(os.sep, '/')}"
    
    return url_path


# AI 생성 수동 - 이미지 리스트와 추천 값 가져오기
def get_style_image_ai_reco(request):

    menu = request.category

    if request.category == '' : 
        menu = request.customMenu

    gpt_role = f''' 
        당신은 온라인 광고 콘텐츠 기획자입니다. 아래 조건을 바탕으로 SNS 또는 디지털 홍보에 적합한 콘텐츠를 제작하려고 합니다.
        디자인 스타일을 선택 후 숫자로만 답해주세요.
        ex) 1, 2, 4
    '''
    copyright_prompt = f'''
        1) [기본 정보]  
        - 매장명: {request.store_name}  
        - 업종: {menu} 
        - 주소: {request.road_name}
        - 주요 고객층: {request.age}
        - 일시: {formattedToday}
        - 홍보 주제 : {request.theme}
        - 업로드 채널 : {request.channel} + {request.subChannel}

        [디자인 스타일]  
        ※ 고객층에 적합한 하나의 카테고리 선택 
        - 1. 3D감성 2. 포토실사 3. 캐릭터/만화 4. 레트로 5. AI모델 6. 예술 
    '''
    # gpt 영역
    gpt_content = gpt_role
    content = copyright_prompt
    client = OpenAI(api_key=os.getenv("GPT_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": gpt_content},
            {"role": "user", "content": content},
        ],
    )
    report = completion.choices[0].message.content

    return report


# 마이페이지용 유저 기본 정보 가져오기
def get_user_info(user_id):
    info = crud_get_user_info(user_id)
    record = crud_get_user_record(user_id)

    return info, record

# 달력용 이번달 포스팅 기록 가져오기
def get_user_reco(user_id):
    record = crud_get_user_record_this_month(user_id)

    return record

# 메인 페이지용 프로필 이미지 가져오기
def get_user_profile(user_id):
    profile_image = crud_get_user_profile(user_id)
    return profile_image

# 유저 정보 업데이트
def update_user_info(user_id, request):
    try:
        profile_base64 = request.profile_image

        # 이미지 저장 경로 설정
        folder_path = f"app/uploads/image/user/user_{user_id}/profile"
        image_path = os.path.join(folder_path, f"{user_id}_profile.png")

        # 폴더 생성
        os.makedirs(folder_path, exist_ok=True)

        # 기존 이미지 삭제
        if os.path.exists(image_path):
            os.remove(image_path)

        # base64 이미지 처리
        if profile_base64 and profile_base64.startswith("data:image"):
            header, encoded = profile_base64.split(",", 1)
            encoded = encoded.replace(" ", "+")
            image_data = base64.b64decode(encoded)

            with open(image_path, "wb") as f:
                f.write(image_data)

        # ✅ 사용자 정보 DB 업데이트
        success = crud_update_user_info(user_id, request)
        return success

    except Exception:
        return False

# 유저 최근 포스팅 기록 가져오기 3개
def get_user_recent_reco(request):
    reco_list = crud_get_user_recent_reco(request)
    return reco_list


# 유저 기록 게시물 1개 업데이트
def update_user_reco(user_id, request):
    success = crud_update_user_reco(user_id, request)
    return success

# 유저 기록 게시물 1개 삭제 처리
def delete_user_reco(user_id, request):
    success = crud_delete_user_reco(user_id, request)
    return success


# AI 생성 수동 카메라 - AI 추천 받기
def get_manual_ai_reco(request):
    male_text = parse_age_gender_info(request.commercial_district_max_sales_m_age)
    female_text = parse_age_gender_info(request.commercial_district_max_sales_f_age)

    gpt_role = f''' 
        당신은 온라인 광고 콘텐츠 기획자입니다. 아래 조건을 바탕으로 SNS 또는 디지털 홍보에 적합한 콘텐츠를 제작하려고 합니다.
        홍보 주제, 채널, 디자인 스타일을 선택 후 숫자로만 답해주세요.
        대답은 숫자 조합으로만 해주세요
        ex) 1, 2, 4
    '''
    copyright_prompt = f'''
        1) [기본 정보]  
        - 매장명: {request.store_name}  
        - 업종: {request.detail_category_name} 
        - 주소: {request.road_name}
        - 주요 고객층: {male_text}, {female_text}
        - 일시: {formattedToday}

        [홍보 주제]  
        ※ 아래 중 하나를 조건에 따라 선택. 
        - 단, 특정 시즌/기념일 이벤트 (예: 발렌타인데이, 할로윈 데이, 크리스마스 등) 엔 이벤트만 선택하고 연말, 설날, 추석에만 감사인사를 선택 그외의 날짜엔 선택하지 않음
        1. 매장 홍보 2. 상품 소개 3. 이벤트 

        [채널]  
        ※ 고객층에 적합한 채널 1개 선택 
        1. 카카오톡 2. 인스타그램 스토리 3. 인스타그램 피드 

        [디자인 스타일]  
        ※ 고객층에 적합한 하나의 카테고리 선택 
        - 1. 사진 원본 2. 배경만 제거 3. 배경 AI변경

    '''
    # print(copyright_prompt)

    # gpt 영역
    gpt_content = gpt_role
    content = copyright_prompt
    client = OpenAI(api_key=os.getenv("GPT_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": gpt_content},
            {"role": "user", "content": content},
        ],
    )
    report = completion.choices[0].message.content
    return report


# AI 생성 수동 카메라 - AI 추천 받기 - 성별 값 없음
def get_manual_ai_reco_without_gender(request):
    gpt_role = f''' 
        당신은 온라인 광고 콘텐츠 기획자입니다. 아래 조건을 바탕으로 SNS 또는 디지털 홍보에 적합한 콘텐츠를 제작하려고 합니다.
        홍보 주제, 채널, 연령대, 디자인 스타일을 하나씩 만 선택 후 숫자로만 답해주세요.
        대답은 숫자 조합으로만 해주세요
        ex) 1, 2, 4, 4
    '''
    copyright_prompt = f'''
        1) [기본 정보]  
        - 매장명: {request.store_name}  
        - 업종: {request.detail_category_name} 
        - 주소: {request.road_name}
        - 일시: {formattedToday}

        [홍보 주제]  
        ※ 아래 중 하나를 조건에 따라 선택. 
        - 단, 특정 시즌/기념일 이벤트 (예: 발렌타인데이, 할로윈 데이, 크리스마스 등) 엔 이벤트만 선택하고 연말, 설날, 추석에만 감사인사를 선택 그외의 날짜엔 선택하지 않음
        1. 매장 홍보 2. 상품 소개 3. 이벤트 

        [채널]  
        ※ 고객층에 적합한 채널 1개 선택 
        1. 카카오톡 2. 인스타그램 스토리 3. 인스타그램 피드 

        [연령대]
        1. 10대 2. 20대 3. 30대 4. 40대 5. 50대 6. 60대 이상

        [디자인 스타일]  
        ※ 고객층에 적합한 하나의 카테고리 선택 
        - 1. 사진 원본 2. 배경만 제거 3. 배경 AI변경

    '''
    # print(copyright_prompt)

    # gpt 영역
    gpt_content = gpt_role
    content = copyright_prompt
    client = OpenAI(api_key=os.getenv("GPT_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": gpt_content},
            {"role": "user", "content": content},
        ],
    )
    report = completion.choices[0].message.content
    return report





def generate_template_manual_camera():
    pass


# 이미지 배경 제거
def generate_image_remove_bg(image):

    output_image = remove(image)

    return [output_image]

# 이미지 배경 변경
def generate_bg(image_url):
    api_url = "https://api.developer.pixelcut.ai/v1/generate-background"

    payload_data = {
        "image_url": image_url,
        "image_transform": {
            "scale": 1,
            "x_center": 0.5,
            "y_center": 0.5
        }
    }
    prompt_options = ["marble", "wood", "industrial", "linen", "brick", "counter"]
    # selected_prompt = random.choice(prompt_options)
    selected_prompt = "brick"
    payload_data["scene"] = selected_prompt

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-API-KEY': os.getenv("PIXEL_API_KEY")  # 환경 변수에서 API 키 가져오기
    }

    result =  requests.post(api_url, headers=headers, data=json.dumps(payload_data)).json().get("result_url")
    response = requests.get(result)
    response.raise_for_status()
    img = Image.open(BytesIO(response.content))
    return [img]