from app.crud.admin_user import (
    get_admin_list as crud_get_admin_list,
)

def get_admin_list():
    rows = crud_get_admin_list()  # list[tuple]
    admins = []
    for r in rows:
        (id, username, email, role, is_active, must_change_password, created_at, last_login_at) = r

        admins.append({
            "id": id,
            "username": username,
            "email": email,
            "role": role,
            "is_active": is_active,
            "must_change_password": must_change_password,
            "created_at": created_at,
            "last_login_at": last_login_at
        })
    return admins