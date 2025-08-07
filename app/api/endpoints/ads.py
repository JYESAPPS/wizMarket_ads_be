from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException, status
)
from app.schemas.ads import (
    AdsInitInfoOutPut,AdsGenerateContentOutPut, AdsContentRequest,
    AdsImageRequest, AdsDeleteRequest, AdsInitInfoOutPutWithImages,
    AuthCallbackRequest,
    AdsSuggestChannelRequest,
    KaKaoTempInsert, KaKaoTempGet, AdsTemplateSeedImage,
)
from fastapi import Request, Body
from PIL import Image, ImageOps
import logging
import base64
import io
from typing import List
import requests
from google_auth_oauthlib.flow import Flow
from app.service.ads import (
    select_ads_init_info as service_select_ads_init_info,
    select_custom_menu as service_select_custom_menu,
    insert_ads as service_insert_ads,
    delete_status as service_delete_status,
    update_ads as service_update_ads,
    random_design_style as service_random_design_style,
    select_ai_age as service_select_ai_age,
    select_ai_data as service_select_ai_data,
)
from app.service.ads_generate import (
    generate_content as service_generate_content,
    generate_image as service_generate_image,
    generate_video as service_generate_video,
    generate_image_mid as service_generate_image_mid,
    generate_add_text_to_video as service_generate_add_text_to_video,
    generate_image_imagen3  as service_generate_image_imagen3,
    generate_image_imagen3_template as service_generate_image_imagen3_template,
    generate_image_vision as service_generate_image_vision
)


# from app.service.ads_upload_naver import upload_naver_ads as service_upload_naver_ads

from app.service.ads_app import (
    get_style_image as service_get_style_image,
)
from app.service.ads_login import (
    select_insta_account as service_select_insta_account
)


import redis
import traceback
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


router = APIRouter()
logger = logging.getLogger(__name__)

ROOT_PATH = Path(os.getenv("ROOT_PATH"))
IMAGE_DIR = Path(os.getenv("IMAGE_DIR"))
VIDEO_DIR = Path(os.getenv("VIDEO_PATH"))
FULL_PATH = ROOT_PATH / IMAGE_DIR.relative_to("/") / "ads"
FULL_PATH.mkdir(parents=True, exist_ok=True)


redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


# 매장 리스트에서 모달창 띄우기
@router.post("/select/init/info", response_model=AdsInitInfoOutPutWithImages)
def select_ads_init_info(store_business_number: str):
    # 쿼리 매개변수로 전달된 store_business_number 값 수신
    try:
        init_data = service_select_ads_init_info(store_business_number)
        custom_menu = service_select_custom_menu(store_business_number)
        ai_age = service_select_ai_age(init_data, custom_menu)
        # print(init_data)
        ai_data = service_select_ai_data(init_data, ai_age, custom_menu)
        random_image_list = service_random_design_style(init_data, ai_data[0])
        all_image_list = service_get_style_image(init_data)
        # insta_info = service_select_insta_account(store_business_number)
        

        # print(ai_age, ai_data)
        return AdsInitInfoOutPutWithImages(
            **init_data.dict(),
            custom_menu=custom_menu,
            image_list=random_image_list,
            all_image_list=all_image_list,
            insta_info=None,
            ai_age = ai_age,
            ai_data = ai_data,
        )

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 광고 채널 추천
@router.post("/suggest/channel")
def select_suggest_channel(request: AdsSuggestChannelRequest):
    # 쿼리 매개변수로 전달된 store_business_number 값 수신
    try:
        gpt_role = '''
            당신은 온라인 광고 전문가 입니다. 
            오프라인 점포를 하는 매장에서 다음과 같은 내용으로 홍보 콘텐츠를 제작하여 포스팅하려고 합니다. 
            이 매장에서 가장 좋은 홍보 방법 무엇이 좋겠습니까? 
            제시된 상황에 따라 채널과  디자인 스타일 중에 하나를 선택해주고 그 이유와 홍보전략을 200자 내외로 작성해주세요.
        '''

        prompt = f'''
            매장명 : {request.store_name}
            주소 : {request.road_name}
            업종 : {request.tag}
            주 고객층 : {request.male_base}, {request.female_base}
            홍보 주제 : {request.title}
            홍보채널 : 문자메시지, 인스타그램 스토리, 인스타그램 피드, 네이버 블로그, 
                        카카오톡, 자사 홈페이지, 페이스북, 디스코드, 트위터, 미디엄, 네이버 밴드, 캐치테이블, 배달의 민족
            디자인 스타일 : 3D 일러스트(3d, 클레이메이션, 픽셀디자인, 레고스타일, 닌텐도 스타일, paper craft, 디오라마, isometric), 
                            실사 사진, 캐릭터.만화, 레트로 감성, AI로 생성한 남녀모델, 예술(르노와르, 피카소, 고흐 등) 
        '''
        detail_contet = ""

        channel = service_generate_content(
            prompt,
            gpt_role,
            detail_contet
        )
        return {"chan": channel}
    except Exception as e:
        print(f"Error occurred: {e}, 문구 생성 오류")


