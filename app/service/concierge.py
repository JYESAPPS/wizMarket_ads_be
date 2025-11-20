import pymysql
from typing import Dict, List, Tuple, Optional, Any
import os
from fastapi import UploadFile
from uuid import uuid4
from fastapi import HTTPException, status
import json, requests
from fastapi.responses import JSONResponse
import shutil

from app.db.connect import (
    get_re_db_connection,
    commit,
    rollback,
    close_cursor,
    close_connection,
)

from app.crud.concierge import (
    is_concierge as crud_is_concierge,
    submit_concierge_user as crud_submit_concierge_user,
    submit_concierge_store as crud_submit_concierge_store,
    submit_concierge_image as crud_submit_concierge_image,
    select_concierge_list as crud_select_concierge_list,
    select_concierge_detail as crud_select_concierge_detail,
    get_report_store as crud_get_report_store,
    update_report_is_concierge as crud_update_report_is_concierge,
    update_concierge_user_status as crud_update_concierge_user_status,
    delete_concierge_user as crud_delete_concierge_user,
)
from app.service.regist_new_store import (
    get_city_id as service_get_city_id,
    get_gu_id as service_get_gu_id,
    get_dong_id as service_get_dong_id,
    add_new_store as service_add_new_store,
    copy_new_store as service_copy_new_store
)


# 축약/변형 → 정식 명칭 매핑
_ALIAS_TO_CANON = {
    # 특별/광역시
    "서울": "서울특별시", "서울시": "서울특별시",
    "부산": "부산광역시", "부산시": "부산광역시",
    "대구": "대구광역시", "대구시": "대구광역시",
    "인천": "인천광역시", "인천시": "인천광역시",
    "광주": "광주광역시", "광주시": "광주광역시",
    "대전": "대전광역시", "대전시": "대전광역시",
    "울산": "울산광역시", "울산시": "울산광역시",
    "세종": "세종특별자치시", "세종시": "세종특별자치시", "세종특별시": "세종특별자치시",

    # 도(광역자치단체)
    "경기": "경기도", "경기도": "경기도",
    "강원": "강원특별자치도", "강원도": "강원특별자치도", "강원특별자치도": "강원특별자치도",
    "충북": "충청북도", "충청북도": "충청북도",
    "충남": "충청남도", "충청남도": "충청남도",
    "전북": "전라북도", "전라북도": "전라북도",
    "전남": "전라남도", "전라남도": "전라남도",
    "경북": "경상북도", "경상북도": "경상북도",
    "경남": "경상남도", "경상남도": "경상남도",
    "제주": "제주특별자치도", "제주도": "제주특별자치도", "제주특별자치도": "제주특별자치도",
}


# 기존 매장인지 조회
def is_concierge(request):
    is_concierge = crud_is_concierge(request)
    return is_concierge



# 이미지 저장 처리
UPLOAD_ROOT = "/app/uploads"  # 도커 컨테이너 내부 실제 저장 위치 (볼륨 마운트 추천)

async def save_concierge_images(user_id: int, images: List[UploadFile]) -> Dict[str, str]:
    """
    user_id 기준으로 concierge/user_{user_id}/... 에 저장하고,
    DB에 넣을 storage_path 맵을 반환.
    예: { "image_1": "concierge/user_1/abcd1234_1.png", ... }
    """
    image_paths: Dict[str, str] = {}

    if not images:
        return image_paths

    # 1) 실제 저장 디렉토리 (컨테이너 내부)
    user_dir = os.path.join(UPLOAD_ROOT, "concierge", f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)  # 폴더 없으면 자동 생성

    for idx, img in enumerate(images[:6], start=1):  # 최대 6장
        if not img.filename:
            continue

        _, ext = os.path.splitext(img.filename)
        ext = (ext or ".jpg").lower()

        filename = f"{uuid4().hex}_{idx}{ext}"

        # 실제 파일이 저장될 전체 경로 (컨테이너 파일 시스템 기준)
        save_path = os.path.join(user_dir, filename)

        # 파일 쓰기
        content = await img.read()
        with open(save_path, "wb") as f:
            f.write(content)

        # 🔹 DB에는 이렇게 저장 (논리 경로)
        #    concierge/user_1/abcd1234_1.png
        storage_path = os.path.join("concierge", f"user_{user_id}", filename).replace("\\", "/")

        image_paths[f"image_{idx}"] = storage_path

    return image_paths


