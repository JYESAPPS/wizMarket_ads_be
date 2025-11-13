from app.crud.concierge import (
    is_concierge as crud_is_concierge
)


def is_concierge(request):
    is_concierge = crud_is_concierge(request)
    return is_concierge