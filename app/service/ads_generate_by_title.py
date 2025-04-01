import os
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import re
from moviepy import *
from datetime import datetime

def combine_ads_1_1 (store_name, road_name, content, title, image_width, image_height, image, weater, tag):
    if title == "매장 소개":
        image1 = combine_ads_store_intro_ver_1(store_name, road_name, content, image_width, image_height, image, weater, tag)
        image2 = combine_ads_store_intro_ver_2(store_name, road_name, content, image_width, image_height, image, alignment="center")
        image3 = combine_ads_store_intro_ver_3(store_name, road_name, content, image_width, image_height, image, alignment="center")
        return image1, image2, image3
    elif title == "이벤트":
        image1 = combine_ads_event(store_name, road_name, content, image_width, image_height, image, alignment="center")
        image2 = combine_ads_event_ver2(store_name, road_name, content, image_width, image_height, image, alignment="center")
        image3 = combine_ads_event_ver3(store_name, road_name, content, image_width, image_height, image, alignment="center")
        return image1, image2, image3
    

def combine_ads_4_7 (store_name, road_name, content, title, image_width, image_height, image, weater, tag):
    if title == "매장 소개":
        image1 = combine_ads_intro_4_7(store_name, road_name, content, image_width, image_height, image)
        image2 = combine_ads_intro_4_7_ver2(store_name, road_name, content, image_width, image_height, image, weater, tag)
        # image3 = combine_ads_intro_4_7_ver3(store_name, road_name, content, image_width, image_height, image)
        image4 = combine_ads_intro_4_7_ver4(store_name, road_name, content, image_width, image_height, image)
        image5 = combine_ads_intro_4_7_ver5(store_name, road_name, content, image_width, image_height, image)
        image6 = combine_ads_intro_4_7_ver6(store_name, road_name, content, image_width, image_height, image)
        image7 = combine_ads_intro_4_7_ver7(store_name, road_name, content, image_width, image_height, image)
        return image1, image2,  image4, image5, image6, image7
    elif title == "이벤트":
        image1 = combine_ads_event_4_7(store_name, road_name, content, image_width, image_height, image)
        image2 = combine_ads_event_4_7_ver2(store_name, road_name, content, image_width, image_height, image)
        image3 = combine_ads_event_4_7_ver3(store_name, road_name, content, image_width, image_height, image)
        image4 = combine_ads_event_4_7_ver4(store_name, road_name, content, image_width, image_height, image)
        image5 = combine_ads_event_4_7_ver5(store_name, road_name, content, image_width, image_height, image)
        return image1, image2, image3, image4, image5
    elif title == "상품소개":
        image = combine_ads_pro_intro_4_7(store_name, road_name, content, image_width, image_height, image)
        return image
    

def combine_ads_7_4 (store_name, road_name, content, title, image_width, image_height, image):
    if title == "매장 소개":
        image = combine_ads_store_intro_ver_1(store_name, road_name, content, image_width, image_height, image, alignment="center")
        return image
    elif title == "이벤트":
        image1 = combine_ads_event(store_name, road_name, content, image_width, image_height, image, alignment="center")
        return image1


# 텍스트 자르기
def split_top_line(text, max_length):

    result = []
    words = text.strip().split()
    # print(words)
    current_line = []
    current_length = 0

    for word in words:
        word_length = len(word)
        # 현재 줄에 추가해도 max_length를 넘지 않으면 추가
        if current_length + word_length + (1 if current_line else 0) <= max_length:
            current_line.append(word)
            current_length += word_length + (1 if current_line else 0)
        else:
            # 현재 줄이 꽉 찼으면 result에 추가하고 새로운 줄 시작
            result.append(" ".join(current_line))
            current_line = [word]
            current_length = word_length

    # 마지막 줄 추가
    if current_line:
        result.append(" ".join(current_line))
    
    return result

# 텍스트 세로 자르기
def split_text_by_column(text, max_chars_per_column):
    words = text.split()  # 띄어쓰기 기준으로 단어 분리
    columns = []
    current_column = ""

    for word in words:
        # 현재 컬럼에 단어를 추가했을 때 최대 글자 수 초과 여부 확인
        if len(current_column) + len(word) > max_chars_per_column:
            columns.append(current_column.strip())  # 현재 컬럼 저장
            current_column = word  # 새로운 컬럼 시작
        else:
            if current_column:
                current_column += " "  # 단어 간 띄어쓰기 유지
            current_column += word

    # 마지막 남은 컬럼 추가
    if current_column:
        columns.append(current_column.strip())

    return columns


from PIL import Image

from PIL import Image

def resize_and_crop_image(image_width, image_height, image, want_width=730, want_height=730):
    """이미지를 원하는 크기로 조정하고 중앙을 기준으로 크롭 (가로/세로 최소 기준 유지)"""
    
    # 원본 및 목표 비율 계산
    target_ratio = want_width / want_height
    original_ratio = image_width / image_height

    # 1. 리사이징 (최소 한 변이 목표 크기 이상이 되도록 조정)
    if original_ratio > target_ratio:
        # 가로가 더 긴 경우 → 세로를 맞추고 가로를 키움
        new_height = want_height
        new_width = int(image_width * (want_height / image_height))
    else:
        # 세로가 더 긴 경우 → 가로를 맞추고 세로를 키움
        new_width = want_width
        new_height = int(image_height * (want_width / image_width))

    # 리사이징 적용
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 2. 크롭 (중앙 기준)
    left = (new_width - want_width) // 2
    top = (new_height - want_height) // 2
    right = left + want_width
    bottom = top + want_height

    image = image.crop((left, top, right, bottom))

    return want_width, want_height, image







# 매장 소개 1:1 버전1
def combine_ads_store_intro_ver_1(store_name, road_name, content, image_width, image_height, image, weater, tag):
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1024)

    # 검은 배경 처리
    back_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_1_1_back.png") 
    # 효과 불러오기 및 리사이즈
    back_image = Image.open(back_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 1024
    new_height = 629
    back_image = back_image.resize((new_width, new_height))

    offset_x = 0
    offset_y = 0

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(back_image, (offset_x, offset_y), back_image)

    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Diphylleia-Regular.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "Diphylleia-Regular.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Diphylleia-Regular.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Diphylleia-Regular.ttf") 
    top_font_size = 36
    bottom_font_size = 80
    store_name_font_size = 96
    road_name_font_size = 36

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 텍스트를 '<br>'로 구분하여 줄 나누기
    # lines = content.split(' ')
    # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    content = content.strip('"')
    lines = content
    # print(content)

    if len(lines) > 0:
        top_line = lines
        lines_list = split_top_line(top_line, max_length=25)  # 반환값은 리스트
        
        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 447

        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비와 높이 계산
                text_bbox = top_font.getbbox(line)  # (left, top, right, bottom)
                text_width = text_bbox[2] - text_bbox[0]  # 너비
                text_height = 42  # 높이

                # 좌우 여백과 상하 여백 추가
                box_padding_x = 16  # 좌우 여백
                box_padding_y = 16  # 상하 여백

                # 좌표 계산
                box_x0 = (image_width - text_width) // 2 - box_padding_x  # 흰색 박스 시작 X 좌표
                box_y0 = top_text_y   # 흰색 박스 시작 Y 좌표
                box_x1 = (image_width + text_width) // 2 + box_padding_x  # 흰색 박스 끝 X 좌표
                box_y1 = top_text_y + text_height + box_padding_y   # 흰색 박스 끝 Y 좌표

                # 흰색 박스 그리기
                draw.rectangle([box_x0, box_y0, box_x1, box_y1], fill="#FFFFFF")

                # 중앙 정렬된 텍스트 그리기
                text_x = (image_width - text_width) // 2
                draw.text((text_x, top_text_y), line, font=top_font, fill="#000000")  # RGBA 적용

                # Y 좌표를 다음 줄로 이동
                top_text_y += text_height + box_padding_y * 2 + 5  # 박스 상하 여백 포함

    # 맨 위 정보 텍스트
    district_name = road_name.split(' ')[1]  # 동이름 추출
    today = datetime.now()
    weekday_number = today.weekday()  # 0: 월요일, 1: 화요일, ..., 6: 일요일

    # 숫자를 한글 요일로 매핑
    weekday_korean = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    text = f"{district_name} | {tag} | {weater} | {weekday_korean[weekday_number]}"  

    # 텍스트 출력 위치
    text_width = road_name_font.getbbox(text)[2]
    text_x = (image_width - text_width) // 2
    text_y = 150  # 세로 시작 위치

    # 텍스트 그리기
    draw.multiline_text(
        (text_x, text_y),  # 시작 좌표
        text,  # 텍스트 내용
        font=road_name_font,  # 폰트 
        fill="#FFFFFF",  # 텍스트 색상
    )

    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = (image_width - store_name_width) // 2
    store_name_y = 254
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="#FFFFFF")

    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"

