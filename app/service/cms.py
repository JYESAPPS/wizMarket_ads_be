from app.crud.cms import (
    insert_business_verification as crud_insert_business_verification
)



def insert_business_verification(
        user_id,
        original,
        saved_name,
        dest_path,    
        content_type,
        size_bytes,
):
    crud_insert_business_verification(
        user_id,
        original,
        saved_name,
        dest_path,    
        content_type,
        size_bytes
    )