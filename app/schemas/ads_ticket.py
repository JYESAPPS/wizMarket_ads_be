from pydantic import BaseModel

class InsertPayRequest(BaseModel):
    user_id: str
    ticket_id: int
    payment_method: str
    payment_date: str  
    qty: int
    type: str
    billing_cycle: str
    plan_type: str

class InsertTokenRequest(BaseModel):
    user_id: int