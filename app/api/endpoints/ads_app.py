from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException, status
)
from app.schemas.ads_app import (
    AutoApp,
)
from fastapi import Request, Body
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime
import os
import uuid
import json
from io import BytesIO
from rembg import remove
import base64
import logging
from app.service.ads_generate import (
    generate_content as service_generate_content,
    generate_image as service_generate_image,
    generate_image_mid as service_generate_image_mid,
    generate_image_imagen3_template as service_generate_image_imagen3_template,
    generate_image_vision as service_generate_image_vision
)
from app.service.ads_app import (
    generate_option as service_generate_option,
    parse_age_gender_info as service_parse_age_gender_info,
    select_random_image as service_select_random_image,
    generate_by_seed_prompt as service_generate_by_seed_prompt
)

router = APIRouter()
logger = logging.getLogger(__name__)

# ver2 AI 생성
@router.post("/auto/app")
def generate_template(request: AutoApp):
    try:
        # GPT 로 옵션 값 자동 생성
        try:
            options = service_generate_option(
                request
            )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")

        raw = options.replace(",", "-").replace(" ", "")  # "3-1-4"
        parts = raw.split("-")  # ["3", "1", "4"]

        title, channel, style = parts

        male_text = service_parse_age_gender_info(request.commercial_district_max_sales_m_age)
        female_text = service_parse_age_gender_info(request.commercial_district_max_sales_f_age)

        detail_content = ""
        # 문구 생성
        try:
            copyright_role = ""
            copyright_prompt = ""
            # print(request.example_image)
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')
            print(title)
            if title == 3 or "3":
                copyright_role : f'''
                    다음과 같은 내용을 바탕으로 온라인 광고 콘텐츠를 제작하려고 합니다. 
                    잘 어울리는 광고 문구를 생성해주세요.
                    - 제목 : 15자 내외 간결하고 호기심을 유발할 수 있는 제목 
                    - 내용 : 30자 내외 간결하고 함축적인 내용
                    - 특수기호, 이모티콘은 제외할 것
                '''

                copyright_prompt = f'''
                    {request.store_name} 업체의 {channel} 위한 광고 컨텐츠를 제작하려고 합니다.
                    {request.detail_category_name}, {formattedToday}, {request.main}, {request.temp}℃
                    주요 고객층: {male_text}, {female_text} 제목 :, 내용 : 형식으로 작성해주세요
                '''
            else:
                copyright_role : f'''
                    다음과 같은 내용을 바탕으로 온라인 광고 콘텐츠를 제작하려고 합니다. 
                    잘 어울리는 광고 문구를 생성해주세요.
                    - 15자 내외 간결하고 호기심을 유발할 수 있는 제목
                    - 특수기호, 이모티콘은 제외할 것
                '''

                copyright_prompt = f'''
                    {request.store_name} 업체의 {channel} 위한 문구.
                    {request.detail_category_name}, {formattedToday}, {request.main}, {request.temp}℃
                    주요 고객층: {male_text}, {female_text}을 바탕으로 15자 이내로 작성해주세요
                '''

            copyright = service_generate_content(
                copyright_prompt,
                copyright_role,
                detail_content
            )
            print(copyright)
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")


        # 전달받은 선택한 템플릿의 시드 프롬프트 gpt로 소분류에 맞게 바꾸기
        seed_prompt = service_select_random_image(style)

        # 이미지 생성
        try:
            origin_image = service_generate_by_seed_prompt(
                channel,
                copyright,
                request.detail_category_name,
                seed_prompt
            )

            output_images = []
            for image in origin_image:  # 리스트의 각 이미지를 순회
                buffer = BytesIO()
                image.save(buffer, format="PNG")  # 이미지 저장
                buffer.seek(0)
                
                # Base64 인코딩 후 리스트에 추가
                output_images.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))

        except Exception as e:
            print(f"Error occurred: {e}, 이미지 생성 오류")

        # 인스타 문구 테스트
        try:
            insta_copyright = ''
            
            if channel == 3:
                today = datetime.now()
                formattedToday = today.strftime('%Y-%m-%d')

                copyright_prompt = f'''
                    {request.store_name} 업체의 {channel}를 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {request.detail_category_name}
                    일시 : {formattedToday}
                    오늘날씨 : {request.main}, {request.temp}℃
                    주요 고객층: {male_text}, {female_text}

                    주소: {request.road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 인플루언서가 {request.detail_category_name} 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    
                    2.광고 타겟들이 흥미를 갖을만한 내용의 키워드를 뽑아서 검색이 잘 될만한 해시태그도 최소 3개에서 6개까지 생성한다
                '''

                insta_copyright = service_generate_content(
                    copyright_prompt,
                    insta_role,
                    detail_content
                )
        except Exception as e:
            print(f"Error occurred: {e}, 인스타 생성 오류")
        
        # 문구와 합성된 이미지 반환
        return JSONResponse(content={
            "copyright": copyright, "origin_image": output_images, "insta_copyright" : insta_copyright,
            "title": title, "channel":channel, "style": style, "core_m": male_text, "core_f": female_text,
            "main": request.main, "detail_category_name" : request.detail_category_name,
            "store_name": request.store_name, "road_name": request.road_name
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

