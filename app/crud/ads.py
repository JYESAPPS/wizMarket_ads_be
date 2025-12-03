from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from dotenv import load_dotenv
import pymysql
from fastapi import HTTPException
import logging
from app.schemas.ads import AdsInitInfo, RandomImage
import random
from typing import List

load_dotenv()
logger = logging.getLogger(__name__)


# 기본 정보 가져오기
def select_ads_init_info(store_business_number: str) -> AdsInitInfo:
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    logger = logging.getLogger(__name__)

    try:
        if connection.open:
            select_query = """
                SELECT 
                    STORE_BUSINESS_NUMBER, 
                    STORE_NAME,
                    ROAD_NAME,
                    CITY_NAME,
                    DISTRICT_NAME,
                    SUB_DISTRICT_NAME,
                    LATITUDE,
                    LONGITUDE,
                    DETAIL_CATEGORY_NAME,
                    LOC_INFO_AVERAGE_SALES_K,
                    COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_MON,
                    COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_TUE,
                    COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_WED,
                    COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_THU,
                    COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_FRI,
                    COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_SAT,
                    COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_SUN, 
                    COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_06_09,
                    COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_09_12,
                    COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_12_15,
                    COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_15_18,
                    COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_18_21,
                    COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_21_24,
                    COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_20S,
                    COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_30S,
                    COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_40S,
                    COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_50S,
                    COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_60_OVER,
                    COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_20S,
                    COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_30S,
                    COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_40S,
                    COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_50S,
                    COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_60_OVER
                FROM
                    report
                WHERE
                    STORE_BUSINESS_NUMBER = %s
                ;
            """
            cursor.execute(select_query, (store_business_number,))
            row = cursor.fetchone()  # 한 행만 가져옴

            if not row:
                raise HTTPException(
                    status_code=404,
                    detail=f"AdsInitInfo {store_business_number}에 해당하는 데이터를 찾을 수 없습니다.",
                )

            # Pydantic 모델로 매핑
            ads_init_info = AdsInitInfo(
                store_business_number=row.get("STORE_BUSINESS_NUMBER"),
                store_name=row.get("STORE_NAME"),
                road_name=row.get("ROAD_NAME"),
                city_name=row.get("CITY_NAME"),
                district_name=row.get("DISTRICT_NAME"),
                sub_district_name=row.get("SUB_DISTRICT_NAME"),
                latitude= row.get("LATITUDE"),
                longitude=row.get("LONGITUDE"),
                detail_category_name=row.get("DETAIL_CATEGORY_NAME"),
                loc_info_average_sales_k=row.get("LOC_INFO_AVERAGE_SALES_K"),
                commercial_district_average_percent_mon = row.get("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_MON"),
                commercial_district_average_percent_tue = row.get("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_TUE"),
                commercial_district_average_percent_wed = row.get("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_WED"),
                commercial_district_average_percent_thu = row.get("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_THU"),
                commercial_district_average_percent_fri = row.get("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_FRi"),
                commercial_district_average_percent_sat = row.get("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_SAT"),
                commercial_district_average_percent_sun = row.get("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_SUN"),
                commercial_district_average_percent_06_09 = row.get("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_06_09"),
                commercial_district_average_percent_09_12 = row.get("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_09_12"),
                commercial_district_average_percent_12_15 = row.get("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_12_15"),
                commercial_district_average_percent_15_18 = row.get("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_15_18"),
                commercial_district_average_percent_18_21 = row.get("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_18_21"),
                commercial_district_average_percent_21_24 = row.get("COMMERCIAL_DISTRICT_AVERAGE_SALES_PERCENT_21_24"),
                commercial_district_avg_client_per_m_20s = row.get("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_20S"),
                commercial_district_avg_client_per_m_30s = row.get("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_30S"),
                commercial_district_avg_client_per_m_40s = row.get("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_40S"),
                commercial_district_avg_client_per_m_50s = row.get("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_50S"),
                commercial_district_avg_client_per_m_60_over = row.get("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_M_60_OVER"),
                commercial_district_avg_client_per_f_20s = row.get("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_20S"),
                commercial_district_avg_client_per_f_30s = row.get("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_30S"),
                commercial_district_avg_client_per_f_40s = row.get("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_40S"),
                commercial_district_avg_client_per_f_50s = row.get("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_50S"),
                commercial_district_avg_client_per_f_60_over = row.get("COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_60_OVER"),
            )
            return ads_init_info
    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
    except Exception as e:
        logger.error(f"Unexpected Error in select_ads_init_info: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류가 발생했습니다.")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



