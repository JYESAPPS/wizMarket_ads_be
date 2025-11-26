from app.crud.regist_new_store import (
    get_city_id as crud_get_city_by_name,
    get_gu_id as crud_get_gu_by_name,
    get_dong_id as crud_get_dong_by_name,
    get_category_name as crud_get_category_name,
    get_max_number as crud_get_max_number,
    add_new_store as crud_add_new_store,
    get_store_data as crud_get_store_data,
    get_city_data as crud_get_city_data,
    get_loc_info_data as crud_get_loc_info_data,
    get_loc_info_j_score as crud_get_loc_info_j_score,
    get_district_move_pop as crud_get_district_move_pop,
    get_category_data as crud_get_category_data,
    get_biz_id as crud_get_biz_id,
    get_biz_category_name as crud_get_biz_category_name,
    get_ref_date as crud_get_ref_date,
    get_top5 as crud_get_top5,
    get_pop_info as crud_get_pop_info,
    get_mz_j_score as crud_get_mz_j_score,
    get_commercial_j_score as crud_get_commercial_j_score,
    get_commercial_count_data as crud_get_commercial_count_data,
    get_commercial_data as crud_get_commercial_data,
    get_nation_commercial_data as crud_get_nation_commercial_data,
    get_top5_sub_district as crud_get_top5_sub_district,
    get_sub_district_name as crud_get_sub_district_name,
    get_rising_nation as crud_get_rising_nation,
    get_rising as crud_get_rising,
    get_nice_category_name as crud_get_nice_category_name,
    get_district_name as crud_get_district_name,
    get_sub_district_name_nation as crud_get_sub_district_name_nation,
    get_hot_place as crud_get_hot_place,
    get_hot_place_loc_info as crud_get_hot_place_loc_info,
    insert_into_report as crud_insert_into_report,
)


# 시 -> id 변환
def get_city_id(si_name: str) -> int:
    city = crud_get_city_by_name(si_name)
    if city:
        return city
    return 0

# 구 -> id 변환
def get_gu_id(gu_name: str) -> int:
    gu = crud_get_gu_by_name(gu_name)
    if gu:
        return gu
    return 0

# 동 -> id 변환
def get_dong_id(dong_name: str) -> int:
    dong = crud_get_dong_by_name(dong_name)
    if dong:
        return dong
    return 0






# admin DB local_store TB 에 값 넣기
def add_new_store(data, city_id, district_id, sub_district_id, longitude, latitude):

    reference_id = 3
    large_category_code = data.large_category_code
    medium_category_code = data.medium_category_code
    small_category_code = data.small_category_code
    store_name = data.store_name
    road_name = data.road_name


    large_category_name, medium_category_name, small_cateogry_name = crud_get_category_name(small_category_code)

    # MAX 매장 관리 번호 값 뽑기
    prev_number = crud_get_max_number()  # 예: "JS0012"
    # print(prev_number)
    # JS 접두사 제거 + 숫자 변환
    if prev_number:
        number = int(prev_number[0]) + 1
    else:
        number = 1  # 처음 등록이라면 JS0001부터 시작

    # 다음 store_business_number 구성
    store_business_number = f"JS{number:04d}"  # JS0013 형식
    sucess = crud_add_new_store(
        store_business_number, city_id, district_id, sub_district_id, reference_id, 
        large_category_code, medium_category_code, small_category_code,
        large_category_name, medium_category_name, small_cateogry_name,
        store_name, road_name, longitude, latitude
    )
    # print(sucess)
    return sucess, store_business_number


