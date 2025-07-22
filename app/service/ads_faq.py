from app.crud.ads_faq import (
    get_faq as crud_get_faq,
    get_tag as crud_get_tag,
    create_faq as crud_create_faq
)


def get_faq():
    notice = crud_get_faq()
    return notice


def get_tag():
    tag = crud_get_tag()
    return tag


def create_faq(request):
    try:
        crud_create_faq(request.question, request.answer, request.name)
        return {"success": True, "message": "공지사항이 등록되었습니다."}
    except Exception as e:
        
        return {"success": False, "message": "서버 오류가 발생했습니다."}