# 매장 소개 1:1 버전2
def combine_ads_store_intro_ver_2(store_name, road_name, content, image_width, image_height, image, alignment="center"):
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1024)

    # 바탕 생성 및 합성
    # 티켓 처리
    tiket_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_1_1_vertical.png") 
    # sp_image 불러오기 및 리사이즈
    tiket_image = Image.open(tiket_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 571
    new_height = 1024
    tiket_image = tiket_image.resize((new_width, new_height))

    offset_x = 453
    offset_y = 0

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(tiket_image, (offset_x, offset_y), tiket_image)

    # 카메라
    camera_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_1_1_camera.png") 
    # sp_image 불러오기 및 리사이즈
    camera_image = Image.open(camera_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 127
    new_height = 82
    tiket_image = tiket_image.resize((new_width, new_height))

    offset_x = 35
    offset_y = 139

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(camera_image, (offset_x, offset_y), camera_image)


    top_path = os.path.join(root_path, "app", "static", "font", "GowunDodum-Regular.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "BMHANNA_11yrs_ttf.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "GowunDodum-Regular.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "DoHyeon-Regular.ttf") 

    top_font_size = 64
    bottom_font_size = (top_font_size * 5) / 8
    store_name_font_size = 40
    road_name_font_size = 40

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))
    

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    content = content.strip('"')
    max_chars_per_column = 9  # 한 칼럼 최대 글자 수
    lines = split_text_by_column(content, max_chars_per_column)
    
    if len(lines) > 0:
        font_size = top_font.size  # 폰트 크기 (X 좌표 증가를 위해 사용)

        # store_name의 전체 높이 계산 (한 글자씩 더해서 총 높이 구하기)
        total_height = sum(top_font.getbbox(char)[3] for char in lines[0]) + (len(lines[0]) - 1) * 1  # 간격 포함

        # X 좌표 중앙 정렬 (각 글자의 가로 폭을 고려)
        content_x_center = 849  # 원래 X 좌표 (기준)
        max_char_width = max(top_font.getbbox(char)[2] for char in "".join(lines))  # 가장 넓은 글자의 폭
        content_x = content_x_center - (max_char_width // 2)  # 중앙 정렬된 X 좌표

        # Y 좌표 시작점 (중앙 정렬)
        content_y = (image_height - total_height) // 2  # 이미지 높이 기준으로 중앙 정렬

        # 한 칼럼씩 세로로 배치
        for column_text in lines:
            for char in column_text:
                draw.text((content_x, content_y), char, font=top_font, fill="#FFFFFF")
                content_y += top_font.getbbox(char)[3]  # 글자 높이 + 간격

            content_x += font_size  # 새로운 X 좌표로 이동
            content_y = (image_height - total_height) // 2  # Y 좌표 초기화


    

    # store_name의 전체 높이 계산 (한 글자씩 더해서 총 높이 구하기)
    total_height = sum(store_name_font.getbbox(char)[3] for char in store_name) + (len(store_name) - 1) * 1  # 간격 포함

    # X 좌표 중앙 정렬 (각 글자의 가로 폭을 고려)
    store_name_x_center = 758  # 원래 X 좌표 (기준)
    max_char_width = max(store_name_font.getbbox(char)[2] for char in store_name)  # 가장 넓은 글자의 폭
    store_name_x = store_name_x_center - (max_char_width // 2)  # 중앙 정렬된 X 좌표

    # Y 좌표 시작점 (중앙 정렬)
    store_name_y = (image_height - total_height) // 2  # 이미지 높이 기준으로 중앙 정렬

    # 한 글자씩 세로로 배치 (중앙 정렬된 X 좌표 사용)
    for char in store_name:
        draw.text((store_name_x, store_name_y), char, font=store_name_font, fill="#FFFFFF")
        store_name_y += store_name_font.getbbox(char)[3] + 1  # 글자 높이 + 간격


    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_height = road_name_font.getbbox(road_name)[3]
    # road_name_x = (image_width - road_name_width) // 2
    road_name_x = 185
    road_name_y = 923
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill="#FFFFFF")

    # 선의 너비 및 위치 설정
    line_width = 161
    line_y = 100 # 위에서부터 197px 떨어진 위치
    line_x_start = 5
    line_x_end = line_x_start + line_width  # X 끝점
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=3) 

    line_width = 164
    line_y = 100 # 위에서부터 197px 떨어진 위치
    line_x_start = 497
    line_x_end = line_x_start + line_width  # X 끝점
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=3)

    line_height = 161  # 세로선의 길이
    line_x = 661  # x 좌표 고정
    line_y_start = 100  # 시작 y 좌표
    line_y_end = line_y_start + line_height  # 끝 y 좌표
    draw.line((line_x, line_y_start, line_x, line_y_end), fill="#FFFFFF", width=3)

    line_height = 161  # 세로선의 길이
    line_x = 648  # x 좌표 고정
    line_y_start = 833  # 시작 y 좌표
    line_y_end = line_y_start + line_height  # 끝 y 좌표
    draw.line((line_x, line_y_start, line_x, line_y_end), fill="#FFFFFF", width=3)

    line_width = 164
    line_y = 997 # 위에서부터 197px 떨어진 위치
    line_x_start = 484
    line_x_end = line_x_start + line_width  # X 끝점
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=3)

    line_width = 161
    line_y = 997 # 위에서부터 197px 떨어진 위치
    line_x_start = 5
    line_x_end = line_x_start + line_width  # X 끝점
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=3) 

    line_height = 161  # 세로선의 길이
    line_x = 5  # x 좌표 고정
    line_y_start = 833  # 시작 y 좌표
    line_y_end = line_y_start + line_height  # 끝 y 좌표
    draw.line((line_x, line_y_start, line_x, line_y_end), fill="#FFFFFF", width=3)

    line_height = 161  # 세로선의 길이
    line_x = 5  # x 좌표 고정
    line_y_start = 100  # 시작 y 좌표
    line_y_end = line_y_start + line_height  # 끝 y 좌표
    draw.line((line_x, line_y_start, line_x, line_y_end), fill="#FFFFFF", width=3)

    # 내부 사각형 흰 선 4개 중 y선 2개 먼저
    line_height = 788  # 세로선의 길이
    line_x = 19  # x 좌표 고정
    line_y_start = 139  # 시작 y 좌표
    line_y_end = line_y_start + line_height  # 끝 y 좌표
    draw.line((line_x, line_y_start, line_x, line_y_end), fill="#FFFFFF", width=3)

    line_height = 788  # 세로선의 길이
    line_x = 633  # x 좌표 고정
    line_y_start = 139  # 시작 y 좌표
    line_y_end = line_y_start + line_height  # 끝 y 좌표
    draw.line((line_x, line_y_start, line_x, line_y_end), fill="#FFFFFF", width=3)

    # 내부 사각형 흰 선 4재 중 나머지 x선
    line_width = 570
    line_y = 974 # 위에서부터 197px 떨어진 위치
    line_x_start = 35
    line_x_end = line_x_start + line_width  # X 끝점
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=3) 

    line_width = 570
    line_y = 129 # 위에서부터 197px 떨어진 위치
    line_x_start = 35
    line_x_end = line_x_start + line_width  # X 끝점
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=3) 


    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"

# 매장 소개 1:1 버전3
def combine_ads_store_intro_ver_3(store_name, road_name, content, image_width, image_height, image, alignment="center"):
    # print(image_width, image_height)
    root_path = os.getenv("ROOT_PATH", ".")
    # print(image)
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1024)

    # 바탕 생성 및 합성
    rectangle_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_1_1.png")
    rectangle = Image.open(rectangle_path).convert("RGBA")
    
    # 새로운 이미지 크기 계산
    new_height = max(image_height, rectangle.height)  # 기존 높이와 추가 높이 중 더 큰 값
    combined_background = Image.new("RGBA", (image_width, new_height), (0, 0, 0, 0))  # 투명 배경 생성
    
    # 기존 rectangle 이미지 복사
    combined_background.paste(rectangle, (0, 0))  # 상단에 원본 rectangle 붙이기
    
    # 원본 이미지와 새 배경 합성
    image = Image.alpha_composite(image, combined_background)

    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "SeoulNamsanEB.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "JejuHallasan.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    top_font_size = 32
    bottom_font_size = 32
    store_name_font_size = 36
    road_name_font_size = 48

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    content = content.strip('"')
    lines = content


    if len(lines) > 0:
        lines_list = split_top_line(lines, max_length=25)  # 반환값은 리스트

        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 151

        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비 계산
                top_text_width = top_font.getbbox(line)[2]
                top_text_height = top_font.getbbox(line)[3]  # 텍스트 높이 계산
                # 중앙 정렬 X 좌표 계산
                top_text_x = 96
                # 텍스트 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill="white")

                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = 96
    store_name_y = 69
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="white")

    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"



# 이벤트 1:1 버전1
def combine_ads_event(store_name, road_name, content, image_width, image_height, image, alignment="center"):
    # print(image_width, image_height)
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1024)

    # 바탕 생성 및 합성
    rectangle_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_1_1.png")
    rectangle = Image.open(rectangle_path).convert("RGBA")
    
    # 새로운 이미지 크기 계산
    new_height = max(image_height, rectangle.height)  # 기존 높이와 추가 높이 중 더 큰 값
    combined_background = Image.new("RGBA", (image_width, new_height), (0, 0, 0, 0))  # 투명 배경 생성
    
    # 기존 rectangle 이미지 복사
    combined_background.paste(rectangle, (0, 0))  # 상단에 원본 rectangle 붙이기
    
    # 원본 이미지와 새 배경 합성
    image = Image.alpha_composite(image, combined_background)

    sp_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "hot_imo.png") 

    # sp_image 불러오기 및 리사이즈
    sp_image = Image.open(sp_image_path).convert("RGBA")
    original_width, original_height = sp_image.size

    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 234
    new_height = 234
    sp_image = sp_image.resize((new_width, new_height))

    # 4번 위치 (하단 오른쪽) 중심 좌표 계산
    offset_x = (image_width * 3 // 4) - (new_width // 2)  # 4등분 했을 때 하단 오른쪽 중심 X
    offset_y = (image_height * 3 // 4) - (new_height // 2)  # 4등분 했을 때 하단 오른쪽 중심 Y

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(sp_image, (offset_x, offset_y), sp_image)

    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "JalnanGothicTTF.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    top_font_size = 55
    bottom_font_size = 78
    store_name_font_size = 48
    road_name_font_size = 36

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 텍스트를 '<br>'로 구분하여 줄 나누기
    # lines = content.split(' ')
    # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    lines = re.findall(r':\s*(.*)', content)  # ':' 이후의 텍스트만 추출
    lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    # print(lines)

    line_width = 721
    line_y = 100 # 위에서부터 197px 떨어진 위치
    line_x_start = 153
    line_x_end = line_x_start + line_width  # X 끝점
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=3)

    line_width = 721
    line_y = 188 # 위에서부터 197px 떨어진 위치
    line_x_start = 153
    line_x_end = line_x_start + line_width  # X 끝점
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=3)

    if len(lines) > 0:
        top_line = lines[0].strip()
        lines_list = split_top_line(top_line, max_length=20)  # 반환값은 리스트

        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 116

        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비 계산
                top_text_width = top_font.getbbox(line)[2]
                top_text_height = top_font.getbbox(line)[3]  # 텍스트 높이 계산
                # 중앙 정렬 X 좌표 계산
                top_text_x = (image_width - 44 - 44 - top_text_width) // 2 + 44

                # 텍스트 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill=(255, 255, 255))

                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    # 하단 텍스트 추가
    bottom_lines = lines[1:]  # 첫 번째 줄을 제외한 나머지
    line_height = bottom_font.getbbox("A")[3] + 4
    text_y = 231

    for line in bottom_lines:
        line = line.strip()
        # 하단 줄을 분리하여 20자 이상일 경우 나눔
        split_lines = split_top_line(line, max_length=13)

        for i, sub_line in enumerate(split_lines):
            sub_line = sub_line.strip()
            text_width = bottom_font.getbbox(sub_line)[2]

            if alignment == "center":
                text_x = (image_width - text_width) // 2
            elif alignment == "left":
                text_x = 10
            elif alignment == "right":
                text_x = image_width - text_width - 10
            else:
                raise ValueError("Invalid alignment option. Choose 'center', 'left', or 'right'.")

            # 현재 줄 렌더링, 색상은 colors[i % len(colors)]로 선택
            draw.text((text_x, text_y), sub_line, font=bottom_font, fill="#FFFB00")
            text_y += line_height  # 다음 줄로 이동

    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_height = store_name_font.getbbox(store_name)[3]
    store_name_x = (image_width - store_name_width) // 2
    store_name_y = 870
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="white")

    fill_color = (255, 255, 255, 58)  # RGBA

    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_height = road_name_font.getbbox(road_name)[3]
    road_name_x = (image_width - road_name_width) // 2
    road_name_y = 925
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill=fill_color)


    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"

