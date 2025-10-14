import pymysql
import logging
from fastapi import HTTPException
from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from datetime import datetime, timezone, timedelta

# 시도 값 리턴
def get_city_id(city_name: str) -> int:
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        select_query = """
            SELECT city_id
            FROM city
            WHERE city_name LIKE %s
        """
        cursor.execute(select_query, (f"%{city_name}%",))  # ← %를 파라미터에 포함
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return 0
    except Exception as e:
        rollback(connection)
        print(f"get_city_id:{e}")
    finally:
        close_cursor(cursor)
        close_connection(connection)


# 시군구 id 리턴
def get_gu_id(gu_name: str) -> int:
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        select_query = "SELECT district_id FROM district WHERE district_name = %s;"
        cursor.execute(select_query, (gu_name,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return 0
    except Exception as e:
        rollback(connection)
        print(f"get_gu_id:{e}")
    finally:
        close_cursor(cursor)
        close_connection(connection)

# 읍면동 id 리턴
def get_dong_id(dong_name: str) -> int:
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        select_query = "SELECT sub_district_id FROM sub_district WHERE sub_district_name = %s;"
        cursor.execute(select_query, (dong_name,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return 0
    except Exception as e:
        rollback(connection)
        print(f"get_dong_id:{e}")
    finally:
        close_cursor(cursor)
        close_connection(connection)


# 카테고리 명 가져오기
def get_category_name(small_category_code):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT 
                MAIN_CATEGORY_NAME,
                SUB_CATEGORY_NAME,
                DETAIL_CATEGORY_NAME
            FROM BUSINESS_AREA_CATEGORY
            WHERE DETAIL_CATEGORY_CODE = %s;
        """

        cursor.execute(select_query, (small_category_code))
        row = cursor.fetchone()

        if row:
            return (
                row["MAIN_CATEGORY_NAME"],
                row["SUB_CATEGORY_NAME"],
                row["DETAIL_CATEGORY_NAME"]
            )
        else:
            return (None, None, None)


    finally:
        if cursor:
            cursor.close()
        connection.close()


# MAX 값 뽑기
def get_max_number():
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT MAX(CAST(SUBSTRING(store_business_number, 3) AS UNSIGNED)) AS max_js_number
            FROM local_store
            WHERE store_business_number LIKE 'JS%';
        """

        cursor.execute(select_query)
        row = cursor.fetchone()

        if row:
            return (
                row["max_js_number"],
            )
        else:
            return (None, None, None)


    finally:
        if cursor:
            cursor.close()
        connection.close()

# 새 매장 추가
def add_new_store(
    store_business_number, city_id, district_id, sub_district_id, reference_id, 
    large_category_code, medium_category_code, small_category_code,
    large_category_name, medium_category_name, small_category_name,
    store_name, road_name, longitude, latitude 
):
    connection = get_db_connection()
    cursor = connection.cursor()

    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST)
    local_year = now.year
    local_quarter = (now.month - 1) // 3 + 1

    try:
        insert_query = """
            INSERT INTO local_store (
                store_business_number,
                city_id,
                district_id,
                sub_district_id,
                reference_id,
                large_category_code,
                medium_category_code,
                small_category_code,
                large_category_name,
                medium_category_name,
                small_category_name,
                store_name,
                road_name_address,
                longitude,
                latitude,
                local_year,
                local_quarter,
                is_exist
            )
            VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1);
        """

        cursor.execute(insert_query, (
            store_business_number,
            city_id,
            district_id,
            sub_district_id,
            reference_id,
            large_category_code,
            medium_category_code,
            small_category_code,
            large_category_name,
            medium_category_name,
            small_category_name,
            store_name,
            road_name,
            longitude,
            local_year,
            local_quarter,
            latitude
        ))

        connection.commit()
        return True

    except Exception as e:
        print("❌ 매장 저장 중 오류 발생:", e)
        connection.rollback()
        return False

    finally:
        if cursor:
            cursor.close()
        connection.close()




# 매장 정보 가져오기
def get_store_data(store_business_number):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT 
                SUB_DISTRICT_ID,
                STORE_NAME, ROAD_NAME_ADDRESS,
                SMALL_CATEGORY_NAME, SMALL_CATEGORY_CODE, 
                LONGITUDE, LATITUDE
            FROM LOCAL_STORE
            WHERE STORE_BUSINESS_NUMBER = %s;
        """

        cursor.execute(select_query, (store_business_number))
        row = cursor.fetchone()

        if row:
            return (
                row["SUB_DISTRICT_ID"],
                row["STORE_NAME"],
                row["ROAD_NAME_ADDRESS"],
                row["SMALL_CATEGORY_NAME"],
                row["SMALL_CATEGORY_CODE"],
                row["LONGITUDE"],
                row["LATITUDE"]
            )
        else:
            return (None, None, None, None, None, None)
    finally:
        if cursor:
            cursor.close()
        connection.close()


# 지역명 가져오기
def get_city_data(sub_district_id):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT 
                c.CITY_NAME,
                d.DISTRICT_NAME, d.DISTRICT_ID,
                sd.SUB_DISTRICT_NAME
            FROM SUB_DISTRICT sd
            JOIN DISTRICT d ON sd.DISTRICT_ID = d.DISTRICT_ID
            JOIN CITY c ON d.CITY_ID = c.CITY_ID
            WHERE sd.SUB_DISTRICT_ID = %s;
        """

        cursor.execute(select_query, (sub_district_id))
        row = cursor.fetchone()

        if row:
            return (
                row["CITY_NAME"],
                row["DISTRICT_NAME"],
                row["DISTRICT_ID"],
                row["SUB_DISTRICT_NAME"],
            )
        else:
            return (None, None, None, None, None)
    finally:
        if cursor:
            cursor.close()
        connection.close()


# 입지 정보 데이터 가져오기
def get_loc_info_data(sub_district_id):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT 
                SHOP, MOVE_POP, SALES, WORK_POP, INCOME, SPEND, HOUSE, RESIDENT, Y_M
            FROM loc_info
            WHERE SUB_DISTRICT_ID = %s
            ORDER BY Y_M DESC
            LIMIT 1;

        """

        cursor.execute(select_query, (sub_district_id))
        row = cursor.fetchone()

        if row:
            return (
                row["SHOP"],
                row["MOVE_POP"],
                row["SALES"],
                row["WORK_POP"],
                row["INCOME"],
                row["SPEND"],
                row["HOUSE"],
                row["RESIDENT"],
                row["Y_M"]
            )
        else:
            return (None, None, None, None, None, None, None, None)
    finally:
        if cursor:
            cursor.close()
        connection.close()


# 입지 정보 통계값 가져오기
def get_loc_info_j_score(sub_district_id, loc_info_ref_date, target_item):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT 
                J_SCORE_NON_OUTLIERS
            FROM loc_info_statistics
            WHERE sub_district_id = %s and ref_date = %s and target_item = %s
            AND CITY_ID is NOT NULL and DISTRICT_ID is NOT NULL;
        """

        cursor.execute(select_query, (sub_district_id, loc_info_ref_date, target_item))
        row = cursor.fetchone()

        if row:
            return (
                row["J_SCORE_NON_OUTLIERS"],
            )
        else:
            return (None)
    finally:
        if cursor:
            cursor.close()
        connection.close()


# 입지 정보 통계값 가져오기
def get_district_move_pop(district_id, loc_info_ref_date):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT 
                AVG_VAL
            FROM loc_info_statistics
            WHERE sub_district_id = %s and ref_date = %s 
            and target_item = 'move_pop' and STAT_LEVEL = "시/군/구" ;
        """

        cursor.execute(select_query, (district_id, loc_info_ref_date))
        row = cursor.fetchone()

        if row:
            return (
                row["AVG_VAL"],
            )
        else:
            return (None)
    finally:
        if cursor:
            cursor.close()
        connection.close()



# 카테고리 ID 가져오기
def get_category_data(small_category_code):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT 
                BUSINESS_AREA_CATEGORY_ID
            FROM business_area_category
            WHERE detail_category_code = %s;
        """

        cursor.execute(select_query, (small_category_code))
        row = cursor.fetchone()

        if row:
            return (
                row["BUSINESS_AREA_CATEGORY_ID"],
            )
        else:
            return (None)
    finally:
        if cursor:
            cursor.close()
        connection.close()


def get_biz_id(detail_category_id):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT 
                REP_ID
            FROM detail_category_mapping
            WHERE business_area_category_id = %s;
        """

        cursor.execute(select_query, (detail_category_id))
        row = cursor.fetchone()

        if row:
            return (
                row["REP_ID"]
            )
        else:
            return (None)
    finally:
        if cursor:
            cursor.close()
        connection.close()


def get_biz_category_name(rep_id):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT 
                mc.BIZ_MAIN_CATEGORY_ID, 
                sc.BIZ_SUB_CATEGORY_ID, 
                dc.BIZ_DETAIL_CATEGORY_NAME
            FROM biz_detail_category dc
            JOIN biz_sub_category sc ON dc.BIZ_SUB_CATEGORY_ID = sc.BIZ_SUB_CATEGORY_ID
            JOIN biz_main_category mc ON sc.BIZ_MAIN_CATEGORY_ID = mc.BIZ_MAIN_CATEGORY_ID
            WHERE dc.BIZ_DETAIL_CATEGORY_ID = %s;

        """

        cursor.execute(select_query, (rep_id))
        row = cursor.fetchone()

        if row:
            return (
                row["BIZ_MAIN_CATEGORY_ID"],
                row["BIZ_SUB_CATEGORY_ID"],
                row["BIZ_DETAIL_CATEGORY_NAME"]
            )
        else:
            return (None)
    finally:
        if cursor:
            cursor.close()
        connection.close()


def get_ref_date():
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            select MAX(Y_M) as REF_DATE from commercial_district;
        """

        cursor.execute(select_query, ())
        row = cursor.fetchone()

        if row:
            return (
                row["REF_DATE"]
            )
        else:
            return (None, None, None, None, None)
    finally:
        if cursor:
            cursor.close()
        connection.close()

def get_top5(sub_district_id, rep_id):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT 
                TOP_MENU_1, TOP_MENU_2, TOP_MENU_3, TOP_MENU_4, TOP_MENU_5
            FROM commercial_district 
            WHERE SUB_DISTRICT_ID = %s AND BIZ_DETAIL_CATEGORY_ID = %s
        """

        cursor.execute(select_query, (sub_district_id, rep_id))
        row = cursor.fetchone()

        if row:
            return (
                row["TOP_MENU_1"],
                row["TOP_MENU_2"],
                row["TOP_MENU_3"],
                row["TOP_MENU_4"],
                row["TOP_MENU_5"],
            )
        else:
            return (None, None, None, None, None)
    finally:
        if cursor:
            cursor.close()
        connection.close()



def get_pop_info(sub_district_id, gender_id):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT 
                AGE_UNDER_10s, AGE_10s, AGE_20s, AGE_30s, AGE_40s, AGE_50s, AGE_PLUS_60s, REF_DATE
            FROM population_age 
            WHERE SUB_DISTRICT_ID = %s and GENDER_ID = %s
            ORDER BY REF_DATE DESC
            LIMIT 1;
        """

        cursor.execute(select_query, (sub_district_id, gender_id))
        row = cursor.fetchone()

        if row:
            return (
                row["AGE_UNDER_10s"],
                row["AGE_10s"],
                row["AGE_20s"],
                row["AGE_30s"],
                row["AGE_40s"],
                row["AGE_50s"],
                row["AGE_PLUS_60s"],
                row["REF_DATE"]
            )
        else:
            return (None, None, None, None, None, None, None)
    finally:
        if cursor:
            cursor.close()
        connection.close()



def get_mz_j_score(sub_district_id, loc_info_ref_date):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT 
                J_SCORE_NON_OUTLIERS
            FROM population_info_mz_statistics 
            WHERE SUB_DISTRICT_ID = %s and REF_DATE = %s
            AND CITY_ID is NOT NULL and DISTRICT_ID is NOT NULL
        """

        cursor.execute(select_query, (sub_district_id, loc_info_ref_date))
        row = cursor.fetchone()

        if row:
            return (
                row["J_SCORE_NON_OUTLIERS"]
            )
        else:
            return (None)
    finally:
        if cursor:
            cursor.close()
        connection.close()



def get_commercial_j_score(rep_id, table_name):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = f"""
            SELECT 
                J_SCORE_AVG
            FROM {table_name}
            WHERE BIZ_DETAIL_CATEGORY_ID = %s
            ORDER BY REF_DATE DESC
            LIMIT 1;
        """

        cursor.execute(select_query, (rep_id))
        row = cursor.fetchone()

        if row:
            return (
                row["J_SCORE_AVG"]
            )
        else:
            return (None)
    finally:
        if cursor:
            cursor.close()
        connection.close()


def get_commercial_count_data(sub_district_id, nice_biz_map_data_ref_date, id):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = f"""
            SELECT
                COUNT(BIZ_MAIN_CATEGORY_ID) as category_count
            FROM
                COMMERCIAL_DISTRICT
            WHERE SUB_DISTRICT_ID = %s
            AND Y_M = %s and BIZ_MAIN_CATEGORY_ID = %s;
        """

        cursor.execute(select_query, (sub_district_id, nice_biz_map_data_ref_date, id))
        row = cursor.fetchone()

        if row:
            return (
                row["category_count"]
            )
        else:
            return (None)
    finally:
        if cursor:
            cursor.close()
        connection.close()


def get_commercial_data(sub_district_id, rep_id, nice_biz_map_data_ref_date):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = f"""
            SELECT
                SUB_DISTRICT_DENSITY, MARKET_SIZE, AVERAGE_SALES, AVERAGE_PAYMENT, USAGE_COUNT,
                AVG_PROFIT_PER_MON,
                AVG_PROFIT_PER_TUE,
                AVG_PROFIT_PER_WED,
                AVG_PROFIT_PER_THU,
                AVG_PROFIT_PER_FRI,
                AVG_PROFIT_PER_SAT,
                AVG_PROFIT_PER_SUN,
                AVG_PROFIT_PER_06_09,
                AVG_PROFIT_PER_09_12,
                AVG_PROFIT_PER_12_15,
                AVG_PROFIT_PER_15_18,
                AVG_PROFIT_PER_18_21,
                AVG_PROFIT_PER_21_24,
                AVG_PROFIT_PER_24_06,
                AVG_CLIENT_PER_M_20,
                AVG_CLIENT_PER_M_30,
                AVG_CLIENT_PER_M_40,
                AVG_CLIENT_PER_M_50,
                AVG_CLIENT_PER_M_60,
                AVG_CLIENT_PER_F_20,
                AVG_CLIENT_PER_F_30,
                AVG_CLIENT_PER_F_40,
                AVG_CLIENT_PER_F_50,
                AVG_CLIENT_PER_F_60
            FROM
                COMMERCIAL_DISTRICT
            WHERE SUB_DISTRICT_ID = %s
            and BIZ_DETAIL_CATEGORY_ID = %s AND Y_M = %s;
        """

        cursor.execute(select_query, (sub_district_id, rep_id, nice_biz_map_data_ref_date))
        row = cursor.fetchone()

        if row:
            return (
                row["SUB_DISTRICT_DENSITY"],
                row["MARKET_SIZE"],
                row["AVERAGE_SALES"],
                row["AVERAGE_PAYMENT"],
                row["USAGE_COUNT"],
                row["AVG_PROFIT_PER_MON"],
                row["AVG_PROFIT_PER_TUE"],
                row["AVG_PROFIT_PER_WED"],
                row["AVG_PROFIT_PER_THU"],
                row["AVG_PROFIT_PER_FRI"],
                row["AVG_PROFIT_PER_SAT"],
                row["AVG_PROFIT_PER_SUN"],
                row["AVG_PROFIT_PER_06_09"],
                row["AVG_PROFIT_PER_09_12"],
                row["AVG_PROFIT_PER_12_15"],
                row["AVG_PROFIT_PER_15_18"],
                row["AVG_PROFIT_PER_18_21"],
                row["AVG_PROFIT_PER_21_24"],
                row["AVG_PROFIT_PER_24_06"],
                row["AVG_CLIENT_PER_M_20"],
                row["AVG_CLIENT_PER_M_30"],
                row["AVG_CLIENT_PER_M_40"],
                row["AVG_CLIENT_PER_M_50"],
                row["AVG_CLIENT_PER_M_60"],
                row["AVG_CLIENT_PER_F_20"],
                row["AVG_CLIENT_PER_F_30"],
                row["AVG_CLIENT_PER_F_40"],
                row["AVG_CLIENT_PER_F_50"],
                row["AVG_CLIENT_PER_F_60"]
            )
        else:
            return (None, None, None, None, None
                    , None, None, None, None, None
                    , None, None, None, None, None
                    , None, None, None, None, None, None, None
                    , None, None, None, None, None, None, None)
    finally:
        if cursor:
            cursor.close()
        connection.close()



def get_nation_commercial_data(sub_district_id, rep_id, nice_biz_map_data_ref_date, table_name):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = f"""
            SELECT
                AVG_VAL, J_SCORE
            FROM
                {table_name}
            WHERE SUB_DISTRICT_ID = %s
            and BIZ_DETAIL_CATEGORY_ID = %s AND REF_DATE = %s;
        """

        cursor.execute(select_query, (sub_district_id, rep_id, nice_biz_map_data_ref_date))
        row = cursor.fetchone()

        if row:
            return (
                row["AVG_VAL"],
                row["J_SCORE"]
            )
        else:
            return (None, None)
    finally:
        if cursor:
            cursor.close()
        connection.close()



def get_top5_sub_district(district_id, nice_biz_map_data_ref_date, rep_id):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = f"""
            select 
                SUB_DISTRICT_ID, AVERAGE_SALES
            from 
                commercial_district 
            where district_id = %s and Y_M = %s and biz_detail_category_id = %s
            ORDER BY AVERAGE_SALES DESC
            LIMIT 5;

        """

        cursor.execute(select_query, (district_id, nice_biz_map_data_ref_date, rep_id))
        rows = cursor.fetchall()

        if rows:
            return rows  # 리스트로 반환 (각 row는 딕셔너리)
        else:
            return []
    finally:
        if cursor:
            cursor.close()
        connection.close()


def get_sub_district_name(top1_id, top2_id, top3_id, top4_id, top5_id):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sub_district_ids = [top1_id, top2_id, top3_id, top4_id, top5_id]
        # None 제거 (IN 조건에서 사용 불가)
        valid_ids = [i for i in sub_district_ids if i is not None]

        if not valid_ids:
            return [None] * 5

        # %s 를 ID 개수만큼 동적으로 생성
        placeholders = ','.join(['%s'] * len(valid_ids))

        select_query = f"""
            SELECT SUB_DISTRICT_ID, SUB_DISTRICT_NAME
            FROM SUB_DISTRICT
            WHERE SUB_DISTRICT_ID IN ({placeholders});
        """

        cursor.execute(select_query, valid_ids)
        rows = cursor.fetchall()

        # 결과를 ID 기준으로 매핑
        id_to_name = {row["SUB_DISTRICT_ID"]: row["SUB_DISTRICT_NAME"] for row in rows}

        # 원래 순서대로 이름 정리 (None은 그대로 유지)
        names = [id_to_name.get(sid, None) for sid in sub_district_ids]

        return names  # 리스트 형태로 반환
    finally:
        if cursor:
            cursor.close()
        connection.close()





def get_rising_nation():
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT
                DISTRICT_ID, SUB_DISTRICT_ID, BIZ_DETAIL_CATEGORY_ID, GROWTH_RATE
            FROM
                rising_business
            WHERE Y_M = '2024-11-30'
            ORDER BY GROWTH_RATE DESC
            LIMIT 5
        """

        cursor.execute(select_query)
        rows = cursor.fetchall()

        if not rows:
            return []

        # ✅ 정리된 데이터 구조로 반환
        return [
            {
                "DISTRICT_ID": row["DISTRICT_ID"],
                "SUB_DISTRICT_ID": row["SUB_DISTRICT_ID"],
                "CATEGORY_ID": row["BIZ_DETAIL_CATEGORY_ID"],
                "GROWTH": round(row["GROWTH_RATE"], 2)
            }
            for row in rows
        ]
    finally:
        if cursor:
            cursor.close()
        connection.close()



def get_district_name(id):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = f"""
            SELECT
                DISTRICT_NAME
            FROM
                DISTRICT
            WHERE DISTRICT_ID = %s
        """

        cursor.execute(select_query, (id))
        row = cursor.fetchone()

        if row:
            return (
                row["DISTRICT_NAME"]
            )
        else:
            return (None)
    finally:
        if cursor:
            cursor.close()
        connection.close()


def get_sub_district_name_nation(id):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = f"""
            SELECT
                SUB_DISTRICT_NAME
            FROM
                SUB_DISTRICT
            WHERE SUB_DISTRICT_ID = %s
        """

        cursor.execute(select_query, (id))
        row = cursor.fetchone()

        if row:
            return (
                row["SUB_DISTRICT_NAME"]
            )
        else:
            return (None)
    finally:
        if cursor:
            cursor.close()
        connection.close()




def get_rising(id):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT
                DISTRICT_ID, SUB_DISTRICT_ID, BIZ_DETAIL_CATEGORY_ID, GROWTH_RATE
            FROM
                rising_business
            WHERE SUB_DISTRICT_ID = %s
            ORDER BY Y_M DESC
            LIMIT 3
        """

        cursor.execute(select_query, (id))
        rows = cursor.fetchall()

        if not rows:
            return []

        # ✅ 정리된 데이터 구조로 반환
        return [
            {
                "DISTRICT_ID": row["DISTRICT_ID"],
                "SUB_DISTRICT_ID": row["SUB_DISTRICT_ID"],
                "CATEGORY_ID": row["BIZ_DETAIL_CATEGORY_ID"],
                "GROWTH": round(row["GROWTH_RATE"], 2)
            }
            for row in rows
        ]
    finally:
        if cursor:
            cursor.close()
        connection.close()


def get_nice_category_name(id):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = f"""
            SELECT
                BIZ_DETAIL_CATEGORY_NAME
            FROM
                BIZ_DETAIL_CATEGORY
            WHERE BIZ_DETAIL_CATEGORY_ID = %s
        """

        cursor.execute(select_query, (id))
        row = cursor.fetchone()

        if row:
            return (
                row["BIZ_DETAIL_CATEGORY_NAME"]
            )
        else:
            return (None)
    finally:
        if cursor:
            cursor.close()
        connection.close()



def get_hot_place(district_id, loc_info_ref_date):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT
                SUB_DISTRICT_ID, J_SCORE_NON_OUTLIERS
            FROM
                loc_info_statistics
            WHERE DISTRICT_ID = %s
            AND ref_date = %s
            AND J_SCORE_NON_OUTLIERS < 10
            AND STAT_LEVEL = '전국'
            AND TARGET_ITEM = 'j_score_avg'
            ORDER BY J_SCORE_NON_OUTLIERS DESC
            LIMIT 5
        """

        cursor.execute(select_query, (district_id, loc_info_ref_date))
        rows = cursor.fetchall()

        if not rows:
            return []

        # ✅ 정리된 데이터 구조로 반환
        return [
            {
                "SUB_DISTRICT_ID": row["SUB_DISTRICT_ID"],
                "J_SCORE_NON_OUTLIERS": row["J_SCORE_NON_OUTLIERS"],
            }
            for row in rows
        ]
    finally:
        if cursor:
            cursor.close()
        connection.close()


def get_hot_place_loc_info(sub_district_id, loc_info_ref_date):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        select_query = """
            SELECT 
                MOVE_POP, SALES
            FROM LOC_INFO 
            WHERE SUB_DISTRICT_ID = %s and Y_M = %s

        """

        cursor.execute(select_query, (sub_district_id, loc_info_ref_date))
        row = cursor.fetchone()

        if row:
            return (
                row["MOVE_POP"],
                row["SALES"]
            )
        else:
            return (None)
    finally:
        if cursor:
            cursor.close()
        connection.close()


def insert_into_report(
    store_business_number, city_name, district_name, sub_district_name,
    small_category_name, store_name, road_name, latitude, longitude, business_area_category_id, biz_detail_category_name, biz_main_category_id, biz_sub_category_id,
    top_1, top_2, top_3, top_4, top_5,
    loc_info_j_score_average,
    population_total, population_m_per, population_f_per, population_10_under, population_10, population_20, population_30, population_40, population_50, population_60,
    loc_info_resident_k, loc_info_work_pop_k, loc_info_move_pop_k, loc_info_shop_k, loc_info_sales_k, loc_info_spend_k, loc_info_house_k, loc_info_income_won, 
    loc_info_resident_j_score, loc_info_work_pop_j_score, loc_info_move_pop_j_score, loc_info_shop_j_score, loc_info_income_j_score,
    loc_info_mz_j_score, loc_info_spend_j_score, loc_info_sales_j_score, loc_info_house_j_score,
    resident, work_pop, loc_info_resident_per, loc_info_work_pop_per,
    move_pop, loc_info_district_move_pop,
    commercial_district_j_score_average,

    commercial_district_food_count, commercial_district_health_count, commercial_district_edu_count, 
    commercial_district_enter_count, commercial_district_life_count, commercial_district_retail_count,
    n_market_size, market_size, n_density, density, n_average_sales, average_sales, n_average_payment, average_payment, n_usage_count, usage_count,
    market_size_j_score, average_sales_j_score, usage_j_score, density_j_score, average_payment_j_score,
    avg_profit_per_mon, avg_profit_per_tue, avg_profit_per_wed, avg_profit_per_thu, avg_profit_per_fri, avg_profit_per_sat, avg_profit_per_sun, 
    avg_profit_per_06_09, avg_profit_per_09_12, avg_profit_per_12_15, avg_profit_per_15_18, avg_profit_per_18_21, avg_profit_per_21_24, 
    avg_client_per_m_20, avg_client_per_m_30, avg_client_per_m_40, avg_client_per_m_50, avg_client_per_m_60, 
    avg_client_per_f_20, avg_client_per_f_30, avg_client_per_f_40, avg_client_per_f_50, avg_client_per_f_60, 
    top1, top2, top3, top4, top5,
    nation_top1, nation_top2, nation_top3, nation_top4, nation_top5,
    local_top1, local_top2, local_top3,
    hot_place_top1_info, hot_place_top2_info, hot_place_top3_info, hot_place_top4_info, hot_place_top5_info,
    loc_info_ref_date, nice_biz_map_data_ref_date, population_date
):
    connection = get_re_db_connection()
    cursor = connection.cursor()

    try:
        insert_query = """
            INSERT INTO REPORT (
                STORE_BUSINESS_NUMBER,
                CITY_NAME,
                DISTRICT_NAME,
                SUB_DISTRICT_NAME,

                DETAIL_CATEGORY_NAME,
                STORE_NAME,
                ROAD_NAME,
                LATITUDE,
                LONGITUDE,
                BUSINESS_AREA_CATEGORY_ID,
                BIZ_DETAIL_CATEGORY_REP_NAME,
                BIZ_MAIN_CATEGORY_ID,
                BIZ_SUB_CATEGORY_ID,

                DETAIL_CATEGORY_TOP1_ORDERED_MENU,
                DETAIL_CATEGORY_TOP2_ORDERED_MENU,
                DETAIL_CATEGORY_TOP3_ORDERED_MENU,
                DETAIL_CATEGORY_TOP4_ORDERED_MENU,
                DETAIL_CATEGORY_TOP5_ORDERED_MENU,

                LOC_INFO_J_SCORE_AVERAGE,

                POPULATION_TOTAL, 
                POPULATION_MALE_PERCENT,
                POPULATION_FEMALE_PERCENT,
                POPULATION_AGE_10_UNDER,
                POPULATION_AGE_10S,
                POPULATION_AGE_20S,
                POPULATION_AGE_30S,
                POPULATION_AGE_40S,
                POPULATION_AGE_50S,
                POPULATION_AGE_60_OVER,

                LOC_INFO_RESIDENT_K,
                LOC_INFO_WORK_POP_K,
                LOC_INFO_MOVE_POP_K,
                LOC_INFO_SHOP_K,
                LOC_INFO_AVERAGE_SALES_K,
                LOC_INFO_AVERAGE_SPEND_K,
                LOC_INFO_HOUSE_K,
                LOC_INFO_INCOME_WON,

                LOC_INFO_RESIDENT_J_SCORE,
                LOC_INFO_WORK_POP_J_SCORE,
                LOC_INFO_MOVE_POP_J_SCORE,
                LOC_INFO_SHOP_J_SCORE,
                LOC_INFO_INCOME_J_SCORE,
                LOC_INFO_MZ_POPULATION_J_SCORE,
                LOC_INFO_AVERAGE_SPEND_J_SCORE,
                LOC_INFO_AVERAGE_SALES_J_SCORE,
                LOC_INFO_HOUSE_J_SCORE,

                LOC_INFO_RESIDENT, 
                LOC_INFO_WORK_POP,
                LOC_INFO_RESIDENT_PERCENT,
                LOC_INFO_WORK_POP_PERCENT,

                LOC_INFO_MOVE_POP,
                LOC_INFO_CITY_MOVE_POP,

                COMMERCIAL_DISTRICT_J_SCORE_AVERAGE,

                COMMERCIAL_DISTRICT_FOOD_BUSINESS_COUNT,
                COMMERCIAL_DISTRICT_HEALTHCARE_BUSINESS_COUNT,
                COMMERCIAL_DISTRICT_EDUCATION_BUSINESS_COUNT,
                COMMERCIAL_DISTRICT_ENTERTAINMENT_BUSINESS_COUNT,
                COMMERCIAL_DISTRICT_LIFESTYLE_BUSINESS_COUNT,
                COMMERCIAL_DISTRICT_RETAIL_BUSINESS_COUNT,

                COMMERCIAL_DISTRICT_NATIONAL_MARKET_SIZE,
                COMMERCIAL_DISTRICT_SUB_DISTRICT_MARKET_SIZE,
                COMMERCIAL_DISTRICT_NATIONAL_DENSITY_AVERAGE,
                COMMERCIAL_DISTRICT_SUB_DISTRICT_DENSITY_AVERAGE,
                COMMERCIAL_DISTRICT_NATIONAL_AVERAGE_SALES,
                COMMERCIAL_DISTRICT_SUB_DISTRICT_AVERAGE_SALES,
                COMMERCIAL_DISTRICT_NATIONAL_AVERAGE_PAYMENT,
                COMMERCIAL_DISTRICT_SUB_DISTRICT_AVERAGE_PAYMENT,
                COMMERCIAL_DISTRICT_NATIONAL_USAGE_COUNT,
                COMMERCIAL_DISTRICT_SUB_DISTRICT_USAGE_COUNT,

                COMMERCIAL_DISTRICT_MARKET_SIZE_J_SCORE,
                COMMERCIAL_DISTRICT_AVERAGE_SALES_J_SCORE,
                COMMERCIAL_DISTRICT_USAGE_COUNT_J_SCORE,
                COMMERCIAL_DISTRICT_SUB_DISTRICT_DENSITY_J_SCORE,
                COMMERCIAL_DISTRICT_AVERAGE_PAYMENT_J_SCORE,

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
                COMMERCIAL_DISTRICT_AVG_CLIENT_PER_F_60_OVER,

                COMMERCIAL_DISTRICT_DETAIL_CATEGORY_AVERAGE_SALES_TOP1_INFO,
                COMMERCIAL_DISTRICT_DETAIL_CATEGORY_AVERAGE_SALES_TOP2_INFO,
                COMMERCIAL_DISTRICT_DETAIL_CATEGORY_AVERAGE_SALES_TOP3_INFO,
                COMMERCIAL_DISTRICT_DETAIL_CATEGORY_AVERAGE_SALES_TOP4_INFO,
                COMMERCIAL_DISTRICT_DETAIL_CATEGORY_AVERAGE_SALES_TOP5_INFO,

                RISING_BUSINESS_NATIONAL_RISING_SALES_TOP1_INFO,
                RISING_BUSINESS_NATIONAL_RISING_SALES_TOP2_INFO,
                RISING_BUSINESS_NATIONAL_RISING_SALES_TOP3_INFO,
                RISING_BUSINESS_NATIONAL_RISING_SALES_TOP4_INFO,
                RISING_BUSINESS_NATIONAL_RISING_SALES_TOP5_INFO,

                RISING_BUSINESS_SUB_DISTRICT_RISING_SALES_TOP1_INFO,
                RISING_BUSINESS_SUB_DISTRICT_RISING_SALES_TOP2_INFO,
                RISING_BUSINESS_SUB_DISTRICT_RISING_SALES_TOP3_INFO,

                LOC_INFO_DISTRICT_HOT_PLACE_TOP1_INFO,
                LOC_INFO_DISTRICT_HOT_PLACE_TOP2_INFO,
                LOC_INFO_DISTRICT_HOT_PLACE_TOP3_INFO,
                LOC_INFO_DISTRICT_HOT_PLACE_TOP4_INFO,
                LOC_INFO_DISTRICT_HOT_PLACE_TOP5_INFO,

                LOC_INFO_DATA_REF_DATE,
                NICE_BIZ_MAP_DATA_REF_DATE,
                POPULATION_DATA_REF_DATE

                
            )
            VALUES (
                %s, %s, %s, %s,                             
                %s, %s, %s, %s, %s, %s, %s, %s, %s,         
                %s, %s, %s, %s, %s,                         
                %s,                                         
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,     
                %s, %s, %s, %s, %s, %s, %s, %s,             
                %s, %s, %s, %s, %s,                      
                %s, %s, %s, %s,     
                %s, %s, %s, %s,     
                %s, %s,             
                %s,         
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s
                  
            );
        """

        cursor.execute(insert_query, (
            store_business_number, city_name, district_name, sub_district_name,
            small_category_name, store_name, road_name, latitude, longitude, business_area_category_id, biz_detail_category_name, biz_main_category_id, biz_sub_category_id,
            top_1, top_2, top_3, top_4, top_5,
            loc_info_j_score_average,
            population_total, population_m_per, population_f_per, population_10_under, population_10, population_20, population_30, population_40, population_50, population_60,
            loc_info_resident_k, loc_info_work_pop_k, loc_info_move_pop_k, loc_info_shop_k, loc_info_sales_k, loc_info_spend_k, loc_info_house_k, loc_info_income_won, 
            loc_info_resident_j_score, loc_info_work_pop_j_score, loc_info_move_pop_j_score, loc_info_shop_j_score, loc_info_income_j_score,
            loc_info_mz_j_score, loc_info_spend_j_score, loc_info_sales_j_score, loc_info_house_j_score,
            resident, work_pop, loc_info_resident_per, loc_info_work_pop_per,
            move_pop, loc_info_district_move_pop,
            commercial_district_j_score_average,

            commercial_district_food_count, commercial_district_health_count, commercial_district_edu_count, 
            commercial_district_enter_count, commercial_district_life_count, commercial_district_retail_count,
            n_market_size, market_size, n_density, density, n_average_sales, average_sales, n_average_payment, average_payment, n_usage_count, usage_count,
            market_size_j_score, average_sales_j_score, usage_j_score, density_j_score, average_payment_j_score,
            avg_profit_per_mon, avg_profit_per_tue, avg_profit_per_wed, avg_profit_per_thu, avg_profit_per_fri, avg_profit_per_sat, avg_profit_per_sun, 
            avg_profit_per_06_09, avg_profit_per_09_12, avg_profit_per_12_15, avg_profit_per_15_18, avg_profit_per_18_21, avg_profit_per_21_24,
            avg_client_per_m_20, avg_client_per_m_30, avg_client_per_m_40, avg_client_per_m_50, avg_client_per_m_60, 
            avg_client_per_f_20, avg_client_per_f_30, avg_client_per_f_40, avg_client_per_f_50, avg_client_per_f_60,
            top1, top2, top3, top4, top5,
            nation_top1, nation_top2, nation_top3, nation_top4, nation_top5,
            local_top1, local_top2, local_top3,
            hot_place_top1_info, hot_place_top2_info, hot_place_top3_info, hot_place_top4_info, hot_place_top5_info,
            loc_info_ref_date, nice_biz_map_data_ref_date, population_date  
        ))

        connection.commit()
        return True

    except Exception as e:
        print("❌ 매장 저장 중 오류 발생:", e)
        connection.rollback()
        return False

    finally:
        if cursor:
            cursor.close()
        connection.close()



