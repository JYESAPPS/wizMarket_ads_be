from PIL import Image, ExifTags
import requests
import tempfile
from io import BytesIO
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

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
    

# 얼굴 비교해보기
def compare_face(image, prompt):
    # 1. prompt 로 이미지 4장 생성해보기
    try:
        key = os.getenv("IMAGEN3_API_SECRET")
        client = genai.Client(api_key=key)

        # Prompt 전달 및 이미지 생성
        response = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=4,
                aspect_ratio="9:16",  # 비율 유지
                output_mime_type='image/jpeg'
            )
        )
        # 생성된 이미지 리스트 내에서 각각 기존 이미지와 코사인 유사도 비교
        # 전달 받은 기존 이미지는 파일 객체임
        # 이미지가 4장이므로 for 문 안에서 진행
        # GPT 적극 활용!! 저도 잘 모르는 영역입니다...ㅠㅠ
        # 필요 시 모듈 설치하고 pip show 모듈명으로 버전 확인 후 requirements.txt 에 작성하기
        for generated_image in response.generated_images:
            image = Image.open(BytesIO(generated_image.image.image_bytes))
            # 생성 된 이미지 띄우기
            image.show()




        # 
        # return image_list_with_compare


    except Exception as e:
        return {"error": f"이미지 생성 중 오류 발생: {e}"}