# 이벤트 1:1 버전2
def combine_ads_event_ver2(store_name, road_name, content, image_width, image_height, image, alignment="center"):
    # print(image_width, image_height)
    root_path = os.getenv("ROOT_PATH", ".")
    # print(image)
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1024)

    # 바탕 생성 및 합성
    rectangle_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_1_1.png")
    rectangle = Image.open(rectangle_path).convert("RGBA")
    
    # 새로운 이미지 크기 계산
    new_height = max(image_height, rectangle.height)  # 기존 높이와 추가 높이 중 더 큰 값
    combined_background = Image.new("RGBA", (image_width, new_height), (0, 0, 0, 0))  # 투명 배경 생성
    
    # 기존 rectangle 이미지 복사
    combined_background.paste(rectangle, (0, 0))  # 상단에 원본 rectangle 붙이기
    
    # 원본 이미지와 새 배경 합성
    image = Image.alpha_composite(image, combined_background)

    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "SeoulNamsanEB.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "JejuHallasan.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    top_font_size = 40
    bottom_font_size = 32
    store_name_font_size = 32
    road_name_font_size = 48

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 텍스트를 '<br>'로 구분하여 줄 나누기
    # lines = content.split(' ')
    # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    lines = re.findall(r':\s*(.*)', content)  # ':' 이후의 텍스트만 추출
    lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    if len(lines) > 0:
        top_line = lines[0].strip()
        lines_list = split_top_line(top_line, max_length=15)  # 반환값은 리스트

        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 121

        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비 계산
                top_text_width = top_font.getbbox(line)[2]
                top_text_height = top_font.getbbox(line)[3]  # 텍스트 높이 계산
                # 중앙 정렬 X 좌표 계산
                top_text_x = 96
                # 텍스트 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill="white")

                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    # 하단 텍스트 추가
    bottom_lines = lines[1:]  # 첫 번째 줄을 제외한 나머지
    line_height = bottom_font.getbbox("A")[3] + 4
    text_y = 336

    for line in bottom_lines:
        line = line.strip()
        # 하단 줄을 분리하여 20자 이상일 경우 나눔
        split_lines = split_top_line(line, max_length=25)

        for i, sub_line in enumerate(split_lines):
            sub_line = sub_line.strip()
            text_width = bottom_font.getbbox(sub_line)[2]

            bottom_text_x = 96

            draw.text((bottom_text_x, text_y), line, font=top_font, fill="white")
            text_y += line_height  # 다음 줄로 이동

    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = 96
    store_name_y = 69
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="white")

    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"

# 이벤트 1:1 버전3
def combine_ads_event_ver3(store_name, road_name, content, image_width, image_height, image, alignment="center"):
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1024)

    # 바탕 생성 및 합성
    rectangle_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_1_1_top.png")
    rectangle = Image.open(rectangle_path).convert("RGBA")
    
    # Rectangle 이미지 크기 확인
    rectangle_width, rectangle_height = rectangle.size

    # 투명 배경 생성: 이미지2 하단에 추가 (전체 높이 1024 맞춤)
    transparent_height = image_height - rectangle_height
    transparent_background = Image.new("RGBA", (rectangle_width, transparent_height), (0, 0, 0, 0))  # 투명 배경 생성

    # Rectangle과 투명 배경 합성
    combined_rectangle = Image.new("RGBA", (rectangle_width, image_height), (0, 0, 0, 0))  # 전체 크기: 1024x1024
    combined_rectangle.paste(rectangle, (0, 0))  # Rectangle 상단 배치
    combined_rectangle.paste(transparent_background, (0, rectangle_height))  # 투명 배경 하단 배치

    # 이미지1(image)와 Rectangle 합성
    image = Image.alpha_composite(image, combined_rectangle)

    # 바탕 생성 및 합성
    rectangle_bottom_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_1_1_bottom.png")
    rectangle_bottom = Image.open(rectangle_bottom_path).convert("RGBA")

    # Rectangle 이미지 크기 확인
    rectangle_bottom_width, rectangle_bottom_height = rectangle_bottom.size

    # 투명 배경 생성: 이미지2 상단에 추가 (전체 높이 1024 맞춤)
    transparent_height = image_height - rectangle_bottom_height
    transparent_background = Image.new("RGBA", (rectangle_bottom_width, transparent_height), (0, 0, 0, 0))  # 투명 배경 생성

    # Rectangle과 투명 배경 합성 (투명 배경 먼저, Rectangle 위에 배치)
    combined_rectangle = Image.new("RGBA", (rectangle_bottom_width, image_height), (0, 0, 0, 0))  # 전체 크기: 1024x1024
    combined_rectangle.paste(transparent_background, (0, 0))  # 투명 배경 상단 배치
    combined_rectangle.paste(rectangle_bottom, (0, transparent_height), mask=rectangle_bottom)  # Rectangle 하단 배치

    # 이미지1(image)와 Rectangle 합성
    image = Image.alpha_composite(image, combined_rectangle)

    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    base_copy_right_path = os.path.join(root_path, "app", "static", "font", "DoHyeon-Regular.otf")

    top_font_size = 55
    bottom_font_size = 64
    store_name_font_size = 40
    road_name_font_size = 36
    base_copy_right_font_size = 32

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))
    base_copy_right_font = ImageFont.truetype(base_copy_right_path, int(base_copy_right_font_size))
    

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 기본 문구 붙여 넣기
    base_copyright = "이벤트"
    base_copyright_width = base_copy_right_font.getbbox(base_copyright)[2]
    base_copyright_height = base_copy_right_font.getbbox(base_copyright)[3]
    base_copyright_x = 77
    base_copyright_y = 596
    padding = 16

    background_x0 = base_copyright_x - padding
    background_y0 = base_copyright_y - padding
    background_x1 = base_copyright_x + base_copyright_width + padding
    background_y1 = base_copyright_y + base_copyright_height + padding

    draw.rectangle(
        [background_x0, background_y0, background_x1, background_y1],
        fill="#09C5FE"  # 배경색
    )

    draw.text(
        (base_copyright_x, base_copyright_y),
        base_copyright,
        font=base_copy_right_font,
        fill=(255, 255, 255)  # 텍스트 색상
    )

    lines = re.findall(r':\s*(.*)', content)  # ':' 이후의 텍스트만 추출
    lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    if len(lines) > 0:
        top_line = lines[0].strip()
        lines_list = split_top_line(top_line, max_length=20)  # 반환값은 리스트

        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 86

        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비 계산
                top_text_width = top_font.getbbox(line)[2]
                top_text_height = top_font.getbbox(line)[3]  # 텍스트 높이 계산
                # 중앙 정렬 X 좌표 계산
                top_text_x = (image_width - 44 - 44 - top_text_width) // 2 + 44
                # 텍스트 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill=(255, 255, 255, 10))

                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    # 하단 텍스트 추가
    bottom_lines = lines[1:]  # 첫 번째 줄을 제외한 나머지

    for line in bottom_lines:
        line = line.strip()
        # 하단 줄을 분리하여 20자 이상일 경우 나눔
        split_lines = split_top_line(line, max_length=13)

        for i, sub_line in enumerate(split_lines):
            sub_line = sub_line.strip()
            text_width = bottom_font.getbbox(sub_line)[2]

            top_text_x = 77
            top_text_y = 678
            # 현재 줄 렌더링
            draw.text((top_text_x, top_text_y), line, font=top_font, fill=(255, 255, 255))  # RGBA 적용
                
            # Y 좌표를 다음 줄로 이동
            top_text_y += top_font.getbbox("A")[3] + 5
    
    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_height = store_name_font.getbbox(store_name)[3]
    store_name_x = (image_width - store_name_width) // 2
    store_name_y = 895
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill=(255, 255, 255))

    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_height = road_name_font.getbbox(road_name)[3]
    road_name_x = (image_width - road_name_width) // 2
    road_name_y = 942
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill=(255, 255, 255))


    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"