# 커밋 처리 한번에
async def submit_concierge(fields: Dict[str, str], images: List[UploadFile]) -> Tuple[bool, str]:
    """
    - concierge_user / concierge_store / concierge_user_file INSERT
    - 이미지 파일은 user_id 기준 폴더에 저장: uploads/concierge/user_{user_id}/...
    """
    main_category = fields.get("mainCategory")
    sub_category = fields.get("subCategory")
    detail_category = fields.get("detailCategory")

    name = fields.get("name")
    phone = fields.get("phone")
    pin = fields.get("pin")

    store_name = fields.get("storeName")
    road_address = fields.get("roadAddress")
    menus = fields.get("menus")

    connection = get_re_db_connection()
    cursor = None

    try:
        cursor = connection.cursor()

        # 1) 컨시어지 유저 생성
        user_id = crud_submit_concierge_user(cursor, name, phone, pin)

        # 2) 컨시어지 가게 생성
        crud_submit_concierge_store(
            cursor,
            user_id,
            store_name,
            road_address,
            menus,
            main_category,
            sub_category,
            detail_category,
        )

        # 3) 이미지 저장 → image_paths 구성 (user_id 기준 폴더 내부)
        image_paths = await save_concierge_images(user_id, images)

        # 4) 컨시어지 이미지 메타데이터 INSERT
        if image_paths:
            crud_submit_concierge_image(cursor, user_id, image_paths)

        # 5) 모두 성공 시 커밋
        commit(connection)
        return True, "신청이 정상적으로 접수되었습니다."

    except pymysql.MySQLError as e:
        rollback(connection)
        print(f"[submit_concierge] DB error: {e}")
        return False, "신청 처리 중 DB 오류가 발생했습니다."

    except Exception as e:
        rollback(connection)
        print(f"[submit_concierge] error: {e}")
        return False, "신청 처리 중 알 수 없는 오류가 발생했습니다."

    finally:
        close_cursor(cursor)
        close_connection(connection)


# 리스트 조회
def select_concierge_list(
    keyword: Optional[str],
    search_field: Optional[str],
    status: Optional[str],
    apply_start: Optional[str],
    apply_end: Optional[str],
):
    return crud_select_concierge_list(
        keyword=keyword,
        search_field=search_field,
        status=status,
        apply_start=apply_start,
        apply_end=apply_end,
    )


# 상세 보기
def select_concierge_detail(user_id: int) -> Dict[str, Any]:
    """
    컨시어지 상세 조회 서비스
    - 없으면 404 에러
    """
    detail: Optional[Dict[str, Any]] = crud_select_concierge_detail(user_id)

    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 컨시어지 신청을 찾을 수 없습니다.",
        )

    return detail



# 리포트 테이블 내 매장 조회
def get_report_store(store_name, road_name):
    
    store_business_number = crud_get_report_store(store_name, road_name)
    return store_business_number



# 컨시어지 용 매장 등록
def concierge_add_new_store (request):
    # 1. 도로명 -> 지번 변환
    url = "https://business.juso.go.kr/addrlink/addrLinkApi.do"
    jibun_key = os.getenv("JIBUN_KEY")
    # ad = "서울특별시 영등포구 영신로 220"
    ad = request.road_name

    params = {
        'confmKey': jibun_key,
        'currentPage': '1',
        'countPerPage': '1',
        'keyword': ad,
        'resultType': 'json'
    }
    req = requests.get(url, params=params)
    data = json.loads(req.text)          # 또는 data = req.json()  # req 가 requests.Response 인 경우
    land_add = data["results"]["juso"][0]["jibunAddr"]

    # 2. 지번 -> 행정동 변환
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    adms_key = os.getenv("ADMS_KEY")
    headers = {"Authorization": f"KakaoAK {adms_key}"}
    params = {"query": land_add}

    req = requests.get(url, headers=headers, params=params)
    data = json.loads(req.text)          # 또는 data = req.json()  # req 가 requests.Response 인 경우

    raw_si_name = data["documents"][0]["address"]["region_1depth_name"]
    si_name = _ALIAS_TO_CANON.get(raw_si_name, raw_si_name)
    # 원문
    full = data["documents"][0]["address"]["region_2depth_name"]

    # 안전하게: 앞뒤 공백 제거 + 연속 공백/탭/개행 모두 처리
    gu_name = (full or "").strip().split()[0] if full else ""
    dong_name = data["documents"][0]["address"]["region_3depth_h_name"]

    # 추출한 행정동 각각 id 로 변환
    city_id = service_get_city_id(si_name)
    district_id = service_get_gu_id(gu_name)
    sub_district_id = service_get_dong_id(dong_name)
    

    # 3. 위경도 조회
    key = os.getenv("ROAD_NAME_KEY")
    apiurl = "https://api.vworld.kr/req/address"
    params = {
        "service": "address",
        "request": "getcoord",
        "crs": "epsg:4326",
        "address": request.road_name,
        "format": "json",
        "type": "road",
        "key": key
    }

    response = requests.get(apiurl, params=params)
    if response.status_code != 200:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "위경도 조회 실패", "number" : ""}
        )

    data = response.json()
    try:
        longitude = str(data['response']['result']['point']['x'])
        latitude = str(data['response']['result']['point']['y'])
    except (KeyError, TypeError, ValueError):
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "좌표 파싱 실패", "number" : ""}
        )
    # 3. 매장 등록 시도
    success, store_business_number = service_add_new_store(request, city_id, district_id, sub_district_id, longitude, latitude)
    if success:
        # 4. 서비스 DB 로 매장 카피
        service_copy_new_store(store_business_number)

        return {"success": True, "message": "매장 등록 성공." , "store_business_number" : store_business_number}

    else : 
        return {"success": False, "message": "서버 오류가 발생했습니다." , "store_business_number" : ""}


