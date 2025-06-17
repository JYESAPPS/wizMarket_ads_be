from datetime import datetime
import logging
import io
import os
from dotenv import load_dotenv
import requests
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
import base64
import re
import time
from runwayml import RunwayML
import anthropic
from moviepy import *
import uuid
from google import genai
from google.genai import types
import subprocess
from PIL import Image
from io import BytesIO
from app.crud.ads_app import (
    select_random_image as crud_select_random_image,
    get_style_image as crud_get_style_image
)

logger = logging.getLogger(__name__)
load_dotenv()

# OpenAI API 키 설정
api_key = os.getenv("GPT_KEY")
client = OpenAI(api_key=api_key)

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


# 옵션 값들 자동 선택
def generate_option(request):
    today = datetime.now()
    formattedToday = today.strftime('%Y-%m-%d')

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
            주어진 프롬프트 스타일은 유지하며 {detail_category_name}에 맞게 내용만 바꿔 영문 프롬프트를 작성해주세요.
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
        if channel in [1, 3]:
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
def get_style_image():
    image_list = crud_get_style_image()
    return image_list

# 주어진 값들로 자동 선택 - 재생성
def generate_option_regen(request):
    pass