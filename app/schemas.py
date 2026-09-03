from pydantic import BaseModel

class Payment(BaseModel):
    customer_name: str
    amount: float
    payment_method: str
    status: str
    failure_reason: str| None = None