# 매장 소개 4:7 버전1
def combine_ads_intro_4_7(store_name, road_name, content, image_width, image_height, image):
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=815, want_height=1091)

    # 포스터 처리 처리
    poster_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_4_7_poster.png") 
    # sp_image 불러오기 및 리사이즈
    poster_image = Image.open(poster_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 1024
    new_height = 1792
    poster_image = poster_image.resize((new_width, new_height))

    # 전달받은 이미지를 포스터 위에 배치
    offset_x = 42  # 포스터의 왼쪽에서 42px
    offset_y = 55  # 포스터의 위쪽에서 55px
    poster_image.paste(image, (offset_x, offset_y), image)
    image = poster_image


    # # 오래된 효과 처리
    # effect_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_4_7_old_effect.png") 
    # # 효과 불러오기 및 리사이즈
    # effect_image = Image.open(effect_image_path).convert("RGBA")
 
    # # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    # new_width = 1024
    # new_height = 1792
    # effect_image = effect_image.resize((new_width, new_height))

    # offset_x = 0
    # offset_y = 0

    # # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    # image.paste(effect_image, (offset_x, offset_y), effect_image)


    # QR 처리
    qr_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_4_7_qr.png") 
    # 효과 불러오기 및 리사이즈
    qr_image = Image.open(qr_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 146
    new_height = 146
    qr_image = qr_image.resize((new_width, new_height))

    offset_x = 46
    offset_y = 1552

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(qr_image, (offset_x, offset_y), qr_image)


    # 세로 글자 처리
    vertical_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_4_7_vertical.png") 
    # 효과 불러오기 및 리사이즈
    vertical_image = Image.open(vertical_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 167
    new_height = 1216
    vertical_image = vertical_image.resize((new_width, new_height))

    offset_x = 857
    offset_y = 55

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(vertical_image, (offset_x, offset_y), vertical_image)

    # 의문 글자 처리
    word_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_4_7_unkown_word.png") 
    # sp_image 불러오기 및 리사이즈
    word_image = Image.open(word_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 523
    new_height = 96
    word_image = word_image.resize((new_width, new_height))

    offset_x = 289
    offset_y = 1577

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(word_image, (offset_x, offset_y), word_image)


    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "BMHANNA_11yrs_ttf.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "DoHyeon-Regular.otf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    top_font_size = 64
    bottom_font_size = 80
    store_name_font_size = 40
    road_name_font_size = 40

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 텍스트를 '<br>'로 구분하여 줄 나누기
    # lines = content.split(' ')
    # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    content = content.strip('"')
    lines = content
    # print(content)
    if len(lines) > 0:
        top_line = lines
        lines_list = split_top_line(top_line, max_length=18)  # 반환값은 리스트
        
        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 1201

        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비 계산
                top_text_width = top_font.getbbox(line)[2]
                
                # 좌우 여백을 고려한 중앙 정렬 X 좌표 계산
                top_text_x = 50
                
                # 현재 줄 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill="#656565")  # RGBA 적용
                
                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    text = f"{store_name}\n{road_name}"  # 줄바꿈(\n)으로 가게명과 주소를 한 번에 처리

    # 텍스트 출력 위치
    text_x = 50  # 가로 위치
    text_y = 1380  # 세로 시작 위치

    # 텍스트 그리기
    draw.multiline_text(
        (text_x, text_y),  # 시작 좌표
        text,  # 텍스트 내용
        font=store_name_font,  # 폰트 (두 텍스트의 폰트를 동일하게 설정)
        fill="#000000",  # 텍스트 색상
        spacing=10  # 줄 간격
    )


    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"

# 매장 소개 4:7 버전2
def combine_ads_intro_4_7_ver2(store_name, road_name, content, image_width, image_height, image, weater, tag):
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1792)

    # 검은 배경 처리
    back_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_black_back.png") 
    # 효과 불러오기 및 리사이즈
    back_image = Image.open(back_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 1024
    new_height = 1023
    back_image = back_image.resize((new_width, new_height))

    offset_x = 0
    offset_y = 0

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(back_image, (offset_x, offset_y), back_image)

    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Diphylleia-Regular.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "Diphylleia-Regular.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Diphylleia-Regular.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Diphylleia-Regular.ttf") 
    top_font_size = 44
    bottom_font_size = 80
    store_name_font_size = 96
    road_name_font_size = 36

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 텍스트를 '<br>'로 구분하여 줄 나누기
    # lines = content.split(' ')
    # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    content = content.strip('"')
    lines = content
    # print(content)

    if len(lines) > 0:
        top_line = lines
        lines_list = split_top_line(top_line, max_length=18)  # 반환값은 리스트
        
        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 665

        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비와 높이 계산
                text_bbox = top_font.getbbox(line)  # (left, top, right, bottom)
                text_width = text_bbox[2] - text_bbox[0]  # 너비
                text_height = 84  # 높이

                # 좌우 여백과 상하 여백 추가
                box_padding_x = 16  # 좌우 여백
                box_padding_y = 2  # 상하 여백

                # 좌표 계산
                box_x0 = (image_width - text_width) // 2 - box_padding_x  # 흰색 박스 시작 X 좌표
                box_y0 = top_text_y - box_padding_y  # 흰색 박스 시작 Y 좌표
                box_x1 = (image_width + text_width) // 2 + box_padding_x  # 흰색 박스 끝 X 좌표
                box_y1 = top_text_y + text_height + box_padding_y  # 흰색 박스 끝 Y 좌표

                # 흰색 박스 그리기
                draw.rectangle([box_x0, box_y0, box_x1, box_y1], fill="#FFFFFF")

                # 중앙 정렬된 텍스트 그리기
                text_x = (image_width - text_width) // 2
                draw.text((text_x, top_text_y), line, font=top_font, fill="#000000")  # RGBA 적용

                # Y 좌표를 다음 줄로 이동
                top_text_y += text_height + box_padding_y * 2 + 5  # 박스 상하 여백 포함

    # 맨 위 정보 텍스트
    district_name = road_name.split(' ')[1]  # 동이름 추출
    today = datetime.now()
    weekday_number = today.weekday()  # 0: 월요일, 1: 화요일, ..., 6: 일요일

    # 숫자를 한글 요일로 매핑
    weekday_korean = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    text = f"{district_name} | {tag} | {weater} | {weekday_korean[weekday_number]}"  

    # 텍스트 출력 위치
    text_width = road_name_font.getbbox(text)[2]
    text_x = (image_width - text_width) // 2
    text_y = 368  # 세로 시작 위치

    # 텍스트 그리기
    draw.multiline_text(
        (text_x, text_y),  # 시작 좌표
        text,  # 텍스트 내용
        font=road_name_font,  # 폰트 
        fill="#FFFFFF",  # 텍스트 색상
    )

    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = (image_width - store_name_width) // 2
    store_name_y = 472
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="#FFFFFF")

    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"

# 매장 소개 4:7 버전3
# def combine_ads_intro_4_7_ver3(store_name, road_name, content, image_width, image_height, image):
#     root_path = os.getenv("ROOT_PATH", ".")
    
#     # RGBA 모드로 변환
#     if image.mode != "RGBA":
#         image = image.convert("RGBA")

#     # 이미지 크기 확인 및 리사이즈
#     image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1792)

#     # # 검은 배경 처리
#     # back_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_4_7_all_black.png") 
#     # # 효과 불러오기 및 리사이즈
#     # back_image = Image.open(back_image_path).convert("RGBA")
 
#     # # sp_image
#     # new_width = 1024
#     # new_height = 1792
#     # back_image = back_image.resize((new_width, new_height))

#     # offset_x = 0
#     # offset_y = 0

#     # # sp_image를 기존 이미지 위에 합성 (투명도 제거)
#     # image.paste(back_image, (offset_x, offset_y), back_image)

#     # 텍스트 설정
#     top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
#     bottom_path = os.path.join(root_path, "app", "static", "font", "BMHANNA_11yrs_ttf.ttf") 
#     store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
#     road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 

#     top_font_size = 48
#     bottom_font_size = 80
#     store_name_font_size = 128
#     road_name_font_size = 40

#     # 폰트 설정
#     top_font = ImageFont.truetype(top_path, int(top_font_size))
#     bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
#     store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
#     road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

#     # 텍스트 렌더링 (합성 작업 후)
#     draw = ImageDraw.Draw(image)

#     # 텍스트를 '<br>'로 구분하여 줄 나누기
#     # lines = content.split(' ')
#     # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
#     # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
#     # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

#     content = content.strip('"')
#     lines = content
#     # print(content)
#     if len(lines) > 0:
#         top_line = lines
#         lines_list = split_top_line(top_line, max_length=15)  # 반환값은 리스트
        
#         # 첫 번째 줄 렌더링 Y 좌표 설정
#         top_text_y = 878

#         for i, line in enumerate(lines_list):
#             if line:  # 줄이 존재할 경우만 처리
#                 # 텍스트 너비 계산
#                 top_text_width = top_font.getbbox(line)[2]
                
#                 # 좌우 여백을 고려한 중앙 정렬 X 좌표 계산
#                 top_text_x = 408
                
#                 # 현재 줄 렌더링
#                 text_x = (image_width - top_text_width) // 2
#                 draw.text((text_x, top_text_y), line, font=top_font, fill="#FFFFFF")  # RGBA 적용
                
#                 # Y 좌표를 다음 줄로 이동
#                 top_text_y += top_font.getbbox("A")[3] + 10


#     # 텍스트 크기 측정
#     store_name_bbox = store_name_font.getbbox(store_name)
#     store_name_width = store_name_bbox[2]  # 텍스트 너비
#     store_name_height = store_name_bbox[3]  # 텍스트 높이
#     store_name_y = 622

#     # 배경 네모 크기 계산 (좌우 50px, 위아래 23px 추가)
#     bg_width = store_name_width + 50
#     bg_height = store_name_height + 23

#     # 네모 배경의 좌표 설정
#     bg_x1 = (image_width - bg_width) // 2  # 왼쪽 X 좌표
#     bg_x2 = bg_x1 + bg_width  # 오른쪽 X 좌표
#     bg_y1 = store_name_y - 23 // 2  # 위쪽 Y 좌표 (중앙 정렬)
#     bg_y2 = bg_y1 + bg_height  # 아래쪽 Y 좌표

#     # 검은색 네모 배경 그리기
#     draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=(0, 0, 0, 60))

#     # 텍스트를 배경 위에 중앙 배치
#     store_name_x = (image_width - store_name_width) // 2
#     draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="#FFFFFF")

    
#     # 텍스트 크기 측정
#     road_name_bbox = road_name_font.getbbox(road_name)
#     road_name_width = road_name_bbox[2]  # 텍스트 너비
#     road_name_height = road_name_bbox[3]  # 텍스트 높이
#     road_name_y = 1624

#     # 배경 네모 크기 계산 (좌우 50px, 위아래 23px 추가)
#     bg_width = road_name_width + 81
#     bg_height = road_name_height + 18

#     # 네모 배경의 좌표 설정
#     bg_x1 = (image_width - bg_width) // 2  # 왼쪽 X 좌표
#     bg_x2 = bg_x1 + bg_width  # 오른쪽 X 좌표
#     bg_y1 = road_name_y - 23 // 2  # 위쪽 Y 좌표 (중앙 정렬)
#     bg_y2 = bg_y1 + bg_height  # 아래쪽 Y 좌표

#     # 검은색 네모 배경 그리기
#     draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=(0, 0, 0, 60))

#     # 텍스트를 배경 위에 중앙 배치
#     road_name_x = (image_width - road_name_width) // 2
#     draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill="#FFFFFF")



#     # 선의 너비 및 위치 설정
#     line_width = 594
#     line_y = 836  # 위에서부터 197px 떨어진 위치
#     line_x_start = 216
#     line_x_end = line_x_start + line_width  # X 끝점
#     draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=2)  # width 값으로 선 두께 조절 가능

#     # 이미지 메모리에 저장
#     buffer = BytesIO()
#     image.save(buffer, format="PNG")
#     buffer.seek(0)

#     # Base64 인코딩
#     base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

#     return f"data:image/png;base64,{base64_image}"

# 매장 소개 4:7 버전4
def combine_ads_intro_4_7_ver4(store_name, road_name, content, image_width, image_height, image):
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1792)

    # 검은 배경 처리
    back_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_4_7_back_60_black.png") 
    # 효과 불러오기 및 리사이즈
    back_image = Image.open(back_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 1024
    new_height = 1058
    back_image = back_image.resize((new_width, new_height))

    offset_x = 0
    offset_y = 0

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(back_image, (offset_x, offset_y), back_image)


    # 검은 배경 처리
    back_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_4_7_back_60_black_down.png") 
    # 효과 불러오기 및 리사이즈
    back_image = Image.open(back_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 1024
    new_height = 342
    back_image = back_image.resize((new_width, new_height))

    offset_x = 0
    offset_y = 1450

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(back_image, (offset_x, offset_y), back_image)




    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "Diphylleia-Regular.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    top_font_size = 80
    bottom_font_size = 80
    store_name_font_size = 110
    road_name_font_size = 48

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 텍스트를 '<br>'로 구분하여 줄 나누기
    # lines = content.split(' ')
    # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    content = content.strip('"')
    lines = content
    # print(content)

    if len(lines) > 0:
        top_line = lines
        lines_list = split_top_line(top_line, max_length=9)  # 반환값은 리스트
        
        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 484

        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비와 높이 계산
                text_bbox = top_font.getbbox(line)  # (left, top, right, bottom)
                text_width = text_bbox[2] - text_bbox[0]  # 너비
                text_height = 84  # 높이

                # 중앙 정렬된 텍스트 그리기
                text_x = 84
                draw.text((text_x, top_text_y), line, font=top_font, fill="#FFFFFF")  # RGBA 적용

                # Y 좌표를 다음 줄로 이동
                top_text_y += text_height + 5  # 박스 상하 여백 포함

    

    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = 80
    store_name_y = 236
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="#FFFFFF")

    # store_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_x = (image_width - road_name_width) // 2
    road_name_y = 1598
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill="#FFFFFF")


    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"


# 매장 소개 4:7 버전5
def combine_ads_intro_4_7_ver5(store_name, road_name, content, image_width, image_height, image):
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1207)

    # 새로운 캔버스 생성 (1024 x (1384 + 585) = 1969)
    new_height = 1792 # 기존 이미지 + 하단 흰색 배경
    new_image = Image.new("RGBA", (1024, new_height), (255, 255, 255, 255))  # 흰색 배경

    # 기존 이미지 상단 배치 (좌표: (0, 0))
    new_image.paste(image, (0, 0))
    image = new_image
    
    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "Diphylleia-Regular.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Thin.otf") 
    top_font_size = 48
    bottom_font_size = 80
    store_name_font_size = 128
    road_name_font_size = 36

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 텍스트를 '<br>'로 구분하여 줄 나누기
    # lines = content.split(' ')
    # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    content = content.strip('"')
    lines = content
    # print(content)

    if len(lines) > 0:
        top_line = lines
        lines_list = split_top_line(top_line, max_length=18)  # 반환값은 리스트
        
        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 1463

        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비와 높이 계산
                text_bbox = top_font.getbbox(line)  # (left, top, right, bottom)
                text_width = text_bbox[2] - text_bbox[0]  # 너비
                text_height = 88  # 높이

                # 중앙 정렬된 텍스트 그리기
                text_x = 88
                draw.text((text_x, top_text_y), line, font=top_font, fill="#000000")  # RGBA 적용

                # Y 좌표를 다음 줄로 이동
                top_text_y += 48 + 5  # 박스 상하 여백 포함

    

    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = 88
    store_name_y = 1318
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="#000000")

    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_x = (image_width - road_name_width) // 2
    road_name_y = 1698
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill="#000000")

    # 선의 너비 및 위치 설정
    line_y = 1716  # 선의 Y 좌표
    line_x_start = 0  # 선의 시작점 (왼쪽 끝)
    line_x_end = road_name_x - 40  # 선의 끝점 (road_name 시작 위치에서 40px 왼쪽)

    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#000000", width=2)  # width 값으로 선 두께 조절 가능


    # 선의 너비 및 위치 설정
    line_y = 1716  # 선의 Y 좌표
    line_x_start = road_name_x + road_name_width + 40
    line_x_end = 1024   # 선의 끝점 (road_name 시작 위치에서 40px 왼쪽)

    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#000000", width=2)  # width 값으로 선 두께 조절 가능



    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"


