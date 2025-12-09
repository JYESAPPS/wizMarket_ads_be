from pydantic import BaseModel
from typing import Optional

class InsertPayRequest(BaseModel):
    user_id: str
    ticket_id: int
    payment_method: str
    payment_date: str  
    qty: int
    type: str
    billing_cycle: str
    plan_type: str
    platform : str
    product_id : str
    purchase_token: Optional[str] = None
    transaction_id: Optional[str] = None

class InsertTokenRequest(BaseModel):
    user_id: int