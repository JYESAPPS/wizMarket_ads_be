
design_map = {
    1: "3D감성",
    2: "포토실사",
    3: "캐릭터/만화",
    4: "레트로",
    5: "AI모델",
    6: "예술",
}

channel_map = {
    1: "카카오톡",
    2: "인스타그램 스토리",
    3: "인스타그램 피드",
    4: "네이버 블로그"
}

title_map = {
    1: "매장 홍보",
    2: "상품 소개",
    3: "이벤트",
    4: "네이버 블로그"
}

def get_name(ai_data):
    design_text = design_map.get(ai_data[0])
    channel_text = channel_map.get(ai_data[2])
    title_text = title_map.get(ai_data[3])

    return design_text, channel_text, title_text

def get_str_number():
    pass