# 광고 채널 추천 테스트
@router.post("/suggest/channel/test")
def select_suggest_channel(request: AdsSuggestChannelRequest):
    # 쿼리 매개변수로 전달된 store_business_number 값 수신
    try:
        gpt_role = '''
            당신은 온라인 광고 전문가 입니다. 
            이 매장에서 가장 좋은 홍보 방법을 제시된 보기에서 하나만 선택 후 숫자만 대답해주세요.
        '''

        prompt = f'''
            매장명 : {request.store_name}
            주소 : {request.road_name}
            업종 : {request.tag}
            주 고객층 : {request.male_base}, {request.female_base}
            홍보 주제 : {request.title}
            홍보채널 : 문자메시지, 인스타그램 스토리, 인스타그램 피드, 네이버 블로그, 
                        카카오톡, 자사 홈페이지, 페이스북, 디스코드, 트위터, 미디엄, 네이버 밴드, 캐치테이블, 배달의 민족
            디자인 스타일 : 3D 일러스트(3d, 클레이메이션, 픽셀디자인, 레고스타일, 닌텐도 스타일, paper craft, 디오라마, isometric), 
                            실사 사진, 캐릭터.만화, 레트로 감성, AI로 생성한 남녀모델, 예술(르노와르, 피카소, 고흐 등) 

            1. 문자메시지, 2. 인스타그램 스토리, 3. 인스타그램 피드, 4. 네이버 블로그, 5. 카카오톡, 6. 네이버 밴드
        '''
        detail_contet = ""

        channel = service_generate_content(
            prompt,
            gpt_role,
            detail_contet
        )
        return {"chan": channel}
    except Exception as e:
        print(f"Error occurred: {e}, 문구 생성 오류")


# 프론트에서 이미지 처리 테스트
# @router.post("/generate/exist/image/test")
# def generate_image_with_test(request: AdsImageTestFront):
#     try:
#         # 문구 생성
#         try:
#             today = datetime.now()
#             formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

#             copyright_prompt = f'''
#                 매장명 : {request.store_name}
#                 주소 : {request.road_name}
#                 업종 : {request.tag}
#                 날짜 : {formattedToday}
#            
#                 매출이 가장 높은 남성 연령대 : {request.male_base}
#                 매출이 가장 높은 여성 연령대 : {request.female_base}
#             '''
#             copyright = service_generate_content(
#                 copyright_prompt,
#                 request.gpt_role,
#                 request.detail_content
#             )
#         except Exception as e:
#             print(f"Error occurred: {e}, 문구 생성 오류")

#         # 문구 반환
#         return JSONResponse(content={"copyright": copyright})

#     except HTTPException as http_ex:
#         logger.error(f"HTTP error occurred: {http_ex.detail}")
#         raise http_ex
#     except Exception as e:
#         error_msg = f"Unexpected error while processing request: {str(e)}"
#         logger.error(error_msg)
#         raise HTTPException(status_code=500, detail=error_msg)










