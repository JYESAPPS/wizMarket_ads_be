from pydantic import BaseModel

class InsertPayRequest(BaseModel):
    user_id: str
    ticket_id: int
    payment_method: str
    payment_date: str  
    qty: int
    type: str

class InsertTokenRequest(BaseModel):
    user_id: int