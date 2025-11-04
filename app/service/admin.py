from app.crud.admin_user import (
    get_admin_list as crud_get_admin_list,
    create_admin_user as crud_create_admin_user,
    delete_admin as crud_delete_admin,
    get_admin_detail as crud_get_admin_detail
)

def get_admin_list():
    rows = crud_get_admin_list()  # list[tuple]
    admins = []
    for r in rows:
        admins.append({
            "id": r["id"],
            "username": r["username"],
            "email": r["email"],
            "role": r["role"],
            "is_active": r["is_active"],
            "must_change_password": r["must_change_password"],
            "created_at": r["created_at"],
            "last_login_at": r.get("last_login_at"),
        })
    return admins

def create_admin_user(data):
    print(data)
    return crud_create_admin_user(data)

def delete_admin(admin_id: int):
    return crud_delete_admin(admin_id)

def get_admin_detail(admin_id):
    return crud_get_admin_detail(admin_id)