# 유저가 설정한 커스텀 메뉴 값 가져오기
def select_custom_menu(user_id):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT REGISTER_TAG, CUSTOM_MENU
                FROM user_info
                WHERE user_id = %s
            """, (user_id,))
            result = cursor.fetchone()

        if result:
            return result[0], result[1]  # 튜플로 반환
        else:
            return None, None

    except Exception as e:
        print(f"중복 검사 오류: {e}")
        return {"available": False}



# 카테고리 name 값으로 id 값 조회
def get_category_id(name):
    try:
        connection = get_re_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM detail_category WHERE name = %s", (name,))
            id = cursor.fetchone()

        return id
    except Exception as e:
        print(f"중복 검사 오류: {e}")
        return {"available": False}


def random_image_list(
    category_id: int,
    design_id: str,
    min_count: int = 3,
    max_count: int = 5,
):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    logger = logging.getLogger(__name__)

    try:
        design_id_int = int(design_id)  # ✅ str → int 변환

        if not connection.open:
            raise HTTPException(status_code=500, detail="DB 연결에 실패했습니다.")

        select_query = """
            SELECT tp.image_path, t.design_id, t.prompt
            FROM thumbnail t
            JOIN thumbnail_path tp ON t.thumbnail_id = tp.thumbnail_id
            WHERE t.category_id = %s AND t.design_id = %s
        """

        # 1차 시도: 사용자가 보낸 category_id
        cursor.execute(select_query, (category_id, design_id_int))
        rows = cursor.fetchall()

        # 2차 시도: 기본 카테고리(249)
        if not rows:
            logger.warning(f"[랜덤이미지] 카테고리 {category_id}, 디자인 {design_id_int} → 기본 카테고리로 재시도")
            cursor.execute(select_query, (249, design_id_int))
            rows = cursor.fetchall()

        if not rows:
            logger.warning(f"[랜덤이미지] 디자인 {design_id_int}는 모든 카테고리에 이미지 없음")
            raise HTTPException(status_code=404, detail="해당 디자인에 대한 이미지가 존재하지 않습니다.")

        total = len(rows)

        # 실제 있는 개수가 min_count보다 적으면 있는 만큼만 반환
        if total <= min_count:
            target_count = total
        else:
            # min_count ~ max_count 사이에서 랜덤으로 선택
            target_count = random.randint(min_count, min(max_count, total))

        # ✅ 중복 없이 여러 개 추출
        selected_rows = random.sample(rows, target_count)

        return [
            RandomImage(
                path=row["image_path"],
                prompt=row["prompt"],
                design_id=row["design_id"],
            )
            for row in selected_rows
        ]

    finally:
        try:
            cursor.close()
            connection.close()
        except Exception:
            pass


# 글만 먼저 저장 처리
def insert_ads(store_business_number: str, use_option: str, title: str, detail_title: str, content: str):
    # 데이터베이스 연결 설정
    connection = get_re_db_connection()
    
    try:
        with connection.cursor() as cursor:
            # 데이터 인서트 쿼리
            insert_query = """
                INSERT INTO ADS 
                (STORE_BUSINESS_NUMBER, USE_OPTION, TITLE, DETAIL_TITLE, CONTENT) 
                VALUES (%s, %s, %s, %s, %s)
            """
            # 쿼리 실행
            cursor.execute(insert_query, (store_business_number, use_option, title, detail_title, content))
            # 자동 생성된 PK 가져오기
            pk = cursor.lastrowid
            # 커밋하여 DB에 반영
            commit(connection)
            return pk

    except pymysql.MySQLError as e:
        rollback(connection)  # 오류 시 롤백
        print(f"Database error: {e}")
        raise

    finally:
        close_cursor(cursor)   # 커서 종료
        close_connection(connection)  # 연결 종료


# 이미지 저장 처리
def insert_ads_image(ads_pk: int, image_url: str, final_image_url: str):
    # 데이터베이스 연결 설정
    connection = get_re_db_connection()
    cursor = None

    try:
        cursor = connection.cursor()
        # 이미지 저장 쿼리
        insert_query = """
            INSERT INTO ADS_IMAGE (ADS_ID, ADS_IMAGE_URL, ADS_FINAL_IMAGE_URL)
            VALUES (%s, %s, %s)
        """
        # 단일 이미지 URL 저장
        cursor.execute(insert_query, (ads_pk, image_url, final_image_url))
        
        commit(connection)
    except Exception as e:
        print("Error:", e)
        rollback(connection)
    finally:
        if cursor:
            close_cursor(cursor)
        close_connection(connection)


# ADS 삭제 처리
def delete_status(ads_id: int) -> bool:
    connection = get_re_db_connection()

    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 업데이트 쿼리 작성
            delete_query = """
                UPDATE ADS
                SET STATUS = 'D'
                WHERE ADS_ID = %s
            """
            # 쿼리 실행
            cursor.execute(delete_query, (ads_id))
            connection.commit()
            
            # rowcount를 통해 업데이트 성공 여부 확인
            if cursor.rowcount == 0:
                return False  # 업데이트된 행이 없는 경우 False 반환
            return True  # 업데이트 성공 시 True 반환
    except pymysql.Error as e:
        logger.error(f"Database error occurred: {str(e)}")
        raise HTTPException(status_code=503, detail=f"데이터베이스 연결 오류: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error occurred LocStoreDetailContent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"내부 서버 오류: {str(e)}")
    finally:
        connection.close()



# 글만 먼저 수정 처리
def update_ads(store_business_number: str, use_option: str, title: str, detail_title: str, content: str):
    # 데이터베이스 연결 설정
    connection = get_re_db_connection()
    print(content)
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 데이터 인서트 쿼리
            update_query = """
                UPDATE ADS 
                SET USE_OPTION = %s, TITLE = %s, DETAIL_TITLE = %s, CONTENT = %s
                WHERE STORE_BUSINESS_NUMBER = %s 
            """
            # 쿼리 실행
            rows_affected = cursor.execute(update_query, (use_option, title, detail_title, content, store_business_number))
            if rows_affected > 0:
                # 업데이트된 행의 ads_id 조회
                select_query = """
                    SELECT ADS_ID 
                    FROM ADS
                    WHERE STORE_BUSINESS_NUMBER = %s
                """
                cursor.execute(select_query, (store_business_number,))
                result = cursor.fetchone()
                
                if result:
                    ads_id = result['ADS_ID']  # 'ADS_ID'는 테이블 컬럼 이름
                else:
                    raise ValueError("No matching record found after update.")
            else:
                raise ValueError("No rows were updated.")

            # 커밋하여 DB에 반영
            connection.commit()
            return ads_id

    except pymysql.MySQLError as e:
        rollback(connection)  # 오류 시 롤백
        print(f"Database error: {e}")
        raise

    finally:
        close_cursor(cursor)   # 커서 종료
        close_connection(connection)  # 연결 종료


# 이미지 수정 처리
def update_ads_image(ads_id: int, image_url: str, final_image_url: str):
    # 데이터베이스 연결 설정
    connection = get_re_db_connection()
    cursor = None

    try:
        cursor = connection.cursor()
        # 이미지 저장 쿼리
        update_query = """
            UPDATE ADS_IMAGE
            SET ADS_IMAGE_URL = %s, ADS_FINAL_IMAGE_URL = %s 
            WHERE ADS_ID = %s
        """
        # 단일 이미지 URL 저장
        cursor.execute(update_query, (image_url, final_image_url, ads_id))
        
        commit(connection)
    except Exception as e:
        print("Error:", e)
        rollback(connection)
    finally:
        if cursor:
            close_cursor(cursor)
        close_connection(connection)



def update_popup(user_id: int, popup: bool):
    connection = get_re_db_connection()
    cursor = connection.cursor()
    logger = logging.getLogger(__name__)

    try:
        if connection.open:
            popup_int = 1 if popup else 0
            query = """
                UPDATE `user`
                SET popup = %s
                WHERE user_id = %s
            """
            cursor.execute(query, (popup_int, user_id))
            connection.commit()
    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        connection.rollback()
        raise HTTPException(status_code=500, detail="DB 오류 발생")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        connection.rollback()
        raise HTTPException(status_code=500, detail="알 수 없는 오류")
    finally:
        cursor.close()
        connection.close()