def update_concierge_status(user_id, store_business_number):
    crud_update_report_is_concierge(store_business_number)
    crud_update_concierge_user_status(user_id, store_business_number)


# 엑셀 업로드된 컨시어지 일괄 등록
def submit_concierge_excel(rows) -> Dict[str, Any]:
    """
    엑셀로 업로드된 컨시어지 후보들을 일괄 등록.
    - rows: [ConciergeExcelRow, ...]
    - 한 row 처리할 때마다 commit
    """
    connection = get_re_db_connection()
    cursor = None

    total = len(rows)
    created_count = 0
    failed_rows: List[int] = []

    try:
        cursor = connection.cursor()

        for idx, row in enumerate(rows):
            try:
                # 0) 완전 빈 줄은 스킵 (필요시 조건 조절)
                if not (row.store_name or row.road_name or row.phone or row.name):
                    continue

                # 1) 메뉴 리스트 구성
                menus = [m for m in [row.menu_1, row.menu_2, row.menu_3] if m]

                # 2) 컨시어지 유저 생성
                #    pin, 카테고리는 엑셀에 없으니까 우선 None / "" 로 처리
                user_id = crud_submit_concierge_user(
                    cursor,
                    row.name or "",
                    row.phone or "",
                    None,  # pin
                )

                # 3) 컨시어지 가게 생성
                crud_submit_concierge_store(
                    cursor,
                    user_id,
                    row.store_name or "",
                    row.road_name or "",
                    menus,   # 기존 crud에서 리스트/문자열 중 어떤 걸 기대하는지에 맞춰서 조정
                    None,    # main_category
                    None,    # sub_category
                    None,    # detail_category
                )

                # 4) 이 row까지는 정상 → 커밋
                commit(connection)
                created_count += 1

            except pymysql.MySQLError as e:
                rollback(connection)
                failed_rows.append(idx)
                print(f"[submit_concierge_excel] DB error at row {idx}: {e}")

            except Exception as e:
                rollback(connection)
                failed_rows.append(idx)
                print(f"[submit_concierge_excel] error at row {idx}: {e}")

        return {
            "success": True,
            "total": total,
            "created": created_count,
            "failed": len(failed_rows),
            "failed_rows": failed_rows,
        }

    finally:
        close_cursor(cursor)
        close_connection(connection)




# 컨시어지 매장 삭제 처리
def delete_concierge_user(user_ids: List[int]) -> Dict[str, Any]:
    """
    컨시어지 신청 여러 건 삭제.
    - user_ids 는 CONCIERGE_USER.id
    - ON DELETE CASCADE 로 STORE / FILE 은 자동 삭제
    - DB 삭제 이후, concierge/user_{user_id} 폴더 통째로 삭제
    """
    connection = get_re_db_connection()
    cursor = None

    total = len(user_ids)

    try:
        cursor = connection.cursor()

        # 1) USER 삭제 (CASCADE로 store/file 레코드 자동 삭제)
        deleted_users = crud_delete_concierge_user(cursor, user_ids)

        # 2) DB 커밋
        commit(connection)

    except pymysql.MySQLError as e:
        rollback(connection)
        print(f"[delete_concierge_user] DB error: {e}")
        return {
            "success": False,
            "message": "컨시어지 삭제 중 DB 오류가 발생했습니다.",
        }

    except Exception as e:
        rollback(connection)
        print(f"[delete_concierge_user] error: {e}")
        return {
            "success": False,
            "message": "컨시어지 삭제 중 알 수 없는 오류가 발생했습니다.",
        }

    finally:
        close_cursor(cursor)
        close_connection(connection)

    # 3) 커밋이 끝난 뒤, 실제 폴더 삭제 (DB 트랜잭션과 분리)
    deleted_dirs = 0

    for user_id in user_ids:
        user_dir = os.path.join(UPLOAD_ROOT, "concierge", f"user_{user_id}")
        try:
            if os.path.isdir(user_dir):
                shutil.rmtree(user_dir)  # 폴더 + 내부 파일 전부 삭제
                deleted_dirs += 1
        except Exception as e:
            # 폴더 삭제 실패해도 DB는 이미 커밋된 상태 → 로그만 남김
            print(f"[delete_concierge_user] dir remove error ({user_dir}): {e}")

    return {
        "success": True,
        "total": total,
        "deleted_users": deleted_users,
        "deleted_dirs": deleted_dirs,
    }