# 매장 소개 4:7 버전6
def combine_ads_intro_4_7_ver6(store_name, road_name, content, image_width, image_height, image):
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=730, want_height=730)

    # 새로운 캔버스 생성 
    new_height = 978 # 기존 이미지 + 하단 흰색 배경
    new_image = Image.new("RGBA", (730, new_height), (255, 255, 255, 255))  # 흰색 배경

    # 기존 이미지 상단 배치 (좌표: (0, 0))
    new_image.paste(image, (0, 0))
    image = new_image


    # 포스터 처리 처리
    poster_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_4_7_back_white.png") 
    # sp_image 불러오기 및 리사이즈
    poster_image = Image.open(poster_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 1024
    new_height = 1792
    poster_image = poster_image.resize((new_width, new_height))

    # 전달받은 이미지를 포스터 위에 배치
    offset_x = 147  # 포스터의 왼쪽에서 42px
    offset_y = 367  # 포스터의 위쪽에서 55px
    poster_image.paste(image, (offset_x, offset_y), image)
    image = poster_image


    # QR 처리
    qr_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_4_7_ver_6_site_icon.png") 
    # 효과 불러오기 및 리사이즈
    qr_image = Image.open(qr_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 44
    new_height = 44
    qr_image = qr_image.resize((new_width, new_height))

    offset_x = 490
    offset_y = 1126

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(qr_image, (offset_x, offset_y), qr_image)

    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "BMHANNA_11yrs_ttf.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "DoHyeon-Regular.otf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 

    top_font_size = 36
    bottom_font_size = 80
    store_name_font_size = 40
    road_name_font_size = 30
    top_store_name_font_size = 30

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))
    top_store_name_font = ImageFont.truetype(road_name_path, int(top_store_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 텍스트를 '<br>'로 구분하여 줄 나누기
    # lines = content.split(' ')
    # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    content = content.strip('"')
    lines = content

    if len(lines) > 0:
        top_line = lines
        lines_list = split_top_line(top_line, max_length=18)  # 반환값은 리스트

        # 첫 번째 줄 Y 좌표 설정 (1478)
        top_text_y = 1478

        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비 계산
                top_text_width = top_font.getbbox(line)[2]

                # 우측 정렬 X 좌표 계산 (오른쪽에서 149px 떨어진 위치)
                top_text_x = 1024 - 149 - top_text_width

                # 현재 줄 렌더링 (우측 정렬)
                draw.text((top_text_x, top_text_y), line, font=top_font, fill="#000000")

                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5


    
    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = (1024 - store_name_width) // 2
    store_name_y = 1200
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="#C4052A")


    # top_store_name 추가
    top_store_name_width = top_store_name_font.getbbox(store_name)[2]
    top_store_name_x = 119
    top_store_name_y = 183
    draw.text((top_store_name_x, top_store_name_y), store_name, font=top_store_name_font, fill="#000000")


    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_x = (1024 - road_name_width) // 2
    road_name_y = 1277
    color = (0, 0, 0, 204)  # 검은색 + 80% 투명도
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill=color)

    # 선의 너비 및 위치 설정
    line_with = 189
    line_y = 1660  # 선의 Y 좌표
    line_x_start = 657  # 선의 시작점 (왼쪽 끝)
    line_x_end = line_x_start + line_with  # 선의 끝점 (road_name 시작 위치에서 40px 왼쪽)
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#C4052A", width=4)  # width 값으로 선 두께 조절 가능

    # 선의 너비 및 위치 설정
    line_with = 189
    line_y = 243  # 선의 Y 좌표
    line_x_start = 119  # 선의 시작점 (왼쪽 끝)
    line_x_end = line_x_start + line_with  # 선의 끝점 (road_name 시작 위치에서 40px 왼쪽)
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#C4052A", width=4)  # width 값으로 선 두께 조절 가능

    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"


