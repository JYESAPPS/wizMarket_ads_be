from PIL import Image, ExifTags


def trat_image_turn(img):
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