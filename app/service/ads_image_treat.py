from PIL import Image, ExifTags
import requests
import tempfile
from io import BytesIO
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()



def treat_image_turn(img):
    try:
        exif = img._getexif()
        if exif:
            for tag, value in exif.items():
                if ExifTags.TAGS.get(tag) == "Orientation":
                    if value == 3:
                        img = img.rotate(180, expand=True)  # 180도 회전
                    elif value == 6:
                        img = img.rotate(270, expand=True)  # 90도 시계 방향
                    elif value == 8:
                        img = img.rotate(90, expand=True)   # 270도 반시계 방향
                    break  # Orientation 값 찾으면 루프 종료
    except Exception as e:
        print(f"EXIF 데이터 처리 중 오류 발생: {e}")
    return img


def generate_test_edit_image(image, find, change):
    try:
        API_KEY = os.getenv("STABILITY_CHANGE_API_KEY")
        # 업로드된 파일을 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(image.file.read())
            temp_file_path = temp_file.name

        # Stability API 호출
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/edit/search-and-replace",
            headers={
                "authorization": f"Bearer {API_KEY}",
                "accept": "image/*"
            },
            files={
                "image": open(temp_file_path, "rb")
            },
            data={
                "prompt": change,          # 바꾸고자 하는 내용
                "search_prompt": find,     # 찾을 대상
                "output_format": "webp"
            },
        )

        if response.status_code == 200:
            return BytesIO(response.content)  # 이걸 반환
        else:
            raise Exception(response.json())

    except Exception as e:
        raise e
    

def generate_test_change_person(image, style):
    try:
        # API 키 환경 변수로 가져오기
        API_KEY = os.getenv("AILABTOOLS_CHANGE_API_KEY")

        # 파일을 BytesIO로 읽어서 외부 API에 전달
        image_contents = image.file.read()  # 이미지 파일 내용
        response = requests.post(
            "https://www.ailabapi.com/api/portrait/effects/portrait-animation",
            headers={'ailabapi-api-key': API_KEY}, 
            files={'image': ('file', BytesIO(image_contents), 'application/octet-stream')},
            data={'type': style}
        )
        
        if response.status_code == 200:
            # 응답에서 이미지 URL 추출
            response_data = response.json()

            return response_data["data"]["image_url"]
        else:
            return None
    except Exception as e:
        print(f"Error during API call: {str(e)}")
        return None
    