# 매장 소개 4:7 버전7
def combine_ads_intro_4_7_ver7(store_name, road_name, content, image_width, image_height, image):
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1792)

    # 검은 배경 처리
    back_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_4_7_ver_7_back_gray.png") 
    # 효과 불러오기 및 리사이즈
    back_image = Image.open(back_image_path).convert("RGBA")
 
    # sp_image
    new_width = 1024
    new_height = 1792
    back_image = back_image.resize((new_width, new_height))

    offset_x = 0
    offset_y = 0

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(back_image, (offset_x, offset_y), back_image)



    # QR 처리
    qr_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_4_7_ver_7_clock.png") 
    # 효과 불러오기 및 리사이즈
    qr_image = Image.open(qr_image_path).convert("RGBA")

    offset_x = 97
    offset_y = 1442

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(qr_image, (offset_x, offset_y), qr_image)

    # QR 처리
    qr_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_4_7_ver_7_site.png") 
    # 효과 불러오기 및 리사이즈
    qr_image = Image.open(qr_image_path).convert("RGBA")

    offset_x = 97
    offset_y = 1374

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(qr_image, (offset_x, offset_y), qr_image)




    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "BMHANNA_11yrs_ttf.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 

    top_font_size = 40
    bottom_font_size = 80
    store_name_font_size = 48
    road_name_font_size = 40

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 텍스트를 '<br>'로 구분하여 줄 나누기
    # lines = content.split(' ')
    # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    content = content.strip('"')
    lines = content
    # print(content)
    if len(lines) > 0:
        top_line = lines
        lines_list = split_top_line(top_line, max_length=15)  # 반환값은 리스트
        
        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 1442

        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비 계산
                top_text_width = top_font.getbbox(line)[2]
                
                # 좌우 여백을 고려한 중앙 정렬 X 좌표 계산
                top_text_x = 408
                
                # 현재 줄 렌더링
                text_x = 157
                draw.text((text_x, top_text_y), line, font=top_font, fill="#FFFFFF")  # RGBA 적용
                
                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 10


    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = 626
    store_name_y = 100
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="#FFFFFF")

    # store_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_x = 157
    road_name_y = 1370
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill="#FFFFFF")

    # 선의 너비 및 위치 설정
    line_width = 477
    line_y = 120 # 위에서부터 197px 떨어진 위치
    line_x_start = 80
    line_x_end = line_x_start + line_width  # X 끝점
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=5)

    # 선의 너비 및 위치 설정
    line_width = 477
    line_y = 1667 # 위에서부터 197px 떨어진 위치
    line_x_start = 467
    line_x_end = line_x_start + line_width  # X 끝점
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=5)

    line_height = 1142  # 세로선의 길이
    line_x = 80  # x 좌표 고정
    line_y_start = 120  # 시작 y 좌표
    line_y_end = line_y_start + line_height  # 끝 y 좌표
    draw.line((line_x, line_y_start, line_x, line_y_end), fill="#FFFFFF", width=5)

    line_height = 1142  # 세로선의 길이
    line_x = 939  # x 좌표 고정
    line_y_start = 569  # 시작 y 좌표
    line_y_end = line_y_start + line_height  # 끝 y 좌표
    draw.line((line_x, line_y_start, line_x, line_y_end), fill="#FFFFFF", width=5)

    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"









# 이벤트 4:7 버전1
def combine_ads_event_4_7(store_name, road_name, content, image_width, image_height, image):
    # print(image_width, image_height)
    root_path = os.getenv("ROOT_PATH", ".")
    # print(image)
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1792)

    # 바탕 생성 및 합성
    rectangle_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_4_7.png")
    rectangle = Image.open(rectangle_path).convert("RGBA")
    
    # Rectangle 이미지 크기 확인
    rectangle_width, rectangle_height = rectangle.size

    # 투명 배경 생성: 이미지2 하단에 추가 (전체 높이 1792로 맞춤)
    transparent_height = image_height - rectangle_height
    transparent_background = Image.new("RGBA", (rectangle_width, transparent_height), (0, 0, 0, 0))  # 투명 배경 생성

    # Rectangle과 투명 배경 합성
    combined_rectangle = Image.new("RGBA", (rectangle_width, image_height), (0, 0, 0, 0))  # 전체 크기: 1024x1792
    combined_rectangle.paste(rectangle, (0, 0))  # Rectangle 상단 배치
    combined_rectangle.paste(transparent_background, (0, rectangle_height))  # 투명 배경 하단 배치

    # 이미지1(image)와 Rectangle 합성
    image = Image.alpha_composite(image, combined_rectangle)


    # 하단 배경
    bg_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_4_7_bg2.png") 
    # 불러오기 및 리사이즈
    bg_image = Image.open(bg_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 1024
    new_height = 342
    bg_image = bg_image.resize((new_width, new_height))

    offset_x = 0
    offset_y = 1450

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(bg_image, (offset_x, offset_y), bg_image)






    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    top_font_size = 110
    bottom_font_size = 84
    store_name_font_size = 48
    road_name_font_size = 48

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 텍스트를 '<br>'로 구분하여 줄 나누기
    # lines = content.split(' ')
    # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    lines = re.findall(r':\s*(.*)', content)  # ':' 이후의 텍스트만 추출
    lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    # print(lines)

    if len(lines) > 0:
        top_line = lines[0].strip()
        lines_list = split_top_line(top_line, max_length=8)  # 반환값은 리스트

        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 147

        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 중앙 정렬 X 좌표 계산
                top_text_x = 76
                # 텍스트 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill=(255, 255, 255, 10))
                # print(line)
                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    # 하단 텍스트 추가
    bottom_lines = lines[1:]  # 첫 번째 줄을 제외한 나머지
    line_height = bottom_font.getbbox("A")[3] + 4
    text_y = 484

    for line in bottom_lines:
        line = line.strip()
        # 하단 줄을 분리하여 20자 이상일 경우 나눔
        split_lines = split_top_line(line, max_length=12)

        for i, sub_line in enumerate(split_lines):
            sub_line = sub_line.strip()
            text_width = bottom_font.getbbox(sub_line)[2]

            text_x = 84

            draw.text((text_x, text_y), sub_line, font=bottom_font, fill="#FFFFFF")
            text_y += line_height  # 다음 줄로 이동

    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = (image_width - store_name_width) // 2
    store_name_y = 1563
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="white")

    fill_color = (255, 255, 255, int(255 * 0.8))  # RGBA

    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_x = (image_width - road_name_width) // 2
    road_name_y = 1639
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill=fill_color)


    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    print(image.width, image.height)
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"

