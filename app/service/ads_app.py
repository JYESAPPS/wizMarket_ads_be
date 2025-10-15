from datetime import datetime
import logging
import os, asyncio, httpx, uuid, shutil
import re
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
from runwayml import RunwayML
from moviepy import *
from google import genai
from google.genai import types
import google.auth 
from google.auth.transport.requests import Request
from io import BytesIO
from fastapi import UploadFile, HTTPException
from app.crud.ads_app import (
    select_random_image as crud_select_random_image,
    get_style_image as crud_get_style_image,
    insert_upload_record as crud_insert_upload_record,
    get_user_info as crud_get_user_info,
    get_user_record as crud_get_user_record,
    get_user_record_this_month as crud_get_user_record_this_month,
    get_user_profile as crud_get_user_profile,
    insert_user_info as crud_insert_user_info,
    update_user_info as crud_update_user_info,
    get_user_recent_reco as crud_get_user_recent_reco,
    update_user_reco as crud_update_user_reco,
    delete_user_reco as crud_delete_user_reco,
    get_store_info as crud_get_store_info,
    update_register_tag as crud_update_register_tag,
    update_user_custom_menu as crud_update_user_custom_menu,
    insert_user_custom_menu as crud_insert_user_custom_menu,
    user_info_exists_by_sbn as crud_user_info_exists_by_sbn,
    upsert_user_info as crud_upsert_user_info,
)
from app.crud.ads import (
    get_category_id as crud_get_category_id
)
import base64
from datetime import datetime
from io import BytesIO
import traceback
import io
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from rembg import remove
import requests
import json
import random
from typing import List


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

    prompt_templates = {
        "10대": "유쾌하고 재밌는 말투로 짧은 광고 문구를 써줘. 이모지와 유행어를 자연스럽게 활용해서 친구끼리 말하는 듯한 느낌이면 좋아.",            
        "20대": "감성적이고 세련된 말투로 SNS에 어울리는 광고 문구를 써줘. 유행하는 표현을 적절히 섞어서 자연스럽고 눈길을 끌 수 있게 해줘.",            
        "30대": "바쁜 일상 속에서도 한눈에 들어올 수 있는 효율적인 문장으로 써줘. 감성은 유지하되 군더더기 없이 직관적인 톤이면 좋아.",            
        "40대": "신뢰감 있고 차분한 말투로 제품이나 서비스의 가치를 안정적으로 전달할 수 있는 광고 문구를 써줘.",            
        "50대": "정직하고 진중한 느낌을 주는 말투로, 신뢰할 수 있고 실용적인 정보가 담긴 광고 문구를 써줘.",            
        "60대": "친절하고 배려 있는 말투로, 쉽게 이해할 수 있고 부담 없이 다가가는 느낌의 광고 문구를 써줘.",
    }

    prompt_template = prompt_templates.get(age, f"{age}를 위한 자연스러운 광고 문구를 써줘.")
    female_text = f"{gender} {age} ({percentage}%) \n\n{prompt_template}"

    return female_text

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
def generate_by_seed_prompt(channel, copyright, detail_category_name, seed_prompt, register_tag: str | None = None):
    try:
        # gpt 영역
        gpt_role = f"""
            You are a professional prompt writing expert.
        """

        gpt_content = f"""
            프롬프트 스타일 : {seed_prompt}
            주어진 프롬프트 스타일은 유지하며 {copyright}와 {register_tag}에 맞게 내용만 바꿔 영문 프롬프트를 작성해주세요.
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

        if channel in [1, 2, 5]:  # 카카오톡, 인스타그램 피드, SMS
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
async def insert_upload_record(request, file: UploadFile | None):
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

    # 여기서만 분기
    if file is not None:
        image_path = save_blob_image(file, user_id, channel)
    else:
        image_path = save_base64_image(request.image, user_id, channel)

    # 이후 로직은 그대로
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
    return {"success": bool(success), "imageUrl": image_path}

# 채널 코드 → 이름 매핑 (내부 포함)
CHANNEL_MAP  = {"1": "kakao", "2": "story", "3": "feed", "4": "blog"}

# base64 이미지 파일 저장 및 경로 설정
def save_base64_image(base64_str, user_id: int, channel_code: str, save_dir="uploads/image/user"):

    channel_name = CHANNEL_MAP.get(channel_code, "unknown")

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
    url_path = f"http://wizmarket.ai:8000/{relative_path.replace(os.sep, '/')}"
    
    return url_path

# blob 저장 경로
def save_blob_image(
    file: UploadFile,
    user_id: int,
    channel_code: str,
    save_dir: str = "app/uploads/image/user",
    base_url: str = "http://wizmarket.ai:8000",
) -> str:
    if not file:
        raise HTTPException(status_code=400, detail="file이 없습니다.")

    # 허용 타입/확장자 결정
    allow = {"image/jpeg": ".jpg", "image/png": ".png"}
    ext = allow.get(file.content_type)
    if not ext:
        # content_type이 비어있으면 파일명 확장자로 보정 시도
        name = (file.filename or "").lower()
        if name.endswith(".jpg") or name.endswith(".jpeg"):
            ext = ".jpg"
        elif name.endswith(".png"):
            ext = ".png"
        else:
            raise HTTPException(status_code=400, detail="jpeg/png만 허용")

    channel_name = CHANNEL_MAP.get(str(channel_code), "unknown")

    # 저장 경로 준비
    user_folder = f"user_{user_id}"
    full_dir = os.path.join(save_dir, user_folder)
    os.makedirs(full_dir, exist_ok=True)

    # 파일명 생성
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    # unique = uuid.uuid4().hex
    filename = f"{user_id}_{channel_name}_{ts}{ext}"
    file_path = os.path.join(full_dir, filename)

    # 스트리밍 저장
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    finally:
        try:
            # UploadFile 닫기 (에러 나도 무시)
            if hasattr(file, "close"):
                # FastAPI UploadFile.close는 코루틴일 수도 있음
                close = file.close()
                if hasattr(close, "__await__"):
                    import asyncio
                    asyncio.create_task(close)  # fire-and-forget
        except Exception:
            pass

    # 퍼블릭 URL 생성 (로컬 경로 → URL)
    relative_path = file_path.replace("app/", "").replace(os.sep, "/")
    return f"{base_url}/{relative_path}"

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

def service_insert_user_info(user_id, request):
    return crud_insert_user_info(user_id, request)

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
        # success = crud_update_user_info(user_id, request)
        success = crud_upsert_user_info(user_id, request)
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
    # prompt_options = ["marble", "wood", "industrial", "linen", "brick", "counter"]
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

# vertex ai(google) 토큰
def get_vertex_token() -> str:
    SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
    creds, _ = google.auth.default(scopes=SCOPES)
    if not creds.valid:
        creds.refresh(Request())
    return creds.token

# vertex ai로 배경 재생성
def generate_vertex_bg(image: bytes, prompt: str) -> bytes:
    
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
    LOCATION   = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    MODEL_ID   = "imagen-3.0-capability-001"
    ENDPOINT   = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/"
        f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:predict"
    )

    b64_im = base64.b64encode(image).decode("utf-8")
    body = {
        "instances": [
            {
                "prompt": prompt,
                "referenceImages": [
                    {
                        "referenceType": "REFERENCE_TYPE_RAW",
                        "referenceId": 1, 
                        "referenceImage": {
                            "bytesBase64Encoded": b64_im
                        }
                    },
                    {
                        "referenceType": "REFERENCE_TYPE_MASK",
                        "referenceId": 2,
                        "maskImageConfig": {
                            "maskMode": "MASK_MODE_BACKGROUND",
                            "dilation": 0.0
                        }
                    }
                ]
            }
        ],
        "parameters": {
            "editConfig": {"baseSteps": 75},
            "editMode": "EDIT_MODE_BGSWAP",
            "sampleCount": 1
            
        }
    }

    headers = {
        "Authorization": f"Bearer {get_vertex_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    res = requests.post(ENDPOINT, headers=headers, data=json.dumps(body), timeout=60)
    if res.status_code != 200:
        raise RuntimeError(f"Vertex error {res.status_code}: {res.text}")

    data = res.json()
    preds = data.get("predictions")
    out_list: List[str] = []
    for p in preds:
        b64_out = p.get("bytesBase64Encoded")
        if not b64_out:
            continue
        # 순수 base64만 부여 
        out_list.append(b64_out)

    return out_list

# 필터 API (AI lab tools)
async def cartoon_image(image_bytes: bytes, index: int,
                        poll_interval: float = 2.0, max_attempts: int = 15) -> Image.Image:
    import os, asyncio, httpx
    AILABTOOLS_API_KEY = os.getenv("AILABTOOLS_API_KEY")
    API_BASE = "https://www.ailabapi.com"
    GEN_URL = f"{API_BASE}/api/image/effects/ai-anime-generator"
    ASYNC_URL = f"{API_BASE}/api/image/asyn-task-results"

    headers = {"ailabapi-api-key": AILABTOOLS_API_KEY}
    files = {
        "task_type": (None, "async"),
        "index": (None, str(index)),
        "image": ("input.png", image_bytes, "image/png"),
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1) 비동기 작업 생성
        create_resp = await client.post(GEN_URL, headers=headers, files=files)
        create_resp.raise_for_status()
        payload = create_resp.json()

        job_id = payload.get("request_id") or payload.get("task_id")
        if not job_id:
             raise HTTPException(status_code=502, detail=f"Invalid response from AILabTools: {payload}")

        # 2) 결과 폴링
        params = {"job_id": job_id, "type": "GENERATE_CARTOONIZED_IMAGE"}
        for _ in range(max_attempts):
            result_resp = await client.get(ASYNC_URL, headers=headers, params=params)
            result_resp.raise_for_status()
            result = result_resp.json()
            data = result.get("data") or {}
            status = (data.get("status") or "").upper()

            if status == "PROCESS_SUCCESS":
                result_url = data.get("result_url")
                if not result_url:
                    raise HTTPException(status_code=502, detail="AILabTools 결과 URL 누락")
                img_resp = await client.get(result_url)
                img_resp.raise_for_status()

                # ✅ bytes → PIL.Image 변환
                return Image.open(BytesIO(img_resp.content))

            if status in {"PROCESS_FAILED", "TIMEOUT_FAILED", "LIMIT_RETRY_FAILED"}:
                raise HTTPException(status_code=502, detail=f"AILabTools 실패: {result}")

            await asyncio.sleep(poll_interval)

        raise HTTPException(status_code=504, detail="시간 초과")


#유효성 검사
def validation_test(title, channel, female_text, style):
        # 매핑 정의
    title_map = {
        "매장홍보": "1",
        "상품소개": "2",
        "이벤트": "3",
    }

    channel_map = {
        "카카오톡": "1",
        "인스타그램 스토리": "2",
        "인스타그램 피드": "3",
        "블로그": "4",
    }

    style_map = {
        "3D감성": "1",
        "포토실사": "2",
        "캐릭터/만화": "3",
        "레트로": "4",
        "AI모델": "5",
        "예술": "6",
    }
    
    # 주 고객
    age_map = {
        1: "10대",
        2: "20대",
        3: "30대",
        4: "40대",
        5: "50대",
        6: "60대 이상"
    }


    # 문자열 매핑 → 숫자 문자열로 통일
    title = title_map.get(str(title), str(title))
    channel = channel_map.get(str(channel), str(channel))
    style = style_map.get(str(style), str(style))

    # 유효성 검사 및 기본값 지정
    if title not in ["1", "2", "3"]:
        title = "1"

    if channel not in ["1", "2", "3", "4"]:
        channel = "2"

    if style not in ["1", "2", "3", "4", "5", "6"]:
        style = "1"

    # 문자열이고 "여성 40대" 같은 문장이면 그대로 유지
    if isinstance(female_text, str) and "대" in female_text:
        pass  # 그대로 둠

    else:
        try:
            female_text_int = int(female_text)
        except (ValueError, TypeError):
            female_text_int = 3  # 숫자 변환 불가능한 경우 기본 30대
        if female_text_int not in age_map:
            female_text_int = 3  # 범위 벗어나면 기본 30대

        female_text = age_map[female_text_int]

    return title, channel, female_text, style

def extract_age_group(text):
    # 이미 원하는 형식이면 그대로 반환
    if re.search(r'\b\d{2}대 이상\b', text):
        return re.search(r'\b\d{2}대 이상\b', text).group(0)
    elif re.search(r'\b\d{2}대\b', text):
        age = re.search(r'\b(\d{2})대\b', text).group(1)
        return "60대 이상" if age == "60" else f"{age}대"
    else:
        return None


def get_store_info(store_business_number):
    store_info = crud_get_store_info(store_business_number)
    return store_info

def update_user_custom_menu(custom_menu, store_business_number):
    if crud_user_info_exists_by_sbn(store_business_number):
        crud_update_user_custom_menu(custom_menu, store_business_number)
    else:
        crud_insert_user_custom_menu(custom_menu, store_business_number)

def update_register_tag(user_id: int, register_tag: str):
    crud_update_register_tag(user_id, register_tag)

def get_season(date: datetime) -> str:
    month = datetime.strptime(date, "%Y-%m-%d").month

    if 3 <= month <= 5:
        return "봄"
    elif 6 <= month <= 8:
        return "여름"
    elif 9 <= month <= 11:
        return "가을"
    else:
        return "겨울"

# 메뉴 텍스트 우선순위에 따라 결정
def pick_effective_menu(request) -> str:
    def _clean(v):
        return (v or "").strip()

    # 1) custom_menu
    menu = _clean(getattr(request, "custom_menu", None))
    if menu:
        return menu

    # 2) register_tag
    tag = _clean(getattr(request, "register_tag", None))
    if tag:
        return tag

    # 3) DB 보강 (있으면)
    # try:
    #     user_id = int(getattr(request, "user_id", 0) or 0)
    #     if user_id:
    #         info, _ = get_user_info(user_id)   # 기존 함수 재사용
    #         # DB의 custom_menu 우선, 없으면 DB의 register_tag
    #         menu = _clean((info or {}).get("custom_menu"))
    #         if menu:
    #             return menu
    #         tag = _clean((info or {}).get("register_tag"))
    #         if tag:
    #             return tag
    # except Exception:
    #     pass

    # 4) 최종 폴백
    return _clean(getattr(request, "detail_category_name", None)) or "메뉴"