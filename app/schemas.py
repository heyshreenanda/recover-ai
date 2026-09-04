from pydantic import BaseModel

class Payment(BaseModel):
    customer_name: str
    amount: float
    payment_method: str
    status: str
    failure_reason: str| None = None
    

class PaymentResponse(BaseModel):
    id: int
    customer_name: str
    amount: float
    payment_method: str
    status: str
    failure_reason: str | None = None
    revenue_at_risk: float
    risk_score: float
    recovery_action: str | None = None
    recovery_message: str | None = None
    class Config:
        from_attributes = True