# 이벤트 4:7 버전2
def combine_ads_event_4_7_ver2(store_name, road_name, content, image_width, image_height, image):

    # print(image_width, image_height)
    root_path = os.getenv("ROOT_PATH", ".")
    # print(image)
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1792)

    # 아치형 배경 합성
    arch_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_4_7_circle.png")
    arch_image = Image.open(arch_path).convert("RGBA")

    # sp_image의 가로 길이를 기존 이미지의 가로 길이에 맞추고, 세로는 비율에 맞게 조정
    arch_width = 1024  # 고정된 가로 크기
    aspect_ratio = arch_image.height / arch_image.width  # 원본 이미지의 가로 세로 비율
    arch_height = int(arch_width * aspect_ratio)  # 비율에 맞는 세로 크기 계산
    arch_image = arch_image.resize((arch_width, arch_height), Image.Resampling.LANCZOS)

    snow_x = 0
    snow_y = 0

    # sp_image를 기존 이미지 위에 합성 
    image.paste(arch_image, (snow_x, snow_y), arch_image)

    # 바탕 생성 및 합성
    rectangle_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_4_7_blue.png")
    rectangle = Image.open(rectangle_path).convert("RGBA")
    
    # Rectangle 이미지 크기 확인
    rectangle_width, rectangle_height = rectangle.size

    # Rectangle의 가로 크기 맞추기
    if rectangle_width < 1024:
        left_padding = (1024 - rectangle_width) // 2
        new_rectangle = Image.new("RGBA", (1024, rectangle_height), (0, 0, 0, 0))
        new_rectangle.paste(rectangle, (left_padding, 0))  # 중앙 배치
        rectangle = new_rectangle
        rectangle_width, rectangle_height = rectangle.size  # 크기 갱신

    # 투명 배경 생성: 이미지2 하단에 추가 (전체 높이 1792 맞춤)
    transparent_height = image_height - rectangle_height
    transparent_background = Image.new("RGBA", (rectangle_width, transparent_height), (0, 0, 0, 0))  # 투명 배경 생성

    # Rectangle과 투명 배경 합성
    combined_rectangle = Image.new("RGBA", (rectangle_width, image_height), (0, 0, 0, 0))  # 전체 크기: 1024x1792
    combined_rectangle.paste(rectangle, (0, 0))  # Rectangle 상단 배치
    combined_rectangle.paste(transparent_background, (0, rectangle_height))  # 투명 배경 하단 배치

    # print(image.size, combined_rectangle.size) 

    # 이미지1(image)와 Rectangle 합성
    image = Image.alpha_composite(image, combined_rectangle)


    # 별 아이콘 추가
    star_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_4_7_star.png")
    star_image = Image.open(star_path).convert("RGBA")

    # sp_image의 가로 길이를 기존 이미지의 가로 길이에 맞추고, 세로는 비율에 맞게 조정
    star_width = 201  # 고정된 가로 크기
    star_ratio = star_image.height / star_image.width  # 원본 이미지의 가로 세로 비율
    star_height = int(star_width * star_ratio)  # 비율에 맞는 세로 크기 계산
    star_image = star_image.resize((star_width, star_height), Image.Resampling.LANCZOS)

    star_x = 611
    star_y = 300

    # sp_image를 기존 이미지 위에 합성 
    image.paste(star_image, (star_x, star_y), star_image)

    # 별 아이콘 추가
    star_image = Image.open(star_path).convert("RGBA")

    # sp_image의 가로 길이를 기존 이미지의 가로 길이에 맞추고, 세로는 비율에 맞게 조정
    star_width = 124  # 고정된 가로 크기
    star_ratio = star_image.height / star_image.width  # 원본 이미지의 가로 세로 비율
    star_height = int(star_width * star_ratio)  # 비율에 맞는 세로 크기 계산
    star_image = star_image.resize((star_width, star_height), Image.Resampling.LANCZOS)

    star_x = 76
    star_y = 154

    # sp_image를 기존 이미지 위에 합성 
    image.paste(star_image, (star_x, star_y), star_image)

    # 별 아이콘 추가
    star_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_4_7_star.png")
    star_image = Image.open(star_path).convert("RGBA")

    # sp_image의 가로 길이를 기존 이미지의 가로 길이에 맞추고, 세로는 비율에 맞게 조정
    star_width = 176  # 고정된 가로 크기
    star_ratio = star_image.height / star_image.width  # 원본 이미지의 가로 세로 비율
    star_height = int(star_width * star_ratio)  # 비율에 맞는 세로 크기 계산
    star_image = star_image.resize((star_width, star_height), Image.Resampling.LANCZOS)

    star_x = 37
    star_y = 570

    # sp_image를 기존 이미지 위에 합성 
    image.paste(star_image, (star_x, star_y), star_image)

    # 별 아이콘 추가
    star_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_4_7_star.png")
    star_image = Image.open(star_path).convert("RGBA")

    # sp_image의 가로 길이를 기존 이미지의 가로 길이에 맞추고, 세로는 비율에 맞게 조정
    star_width = 127  # 고정된 가로 크기
    star_ratio = star_image.height / star_image.width  # 원본 이미지의 가로 세로 비율
    star_height = int(star_width * star_ratio)  # 비율에 맞는 세로 크기 계산
    star_image = star_image.resize((star_width, star_height), Image.Resampling.LANCZOS)

    star_x = 831
    star_y = 128

    # sp_image를 기존 이미지 위에 합성 
    image.paste(star_image, (star_x, star_y), star_image)

    
    # 그룹 별 아이콘 추가
    group_star_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_4_7_group_star.png")
    group_star_image = Image.open(group_star_path).convert("RGBA")

    # sp_image의 가로 길이를 기존 이미지의 가로 길이에 맞추고, 세로는 비율에 맞게 조정
    group_star_width = 222 # 고정된 가로 크기
    group_star_ratio = group_star_image.height / group_star_image.width  # 원본 이미지의 가로 세로 비율
    group_star_height = int(group_star_width * group_star_ratio)  # 비율에 맞는 세로 크기 계산
    group_star_image = group_star_image.resize((group_star_width, group_star_height), Image.Resampling.LANCZOS)

    group_star_x = 429
    group_star_y = 35

    # sp_image를 기존 이미지 위에 합성 
    image.paste(group_star_image, (group_star_x, group_star_y), group_star_image)

    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "BlackAndWhitePicture-Regular.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    top_font_size = 96
    bottom_font_size = 60
    store_name_font_size = 48
    road_name_font_size = 40

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 텍스트를 '<br>'로 구분하여 줄 나누기
    # lines = content.split(' ')
    # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    lines = re.findall(r':\s*(.*)', content)  # ':' 이후의 텍스트만 추출
    lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    # print(lines)

    if len(lines) > 0:
        top_line = lines[0].strip()
        lines_list = split_top_line(top_line, max_length=13)  # 반환값은 리스트

        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 178

        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 중앙 정렬 X 좌표 계산
                top_text_width = top_font.getbbox(line)[2]
                top_text_x = (image_width - 80 - 80 - top_text_width) // 2 + 80
                # 텍스트 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill=(255, 255, 255, 10))
                # print(line)
                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    # 하단 텍스트 추가
    bottom_lines = lines[1:]  # 첫 번째 줄을 제외한 나머지
    line_height = bottom_font.getbbox("A")[3] + 4
    text_y = 394

    for line in bottom_lines:
        line = line.strip()
        # 하단 줄을 분리하여 20자 이상일 경우 나눔
        split_lines = split_top_line(line, max_length=18)

        for i, sub_line in enumerate(split_lines):
            sub_line = sub_line.strip()
            text_width = bottom_font.getbbox(sub_line)[2]

            text_x = (image_width - 97 - 97 - text_width) // 2 + 97

            draw.text((text_x, text_y), sub_line, font=bottom_font, fill="white")
            text_y += line_height  # 다음 줄로 이동

    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = (image_width - store_name_width) // 2
    store_name_y = 1563
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="white")

    fill_color = (255, 255, 255, int(255 * 0.8))  # RGBA

    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_x = (image_width - road_name_width) // 2
    road_name_y = 1639
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill=fill_color)


    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"

# 이벤트 4:7 버전3
def combine_ads_event_4_7_ver3(store_name, road_name, content, image_width, image_height, image):
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=876, want_height=876)

    # 포스터 처리 처리
    poster_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_4_7_wedding.png") 
    # sp_image 불러오기 및 리사이즈
    poster_image = Image.open(poster_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 1024
    new_height = 1792
    poster_image = poster_image.resize((new_width, new_height))

    # 전달받은 이미지를 포스터 위에 배치
    offset_x = 74  # 포스터의 왼쪽에서 42px
    offset_y = 606 # 포스터의 위쪽에서 55px
    poster_image.paste(image, (offset_x, offset_y), image)
    image = poster_image


    # QR 처리
    qr_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_4_7_ver_3_site.png") 
    # 효과 불러오기 및 리사이즈
    qr_image = Image.open(qr_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 48
    new_height = 48
    qr_image = qr_image.resize((new_width, new_height))

    offset_x = 237
    offset_y = 526

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(qr_image, (offset_x, offset_y), qr_image)

    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 

    top_font_size = 40
    bottom_font_size = 36
    store_name_font_size = 128
    road_name_font_size = 30
    top_store_name_font_size = 30

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))
    top_store_name_font = ImageFont.truetype(road_name_path, int(top_store_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 텍스트를 '<br>'로 구분하여 줄 나누기
    # lines = content.split(' ')
    # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    lines = re.findall(r':\s*(.*)', content)  # ':' 이후의 텍스트만 추출
    lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    # print(lines)

    if len(lines) > 0:
        top_line = lines[0].strip()
        lines_list = split_top_line(top_line, max_length=18)  # 반환값은 리스트

        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 258

        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 중앙 정렬 X 좌표 계산
                top_text_width = top_font.getbbox(line)[2]
                top_text_x = (1024 - top_text_width) // 2
                # 텍스트 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill="#7F624C")
                # print(line)
                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    # 하단 텍스트 추가
    bottom_lines = lines[1:]  # 첫 번째 줄을 제외한 나머지
    line_height = bottom_font.getbbox("A")[3] + 4
    text_y = 1535

    for line in bottom_lines:
        line = line.strip()
        # 하단 줄을 분리하여 20자 이상일 경우 나눔
        split_lines = split_top_line(line, max_length=18)

        for i, sub_line in enumerate(split_lines):
            sub_line = sub_line.strip()
            text_width = bottom_font.getbbox(sub_line)[2]
            text_x = (image_width - 129 - 129 - text_width) // 2 + 200

            draw.text((text_x, text_y), sub_line, font=bottom_font, fill="#7F624C")
            text_y += line_height  # 다음 줄로 이동


    
    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = (1024 - store_name_width) // 2
    store_name_y = 320
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="#7F624C")


 


    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_x = (1024 - road_name_width) // 2
    road_name_y = 530
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill="#7F624C")

   

    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"

