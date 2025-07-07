from pydantic import BaseModel
from typing import Optional


class PlanList(BaseModel):
    TICKET_ID: int
    TICKET_NAME: str
    TICKET_PRICE: int
    TICKET_TYPE: str
    BILLING_CYCLE : Optional[int]
    TOKEN_AMOUNT: int

    class Config:
        from_attributes = True


class InsertFeeRequest(BaseModel):
    ticket_type: str
    ticket_name: str
    ticket_price: int
    billing_cycle: Optional[int]
    token_amount : int