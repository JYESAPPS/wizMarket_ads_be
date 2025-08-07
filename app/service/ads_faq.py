from app.crud.ads_faq import (
    get_faq as crud_get_faq,
    get_tag as crud_get_tag,
    create_faq as crud_create_faq,
    update_faq as crud_update_faq,
    delete_faq as crud_delete_faq
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
        return {"success": True, "message": "FAQ가 등록되었습니다."}
    except Exception as e:
        
        return {"success": False, "message": "서버 오류가 발생했습니다."}
    
def update_faq(request):
    try:
        crud_update_faq(request.faq_id, request.question, request.answer, request.name)
        return {"success": True, "message": "FAQ가 업데이트되었습니다."}
    except Exception as e:
        
        return {"success": False, "message": "서버 오류가 발생했습니다."}
    


def delete_faq(request):
    try:
        crud_delete_faq(request.faq_id)
        return {"success": True, "message": "FAQ가 업데이트되었습니다."}
    except Exception as e:
        
        return {"success": False, "message": "서버 오류가 발생했습니다."}