# ver2 AI 생성
@router.post("/generate/template2")
def generate_template(request: AdsTemplateSeedImage):
    try:
        # 문구 생성
        try:
            # print(request.example_image)
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')
            if request.title == '이벤트':
                copyright_prompt = f'''
                    {request.store_name} 업체의 {request.use_option} 위한 광고 컨텐츠를 제작하려고 합니다.
                    {request.tag}, {formattedToday}, {request.weather}, {request.temp}℃, {request.detail_content}
                    핵심 고객 연령대 : {request.male_base}, {request.female_base} 제목 :, 내용 : 형식으로 작성해주세요
                '''
            else:
                copyright_prompt = f'''
                    {request.store_name} 업체의 {request.use_option} 위한 광고 컨텐츠를 제작하려고 합니다.
                    {request.tag}, {formattedToday}, {request.weather}, {request.temp}℃, {request.detail_content}
                    핵심 고객 연령대 : {request.male_base}, {request.female_base} 내용 15자 이내로 작성해주세요
            '''

            copyright = service_generate_content(
                copyright_prompt,
                request.gpt_role,
                request.detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")
        
        # 전달받은 선택한 템플릿의 시드 프롬프트 gpt로 소분류에 맞게 바꾸기
        seed_image_prompt = request.seed_prompt

        # 전달받은 선택한 템플릿의 시드 이미지 gpt로 이미지 분석
        seed_image_vision = service_generate_image_vision(request.example_image)

        # 이미지 생성
        try:
            if request.ai_model_option == 'midJouney':
                origin_image = service_generate_image_mid(
                    request.use_option,
                    seed_image_prompt
                )
            elif request.ai_model_option == "imagen3":
                origin_image = service_generate_image_imagen3_template(
                    request.use_option,
                    copyright,
                    request.tag,
                    seed_image_prompt,
                    seed_image_vision
                )
            else:
                origin_image = service_generate_image(
                    request.use_option,
                    seed_image_prompt
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
            
            if request.use_option == '인스타그램 피드':
                today = datetime.now()
                formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

                copyright_prompt = f'''
                    {request.store_name} 업체의 {request.title}를 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {request.tag}
                    세부정보 : {request.detail_content}
                    일시 : {formattedToday}
        
                    핵심고객: 
                    매출이 가장 높은 남성 연령대 : 남자 {request.male_base}
                    매출이 가장 높은 여성 연령대 : 여자 {request.female_base}


                    주소: {request.road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로, 영업시간은 🕒로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = '''
                    1. '{copyright}' 를 100~150자까지 {request.title} 인플루언서가 $대분류$ 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    
                    2.광고 타겟들이 흥미를 갖을만한 내용의 키워드를 뽑아서 검색이 잘 될만한 해시태그도 최소 3개에서 6개까지 생성한다
                '''

                insta_copyright = service_generate_content(
                    copyright_prompt,
                    insta_role,
                    request.detail_content
                )

        except Exception as e:
            print(f"Error occurred: {e}, 인스타 생성 오류")
        
        # 문구와 합성된 이미지 반환
        return JSONResponse(content={"copyright": copyright, "origin_image": output_images, "insta_copyright" : insta_copyright})

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# ver2 파일 업로드
@router.post("/generate/exist/image/template2")
def generate_image_with_text_template2(
        store_name: str = Form(...),
        road_name: str = Form(...),
        tag: str = Form(...),
        weather: str = Form(...),
        temp: float = Form(...),
        male_base: str = Form(...),
        female_base: str = Form(...),
        gpt_role: str = Form(...),
        detail_content: str = Form(...),
        use_option: str = Form(...),
        title: str = Form(...),
    ):

    try:
        # 문구 생성
        try:
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

            copyright_prompt = f'''
                매장명 : {store_name}
                주소 : {road_name}
                업종 : {tag}
                날짜 : {formattedToday}
                매출이 가장 높은 남성 연령대 : {male_base}
                매출이 가장 높은 여성 연령대 : {female_base}
            '''
            copyright = service_generate_content(
                copyright_prompt,
                gpt_role,
                detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")

    # 인스타 문구 테스트
        try:
            insta_copyright = ''
            
            if use_option == '인스타그램 피드':
                today = datetime.now()
                formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

                copyright_prompt = f'''
                    {store_name} 업체의 {title}를 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {tag}
                    세부정보 : {detail_content}
                    일시 : {formattedToday}
        
                    핵심고객: 
                    매출이 가장 높은 남성 연령대 : 남자 {male_base}
                    매출이 가장 높은 여성 연령대 : 여자 {female_base}


                    주소: {road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로, 영업시간은 🕒로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = '''
                    1. '{copyright}' 를 100~150자까지 {request.title} 인플루언서가 $대분류$ 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    {request.title}에 광고할 타겟은 핵심 연령층으로 {request.title}에 어울리는 내용을 생성한다. 
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
        return JSONResponse(content={"copyright": copyright, "insta_copyright" : insta_copyright})

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)





# 문구 생성
@router.post("/generate/content", response_model=AdsGenerateContentOutPut)
def generate_content(request: AdsContentRequest):
    try:
        # print('깃허브 푸시용 테스트')
        # 서비스 레이어 호출: 요청의 데이터 필드를 unpack
        data = service_generate_content(
            request.prompt,
            request.gpt_role,
            request.detail_content
        )
        return {"content": data}  
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# 모달창에서 이미지 생성하기
@router.post("/generate/image")
def generate_image(request: AdsImageRequest):
    try:
        if request.ai_model_option == 'midJouney':
            image = service_generate_image_mid(
                request.use_option,
                request.ai_mid_prompt,
            )
            return image
        else:
            # 서비스 레이어 호출: 요청의 데이터 필드를 unpack
            image = service_generate_image(
                request.use_option,
                request.ai_prompt,
            )
            base64_images = []
            for img in image:
                if isinstance(img, dict):  # 🔹 dict이면 이미지 객체가 아니라 직렬화된 데이터이므로 처리 불필요
                    base64_images.append(img)  # 이미 변환된 데이터라면 그대로 추가
                else:
                    buffered = io.BytesIO()
                    img.save(buffered, format="PNG")
                    base64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    base64_images.append(base64_img)

            return base64_images  # 🔹 리스트 자체를 반환 (FastAPI 자동 직렬화 방지)
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        print(f"HTTPException 발생: {http_ex.detail}")  # 추가 디버깅 출력
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        print(f"Exception 발생: {error_msg}")  # 추가 디버깅 출력
        raise HTTPException(status_code=500, detail=error_msg)



# ADS DB에 저장
@router.post("/insert")
def insert_ads(
        store_business_number: str = Form(...),
        use_option: str = Form(...),
        title: str = Form(...),
        detail_title: Optional[str] = Form(None),  # 선택적 필드
        content: str = Form(...),
        image: UploadFile = File(None),
        final_image: UploadFile = File(None)  # 단일 이미지 파일
    ):
    # 이미지 파일 처리
    image_url = None
    if image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_{today}_{uuid.uuid4()}{ext}"

            # 파일 저장 경로 지정
            file_path = os.path.join(FULL_PATH, unique_filename)

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            # 이미지 URL 생성
            image_url = f"/static/images/ads/{unique_filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving image file: {str(e)}"
            )

    # 파이널 이미지 파일 처리
    final_image_url = None
    if final_image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(final_image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_final_{today}_{uuid.uuid4()}{ext}"

            # 파일 저장 경로 지정
            file_path = os.path.join(FULL_PATH, unique_filename)

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(final_image.file, buffer)

            # 파이널 이미지 URL 생성
            final_image_url = f"/static/images/ads/{unique_filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving final_image file: {str(e)}"
            )

    # 데이터 저장 호출
    try:
        ads_pk = service_insert_ads(
            store_business_number, 
            use_option, 
            title, 
            detail_title, 
            content, 
            image_url, 
            final_image_url
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inserting ad data: {str(e)}"
        )

    # 성공 응답 반환
    return ads_pk

# ADS 삭제처리
@router.post("/delete/status")
def delete_status(request: AdsDeleteRequest):
    try:
        # 서비스 레이어를 통해 업데이트 작업 수행
        success = service_delete_status(
            request.ads_id,
        )
        if success:
            return success
    except Exception as e:
        # 예외 처리
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

# ADS DB에 수정
@router.post("/update")
def update_ads(
        store_business_number: str = Form(...),
        use_option: str = Form(...),
        title: str = Form(...),
        detail_title: Optional[str] = Form(None),  # 선택적 필드
        content: str = Form(...),
        image: UploadFile = File(None),
        final_image: UploadFile = File(None)  # 단일 이미지 파일
    ):
    
    # 이미지 파일 처리
    image_url = None
    if image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_{today}_{uuid.uuid4()}{ext}"

            # 파일 저장 경로 지정
            file_path = os.path.join(FULL_PATH, unique_filename)

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            # 이미지 URL 생성
            image_url = f"/static/images/ads/{unique_filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving image file: {str(e)}"
            )

    # 파이널 이미지 파일 처리
    final_image_url = None
    if final_image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(final_image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_final_{today}_{uuid.uuid4()}{ext}"

            # 파일 저장 경로 지정
            file_path = os.path.join(FULL_PATH, unique_filename)

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(final_image.file, buffer)

            # 파이널 이미지 URL 생성
            final_image_url = f"/static/images/ads/{unique_filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving final_image file: {str(e)}"
            )

    # 데이터 저장 호출
    try:
        service_update_ads(
            store_business_number, 
            use_option, 
            title, 
            detail_title, 
            content, 
            image_url, 
            final_image_url
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating ad data: {str(e)}"
        )

    # 성공 응답 반환
    return {
        "store_business_number": store_business_number,
        "use_option": use_option,
        "title": title,
        "detail_title": detail_title,
        "content": content,
        "image_url": image_url,
        "final_image_url": final_image_url
    }



# 카카오톡 업로드
@router.post("/temp/insert")
def generate_share_uuid(data: KaKaoTempInsert):
    unique_id = str(uuid.uuid4())[:8]  # 8자리 UUID 생성

    # 🔹 Redis에 JSON 데이터 저장 (유효기간 7일)
    redis_client.setex(unique_id, 86400 * 7, json.dumps(data.dict()))  

    return {"shortUrl": f"{unique_id}"}


@router.post("/temp/get")
def get_share_data(request: KaKaoTempGet):
    stored_data = redis_client.get(request.share_id)

    if not stored_data:
        raise HTTPException(status_code=404, detail="공유 데이터 없음")

    return json.loads(stored_data)


ROOT_PATH = os.getenv("ROOT_PATH")
AUTH_PATH = os.getenv("AUTH_PATH")

@router.post("/auth/callback")
def youtube_auth_callback(request: AuthCallbackRequest):
    CLIENT_SECRETS_FILE = os.path.join(ROOT_PATH, AUTH_PATH.lstrip("/"), "google_auth_wiz.json")
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    REDIRECT_URI = "http://localhost:3002/ads/auth/callback"

    code = request.code
    try:
        # Google OAuth Flow 초기화
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            SCOPES,
            redirect_uri=REDIRECT_URI,
        )

        # 인증 코드로 액세스 토큰 교환
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # 반환된 액세스 토큰
        access_token = credentials.token
        return {"access_token": access_token}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"Error exchanging auth code: {str(e)}"},
        )




# Ads 영상 만들기
@router.post("/generate/video")
def generate_video(
        title: str = Form(...),
        final_image: UploadFile = File(None)  # 단일 이미지 파일
    ):
    
    # 파이널 이미지 파일 처리
    if final_image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(final_image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_final_{today}_{uuid.uuid4()}{ext}"
            file_path = os.path.join(FULL_PATH, unique_filename)
            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(final_image.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving final_image file: {str(e)}"
            )
    
    # 데이터 저장 호출
    try:
        result_url= service_generate_video(file_path)
        return {"result_url" : result_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inserting ad data: {str(e)}"
        )


# 업로드 된 이미지로 영상 만들기
@router.post("/generate/video/image")
def generate_video_with_text(
        store_name: str = Form(...),
        road_name: str = Form(...),
        tag: str = Form(...),
        weather: str = Form(...),
        temp: float = Form(...),
        male_base: str = Form(...),
        female_base: str = Form(...),
        gpt_role: str = Form(...),
        detail_content: str = Form(...),
        image: UploadFile = File(...)
    ):

    try:
        # 문구 생성
        try:
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

            copyright_prompt = f'''
                매장명 : {store_name}
                주소 : {road_name}
                업종 : {tag}
                날짜 : {formattedToday}
                매출이 가장 높은 남성 연령대 : {male_base}
                매출이 가장 높은 여성 연령대 : {female_base}
            '''
            copyright = service_generate_content(
                copyright_prompt,
                gpt_role,
                detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")

        # 영상 생성
        if image:
            try:
                # 고유 이미지 명 생성
                filename, ext = os.path.splitext(image.filename)
                today = datetime.now().strftime("%Y%m%d")
                unique_filename = f"{filename}_jyes_ads_final_{today}_{uuid.uuid4()}{ext}"
                file_path = os.path.join(FULL_PATH, unique_filename)
                # 파일 저장
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error saving final_image file: {str(e)}"
                )
        try:
            result_path= service_generate_video(file_path)
        except Exception as e:
            print(f"Error occurred: {e}, 영상 생성 오류")

        # 문구와 영상 합성
        try:
            video_path = service_generate_add_text_to_video(result_path, copyright)
        except Exception as e:
            print(f"Error occurred: {e}, 영상 합성 오류")
        return {"copyright": copyright, "result_url": video_path["result_url"]}

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)