# 이벤트 4:7 버전4
def combine_ads_event_4_7_ver4(store_name, road_name, content, image_width, image_height, image):
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1792)

    
    # 배경 처리
    qr_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_4_7_ver_4_bottom_black.png") 
    # 효과 불러오기 및 리사이즈
    qr_image = Image.open(qr_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 1024
    new_height = 822
    qr_image = qr_image.resize((new_width, new_height))

    offset_x = 0
    offset_y = 970

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(qr_image, (offset_x, offset_y), qr_image)


    # 배경 처리
    back_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_4_7_ver_4_top_black.png") 
    # 효과 불러오기 및 리사이즈
    back_image = Image.open(back_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 1024
    new_height = 415
    back_image = back_image.resize((new_width, new_height))

    offset_x = 0
    offset_y = 0

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(back_image, (offset_x, offset_y), back_image)
    

    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    base_copy_right_path = os.path.join(root_path, "app", "static", "font", "DoHyeon-Regular.otf")

    top_font_size = 64
    bottom_font_size = 40
    store_name_font_size = 55
    road_name_font_size = 32
    base_copy_right_font_size = 32

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))
    base_copy_right_font = ImageFont.truetype(base_copy_right_path, int(base_copy_right_font_size))
    

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 기본 문구 붙여 넣기
    base_copyright = "이벤트"
    base_copyright_width = base_copy_right_font.getbbox(base_copyright)[2]
    base_copyright_height = base_copy_right_font.getbbox(base_copyright)[3]
    base_copyright_x = 120
    base_copyright_y = 1159
    padding_x = 16
    padding_y = 8

    background_x0 = base_copyright_x - padding_x
    background_y0 = base_copyright_y - padding_y
    background_x1 = base_copyright_x + base_copyright_width + padding_x
    background_y1 = base_copyright_y + base_copyright_height + padding_y

    draw.rectangle(
        [background_x0, background_y0, background_x1, background_y1],
        fill="#09C5FE"  # 배경색
    )

    draw.text(
        (base_copyright_x, base_copyright_y),
        base_copyright,
        font=base_copy_right_font,
        fill=(255, 255, 255)  # 텍스트 색상
    )

    lines = re.findall(r':\s*(.*)', content)  # ':' 이후의 텍스트만 추출
    lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    if len(lines) > 0:
        top_line = lines[0].strip()
        lines_list = split_top_line(top_line, max_length=15)  # 반환값은 리스트

        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 1224

        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비 계산
                top_text_width = top_font.getbbox(line)[2]
                top_text_height = top_font.getbbox(line)[3]  # 텍스트 높이 계산
                # 중앙 정렬 X 좌표 계산
                top_text_x = 104
                # 텍스트 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill=(255, 255, 255))

                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    # 하단 텍스트 추가
    bottom_lines = lines[1:]  # 첫 번째 줄을 제외한 나머지

    for line in bottom_lines:
        line = line.strip()
        # 하단 줄을 분리하여 13자 기준으로 나눔
        split_lines = split_top_line(line, max_length=20)

        top_text_x = 104  # 고정
        top_text_y = 1438  # Y 좌표 유지
        max_text_width = 1024 - 148 - top_text_x  # 최대 너비 (876 - 104)

        for i, sub_line in enumerate(split_lines):
            sub_line = sub_line.strip()
            words = sub_line.split()  # 단어 단위 분할
            current_line = ""

            for word in words:
                test_line = current_line + " " + word if current_line else word
                text_width = bottom_font.getbbox(test_line)[2]

                if text_width <= max_text_width:
                    current_line = test_line  # 현재 줄에 추가
                else:
                    # 현재 줄 출력 후 새로운 줄 시작
                    draw.text((top_text_x, top_text_y), current_line, font=bottom_font, fill=(255, 255, 255))
                    top_text_y += bottom_font.getbbox("A")[3] + 5  # 다음 줄로 이동
                    current_line = word  # 새로운 줄 시작

            # 마지막 줄 출력
            if current_line:
                draw.text((top_text_x, top_text_y), current_line, font=bottom_font, fill=(255, 255, 255))
                top_text_y += bottom_font.getbbox("A")[3] + 5  # 다음 줄로 이동

    
    # store_name 추가
    road_name_parts = road_name.split()  # 띄어쓰기 기준으로 나누기
    district = road_name_parts[1] if len(road_name_parts) > 1 else ""  # 두 번째 요소(구) 추출

    final_store_name = f"{store_name} | {district}"  # 최종 store_name 형식

    store_name_width = store_name_font.getbbox(final_store_name)[2]
    store_name_height = store_name_font.getbbox(final_store_name)[3]
    store_name_x = (image_width - store_name_width) // 2
    store_name_y = 116

    draw.text((store_name_x, store_name_y), final_store_name, font=store_name_font, fill=(255, 255, 255))


    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_height = road_name_font.getbbox(road_name)[3]
    road_name_x = (image_width - road_name_width) // 2
    road_name_y = 1714
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill=(255, 255, 255))

    # 선의 너비 및 위치 설정
    line_with = 721
    line_y = 100  # 선의 Y 좌표
    line_x_start = 153  # 선의 시작점 (왼쪽 끝)
    line_x_end = line_x_start + line_with  # 선의 끝점 (road_name 시작 위치에서 40px 왼쪽)
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=1) 

    # 선의 너비 및 위치 설정
    line_with = 721
    line_y = 188  # 선의 Y 좌표
    line_x_start = 153  # 선의 시작점 (왼쪽 끝)
    line_x_end = line_x_start + line_with  # 선의 끝점 (road_name 시작 위치에서 40px 왼쪽)
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=1) 

    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    return f"data:image/png;base64,{base64_image}"

# 이벤트 4:7 버전5
def combine_ads_event_4_7_ver5(store_name, road_name, content, image_width, image_height, image):
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1792)

    
    # 배경 처리
    qr_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_4_7_ver_5_bottom_black.png") 
    # 효과 불러오기 및 리사이즈
    qr_image = Image.open(qr_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 1024
    new_height = 473
    qr_image = qr_image.resize((new_width, new_height))

    offset_x = 0
    offset_y = 1319

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(qr_image, (offset_x, offset_y), qr_image)


    # 배경 처리
    back_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_4_7_ver_5_top_black.png") 
    # 효과 불러오기 및 리사이즈
    back_image = Image.open(back_image_path).convert("RGBA")
 
    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 1024
    new_height = 722
    back_image = back_image.resize((new_width, new_height))

    offset_x = 0
    offset_y = 0

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(back_image, (offset_x, offset_y), back_image)
    

    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "JejuHallasan.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    base_copy_right_path = os.path.join(root_path, "app", "static", "font", "DoHyeon-Regular.otf")

    top_font_size = 63
    bottom_font_size = 35
    store_name_font_size = 67
    road_name_font_size = 36
    

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))
    
    
    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    
    lines = re.findall(r':\s*(.*)', content)  # ':' 이후의 텍스트만 추출
    lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    if len(lines) > 0:
        top_line = lines[0].strip()
        lines_list = split_top_line(top_line, max_length=10)  # 반환값은 리스트

        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 324

        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 중앙 정렬 X 좌표 계산
                top_text_width = top_font.getbbox(line)[2]
                top_text_x = (1024 - top_text_width) // 2
                # 텍스트 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill="#ACACAC")
                # print(line)
                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    # 하단 텍스트 추가
    bottom_lines = lines[1:]  # 첫 번째 줄을 제외한 나머지
    line_height = bottom_font.getbbox("A")[3] + 4
    text_y = 541

    for line in bottom_lines:
        line = line.strip()
        # 하단 줄을 분리하여 20자 이상일 경우 나눔
        split_lines = split_top_line(line, max_length=18)

        for i, sub_line in enumerate(split_lines):
            sub_line = sub_line.strip()
            text_width = bottom_font.getbbox(sub_line)[2]

            text_x = (image_width - 188 - 188 - text_width) // 2 + 188

            draw.text((text_x, text_y), sub_line, font=bottom_font, fill="white")
            text_y += line_height  # 다음 줄로 이동

    
    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_height = store_name_font.getbbox(store_name)[3]
    store_name_x = (image_width - store_name_width) // 2
    store_name_y = 227
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill=(255, 255, 255))


    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_height = road_name_font.getbbox(road_name)[3]
    road_name_x = (image_width - road_name_width) // 2
    road_name_y = 1676
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill=(255, 255, 255))

    # 선의 너비 및 위치 설정
    line_with = 512
    line_y = 314  # 선의 Y 좌표
    line_x_start = 267  # 선의 시작점 (왼쪽 끝)
    line_x_end = line_x_start + line_with  # 선의 끝점 (road_name 시작 위치에서 40px 왼쪽)
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=1) 

    # 선의 너비 및 위치 설정
    line_with = 512
    line_y = 504  # 선의 Y 좌표
    line_x_start = 267  # 선의 시작점 (왼쪽 끝)
    line_x_end = line_x_start + line_with  # 선의 끝점 (road_name 시작 위치에서 40px 왼쪽)
    draw.line((line_x_start, line_y, line_x_end, line_y), fill="#FFFFFF", width=1) 

    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    return f"data:image/png;base64,{base64_image}"














# 상품 소개 4:7 버전1
def combine_ads_pro_intro_4_7(store_name, road_name, content, image_width, image_height, image):
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1792)

    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    # 메뉴명
    base_copy_right_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf")

    top_font_size = 64
    bottom_font_size = 48
    store_name_font_size = 55
    road_name_font_size = 36
    base_copy_right_font_size = 64

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))
    base_copy_right_font = ImageFont.truetype(base_copy_right_path, int(base_copy_right_font_size))
    
    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # ':' 이후의 텍스트만 추출
    print(content)
    lines = re.findall(r':\s*(.*)', content)  # ':' 이후의 텍스트만 추출
    lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외
    print(lines)
    # 기본 문구 붙여 넣기
    base_copyright = lines[0] 
    base_copyright_width = base_copy_right_font.getbbox(base_copyright)[2]
    base_copyright_height = base_copy_right_font.getbbox(base_copyright)[3]
    base_copyright_x = 61
    base_copyright_y = 1159
    padding = 10 

    background_x0 = base_copyright_x - padding
    background_y0 = base_copyright_y - padding
    background_x1 = base_copyright_x + base_copyright_width + padding
    background_y1 = base_copyright_y + base_copyright_height + padding

    draw.rectangle(
        [background_x0, background_y0, background_x1, background_y1],
        fill="#09C5FE"  # 배경색
    )

    draw.text(
        (base_copyright_x, base_copyright_y),
        base_copyright,
        font=base_copy_right_font,
        fill=(255, 255, 255)  # 텍스트 색상
    )

    # print(lines)
    if len(lines) > 0:
        top_line = lines[1].strip()

        lines_list = split_top_line(top_line, max_length=15)  # 반환값은 리스트

        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 1251

        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 중앙 정렬 X 좌표 계산
                top_text_width = top_font.getbbox(line)[2]
                top_text_x = 45
                # 텍스트 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill=(255, 255, 255, 10))
                # print(line)
                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    # 하단 텍스트 추가
    bottom_lines = lines[2:]  # 첫 번째 줄을 제외한 나머지

    line_height = bottom_font.getbbox("A")[3] + 4
    text_y = 1438

    for line in bottom_lines:
        line = line.strip()
        # 하단 줄을 분리하여 20자 이상일 경우 나눔
        split_lines = split_top_line(line, max_length=25)

        for i, sub_line in enumerate(split_lines):
            sub_line = sub_line.strip()
            text_width = bottom_font.getbbox(sub_line)[2]

            text_x = 45

            draw.text((text_x, text_y), sub_line, font=bottom_font, fill="#FFFFFF")
            text_y += line_height  # 다음 줄로 이동
    
    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_height = store_name_font.getbbox(store_name)[3]
    store_name_x = (image_width - store_name_width) // 2
    store_name_y = 134
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill=(255, 255, 255))

    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_height = road_name_font.getbbox(road_name)[3]
    road_name_x = (image_width - road_name_width) // 2
    road_name_y = 1714
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill=(255, 255, 255))


    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"