def copy_new_store(store_business_number):
    try : 
        # 매장 데이터 꺼내오기
        sub_district_id, store_name, road_name, small_category_name, small_category_code, longitude, latitude = crud_get_store_data(store_business_number)

        # 지역 명 가져오기
        city_name, district_name, district_id, sub_district_name = crud_get_city_data(sub_district_id)

        # 입지 정보 값 가져오기
        shop, move_pop, sales, work_pop, income, spend, house, resident, loc_info_ref_date = crud_get_loc_info_data(sub_district_id)

        resident = resident or 0
        work_pop = work_pop or 0

        # 0으로 나누기 방지
        total_pop = resident + work_pop
        if total_pop == 0:
            loc_info_resident_per = 0
            loc_info_work_pop_per = 0
        else:
            loc_info_resident_per = resident / total_pop
            loc_info_work_pop_per = work_pop / total_pop

        # 입지 j-score 값 가져오기
        loc_info_j_score_average = crud_get_loc_info_j_score(sub_district_id, loc_info_ref_date, 'j_score_average')

        # 상권 정보 값 가져오기
        ## 카테고리 엮기
        
        ### 상권 정보 분류표 ID 가져오기
        business_area_category_id = crud_get_category_data(small_category_code)

        ### 매핑 값 가져오기
        rep_id = crud_get_biz_id(business_area_category_id)

        ### 매핑한 NAME 값 가져오기
        biz_main_category_id, biz_sub_category_id, biz_detail_category_name = crud_get_biz_category_name(rep_id)

        
        # 상권 정보 날짜값
        nice_biz_map_data_ref_date = crud_get_ref_date()
        
        # 소분류 주문 TOP 메뉴 가져오기
        top_1, top_2, top_3, top_4, top_5 = crud_get_top5(sub_district_id, rep_id)

        # 인구 분포 가져오기
        m_under_10, m_10, m_20, m_30, m_40, m_50, m_60, population_date =  crud_get_pop_info(sub_district_id, 1)
        f_under_10, f_10, f_20, f_30, f_40, f_50, f_60, population_date =  crud_get_pop_info(sub_district_id, 2)

        m_population_total = (m_under_10 + m_10 + m_20 + m_30 + m_40 + m_50 + m_60)
        f_population_total = (f_under_10 + f_10 + f_20 + f_30 + f_40 + f_50 + f_60)

        population_total = m_population_total + f_population_total
        population_m_per = (m_population_total / population_total) * 100
        population_f_per = (f_population_total / population_total) * 100
        population_10_under = m_under_10 + f_under_10
        population_10 = m_10 + f_10
        population_20 = m_20 + f_20
        population_30 = m_30 + f_30
        population_40 = m_40 + f_40
        population_50 = m_50 + f_50
        population_60 = m_60 + f_60

        resident = resident or 0
        work_pop = work_pop or 0
        move_pop = move_pop or 0
        shop = shop or 0
        income = income or 0
        sales = sales or 0
        spend = spend or 0
        house = house or 0

        # 입지 정보 값 가공
        loc_info_resident_k = resident / 1000
        loc_info_work_pop_k = work_pop / 1000
        loc_info_move_pop_k = move_pop / 1000
        loc_info_shop_k = shop / 1000
        loc_info_income_won = income / 10000  # 만 단위
        loc_info_sales_k = sales / 1000
        loc_info_spend_k = spend / 1000
        loc_info_house_k = house / 1000
        loc_info_resident_k = resident / 1000

        loc_info_resident_j_score = crud_get_loc_info_j_score(sub_district_id, loc_info_ref_date, 'resident')
        loc_info_work_pop_j_score = crud_get_loc_info_j_score(sub_district_id, loc_info_ref_date, 'work_pop')
        loc_info_move_pop_j_score = crud_get_loc_info_j_score(sub_district_id, loc_info_ref_date, 'move_pop')
        loc_info_shop_j_score = crud_get_loc_info_j_score(sub_district_id, loc_info_ref_date, 'shop')
        loc_info_income_j_score = crud_get_loc_info_j_score(sub_district_id, loc_info_ref_date, 'income')
        loc_info_spend_j_score = crud_get_loc_info_j_score(sub_district_id, loc_info_ref_date, 'spend')
        loc_info_sales_j_score = crud_get_loc_info_j_score(sub_district_id, loc_info_ref_date, 'sales')
        loc_info_house_j_score = crud_get_loc_info_j_score(sub_district_id, loc_info_ref_date, 'house')

        loc_info_district_move_pop = crud_get_district_move_pop(district_id, loc_info_ref_date)

        # MZ 인구 j_score
        loc_info_mz_j_score = crud_get_mz_j_score(sub_district_id, loc_info_ref_date)

        # 상권 정보 j_score
        commercial_district_j_score_average = crud_get_commercial_j_score(rep_id, 'commercial_district_weighted_average')
        



        # 상권 정보 대분류 별 값
        commercial_district_food_count = crud_get_commercial_count_data(sub_district_id, nice_biz_map_data_ref_date, 1)
        commercial_district_health_count = crud_get_commercial_count_data(sub_district_id, nice_biz_map_data_ref_date, 2)
        commercial_district_edu_count = crud_get_commercial_count_data(sub_district_id, nice_biz_map_data_ref_date, 3)
        commercial_district_enter_count = crud_get_commercial_count_data(sub_district_id, nice_biz_map_data_ref_date, 4)
        commercial_district_life_count = crud_get_commercial_count_data(sub_district_id, nice_biz_map_data_ref_date, 5)
        commercial_district_retail_count = crud_get_commercial_count_data(sub_district_id, nice_biz_map_data_ref_date, 6)

        (
            density, market_size, average_sales, average_payment, usage_count,
            avg_profit_per_mon, avg_profit_per_tue, avg_profit_per_wed, avg_profit_per_thu, avg_profit_per_fri, avg_profit_per_sat, avg_profit_per_sun, 
            avg_profit_per_06_09, avg_profit_per_09_12, avg_profit_per_12_15, avg_profit_per_15_18, avg_profit_per_18_21, avg_profit_per_21_24, avg_profit_per_24_06, 
            avg_client_per_m_20, avg_client_per_m_30, avg_client_per_m_40, avg_client_per_m_50, avg_client_per_m_60, 
            avg_client_per_f_20, avg_client_per_f_30, avg_client_per_f_40, avg_client_per_f_50, avg_client_per_f_60, 
        ) = crud_get_commercial_data(sub_district_id, rep_id, nice_biz_map_data_ref_date)



        n_density, density_j_score = crud_get_nation_commercial_data(sub_district_id, rep_id, nice_biz_map_data_ref_date, 'commercial_district_sub_district_density_statistics')
        n_market_size, market_size_j_score = crud_get_nation_commercial_data(sub_district_id, rep_id, nice_biz_map_data_ref_date, 'commercial_district_market_size_statistics')
        n_average_sales, average_sales_j_score = crud_get_nation_commercial_data(sub_district_id, rep_id, nice_biz_map_data_ref_date, 'commercial_district_average_sales_statistics')
        n_average_payment, average_payment_j_score = crud_get_nation_commercial_data(sub_district_id, rep_id, nice_biz_map_data_ref_date, 'commercial_district_average_payment_statistics')
        n_usage_count, usage_j_score = crud_get_nation_commercial_data(sub_district_id, rep_id, nice_biz_map_data_ref_date, 'commercial_district_useage_count_statistics')

        # 해당 소분류 시군구에서 1등 읍면동
        # 1. 상위 5개 데이터 조회
        top_rows = crud_get_top5_sub_district(district_id, nice_biz_map_data_ref_date, rep_id)

        # 2. ID 리스트
        ids = [row["SUB_DISTRICT_ID"] for row in top_rows]
        ids += [None] * (5 - len(ids))

        # 3. 이름 리스트
        names = crud_get_sub_district_name(*ids)

        # 4. 매출 리스트
        sales = [row["AVERAGE_SALES"] for row in top_rows]
        sales += [None] * (5 - len(sales))

        # 5. "이름,매출" 문자열 조합
        top1 = f"{names[0]},{sales[0]}" if names[0] and sales[0] else None
        top2 = f"{names[1]},{sales[1]}" if names[1] and sales[1] else None
        top3 = f"{names[2]},{sales[2]}" if names[2] and sales[2] else None
        top4 = f"{names[3]},{sales[3]}" if names[3] and sales[3] else None
        top5 = f"{names[4]},{sales[4]}" if names[4] and sales[4] else None

        
        # 뜨는 업종 MAX 날짜 값
        top5_rising = crud_get_rising_nation()

        top1_district_id = top5_rising[0]["DISTRICT_ID"]
        top1_sub_district_id = top5_rising[0]["SUB_DISTRICT_ID"]
        top1_category_id = top5_rising[0]["CATEGORY_ID"]
        top1_growth = top5_rising[0]["GROWTH"]

        top2_district_id = top5_rising[1]["DISTRICT_ID"]
        top2_sub_district_id = top5_rising[1]["SUB_DISTRICT_ID"]
        top2_category_id = top5_rising[1]["CATEGORY_ID"]
        top2_growth = top5_rising[1]["GROWTH"]

        top3_district_id = top5_rising[2]["DISTRICT_ID"]
        top3_sub_district_id = top5_rising[2]["SUB_DISTRICT_ID"]
        top3_category_id = top5_rising[2]["CATEGORY_ID"]
        top3_growth = top5_rising[2]["GROWTH"]

        top4_district_id = top5_rising[3]["DISTRICT_ID"]
        top4_sub_district_id = top5_rising[3]["SUB_DISTRICT_ID"]
        top4_category_id = top5_rising[3]["CATEGORY_ID"]
        top4_growth = top5_rising[3]["GROWTH"]

        top5_district_id = top5_rising[4]["DISTRICT_ID"]
        top5_sub_district_id = top5_rising[4]["SUB_DISTRICT_ID"]
        top5_category_id = top5_rising[4]["CATEGORY_ID"]
        top5_growth = top5_rising[4]["GROWTH"]

        nation_top1_name = crud_get_nice_category_name(top1_category_id)
        nation_top2_name = crud_get_nice_category_name(top2_category_id)
        nation_top3_name = crud_get_nice_category_name(top3_category_id)
        nation_top4_name = crud_get_nice_category_name(top4_category_id)
        nation_top5_name = crud_get_nice_category_name(top5_category_id)

        nation_top1_district_name = crud_get_district_name(top1_district_id)
        nation_top2_district_name = crud_get_district_name(top2_district_id)
        nation_top3_district_name = crud_get_district_name(top3_district_id)
        nation_top4_district_name = crud_get_district_name(top4_district_id)
        nation_top5_district_name = crud_get_district_name(top5_district_id)

        nation_top1_sub_district_name = crud_get_sub_district_name_nation(top1_sub_district_id)
        nation_top2_sub_district_name = crud_get_sub_district_name_nation(top2_sub_district_id)
        nation_top3_sub_district_name = crud_get_sub_district_name_nation(top3_sub_district_id)
        nation_top4_sub_district_name = crud_get_sub_district_name_nation(top4_sub_district_id)
        nation_top5_sub_district_name = crud_get_sub_district_name_nation(top5_sub_district_id)

        nation_top1 = f"{nation_top1_district_name},{nation_top1_sub_district_name},{nation_top1_name},{top1_growth}"
        nation_top2 = f"{nation_top2_district_name},{nation_top2_sub_district_name},{nation_top2_name},{top2_growth}"
        nation_top3 = f"{nation_top3_district_name},{nation_top3_sub_district_name},{nation_top3_name},{top3_growth}"
        nation_top4 = f"{nation_top4_district_name},{nation_top4_sub_district_name},{nation_top4_name},{top4_growth}"
        nation_top5 = f"{nation_top5_district_name},{nation_top5_sub_district_name},{nation_top5_name},{top5_growth}"

        local_rising_top3 = crud_get_rising(sub_district_id)

        local_top1_district_id = local_rising_top3[0]["DISTRICT_ID"]
        local_top1_sub_district_id = local_rising_top3[0]["SUB_DISTRICT_ID"]
        local_top1_category_id = local_rising_top3[0]["CATEGORY_ID"]
        local_top1_growth = local_rising_top3[0]["GROWTH"]

        local_top2_district_id = local_rising_top3[1]["DISTRICT_ID"]
        local_top2_sub_district_id = local_rising_top3[1]["SUB_DISTRICT_ID"]
        local_top2_category_id = local_rising_top3[1]["CATEGORY_ID"]
        local_top2_growth = local_rising_top3[1]["GROWTH"]

        local_top3_district_id = local_rising_top3[2]["DISTRICT_ID"]
        local_top3_sub_district_id = local_rising_top3[2]["SUB_DISTRICT_ID"]
        local_top3_category_id = local_rising_top3[2]["CATEGORY_ID"]
        local_top3_growth = local_rising_top3[2]["GROWTH"]


        local_top1_name = crud_get_nice_category_name(local_top1_category_id)
        local_top2_name = crud_get_nice_category_name(local_top2_category_id)
        local_top3_name = crud_get_nice_category_name(local_top3_category_id)

        local_top1_district_name = crud_get_district_name(local_top1_district_id)
        local_top2_district_name = crud_get_district_name(local_top2_district_id)
        local_top3_district_name = crud_get_district_name(local_top3_district_id)

        local_top1_sub_district_name = crud_get_sub_district_name_nation(local_top1_sub_district_id)
        local_top2_sub_district_name = crud_get_sub_district_name_nation(local_top2_sub_district_id)
        local_top3_sub_district_name = crud_get_sub_district_name_nation(local_top3_sub_district_id)

        local_top1 = f"{local_top1_district_name},{local_top1_sub_district_name},{local_top1_name},{local_top1_growth}"
        local_top2 = f"{local_top2_district_name},{local_top2_sub_district_name},{local_top2_name},{local_top2_growth}"
        local_top3 = f"{local_top3_district_name},{local_top3_sub_district_name},{local_top3_name},{local_top3_growth}"


        hot_place_top5 = crud_get_hot_place(district_id, loc_info_ref_date)

        hot_place_top1_sub_district_id = hot_place_top5[0]["SUB_DISTRICT_ID"]
        hot_place_top1_j_score = hot_place_top5[0]["J_SCORE_NON_OUTLIERS"]

        hot_place_top2_sub_district_id = hot_place_top5[1]["SUB_DISTRICT_ID"]
        hot_place_top2_j_score = hot_place_top5[1]["J_SCORE_NON_OUTLIERS"]

        hot_place_top3_sub_district_id = hot_place_top5[2]["SUB_DISTRICT_ID"]
        hot_place_top3_j_score = hot_place_top5[2]["J_SCORE_NON_OUTLIERS"]

        hot_place_top4_sub_district_id = hot_place_top5[3]["SUB_DISTRICT_ID"]
        hot_place_top4_j_score = hot_place_top5[3]["J_SCORE_NON_OUTLIERS"]

        hot_place_top5_sub_district_id = hot_place_top5[4]["SUB_DISTRICT_ID"]
        hot_place_top5_j_score = hot_place_top5[4]["J_SCORE_NON_OUTLIERS"]

        hot_place_top1_sub_district_name = crud_get_sub_district_name_nation(hot_place_top1_sub_district_id)
        hot_place_top2_sub_district_name = crud_get_sub_district_name_nation(hot_place_top2_sub_district_id)
        hot_place_top3_sub_district_name = crud_get_sub_district_name_nation(hot_place_top3_sub_district_id)
        hot_place_top4_sub_district_name = crud_get_sub_district_name_nation(hot_place_top4_sub_district_id)
        hot_place_top5_sub_district_name = crud_get_sub_district_name_nation(hot_place_top5_sub_district_id)

        hot_place_top1_move_pop, hot_place_top1_sales = crud_get_hot_place_loc_info(hot_place_top1_sub_district_id, loc_info_ref_date)
        hot_place_top2_move_pop, hot_place_top2_sales = crud_get_hot_place_loc_info(hot_place_top2_sub_district_id, loc_info_ref_date)
        hot_place_top3_move_pop, hot_place_top3_sales = crud_get_hot_place_loc_info(hot_place_top3_sub_district_id, loc_info_ref_date)
        hot_place_top4_move_pop, hot_place_top4_sales = crud_get_hot_place_loc_info(hot_place_top4_sub_district_id, loc_info_ref_date)
        hot_place_top5_move_pop, hot_place_top5_sales = crud_get_hot_place_loc_info(hot_place_top5_sub_district_id, loc_info_ref_date)

        hot_place_top1_info = f"{hot_place_top1_sub_district_name},{hot_place_top1_move_pop},{hot_place_top1_sales},{hot_place_top1_j_score}"
        hot_place_top2_info = f"{hot_place_top2_sub_district_name},{hot_place_top2_move_pop},{hot_place_top2_sales},{hot_place_top2_j_score}"
        hot_place_top3_info = f"{hot_place_top3_sub_district_name},{hot_place_top3_move_pop},{hot_place_top3_sales},{hot_place_top3_j_score}"
        hot_place_top4_info = f"{hot_place_top4_sub_district_name},{hot_place_top4_move_pop},{hot_place_top4_sales},{hot_place_top4_j_score}"
        hot_place_top5_info = f"{hot_place_top5_sub_district_name},{hot_place_top5_move_pop},{hot_place_top5_sales},{hot_place_top5_j_score}"


        # 리포트에 넣기
        sucess = crud_insert_into_report(
            store_business_number, city_name, district_name, sub_district_name,
            small_category_name, store_name, road_name, latitude, longitude, business_area_category_id, biz_detail_category_name, biz_main_category_id, biz_sub_category_id,
            top_1, top_2, top_3, top_4, top_5,
            loc_info_j_score_average,
            population_total, population_m_per, population_f_per, population_10_under, population_10, population_20, population_30, population_40, population_50, population_60,
            loc_info_resident_k, loc_info_work_pop_k, loc_info_move_pop_k, loc_info_shop_k, loc_info_income_won, loc_info_sales_k, loc_info_spend_k, loc_info_house_k,
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
        )
    except Exception as e:
        print ("매장 복사 오류 :", str(e))

    
