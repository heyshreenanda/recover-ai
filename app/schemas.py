from pydantic import BaseModel


class Payment(BaseModel):

    customer_name: str

    amount: float

    payment_method: str

    status: str

    failure_reason: str | None = None


class PaymentResponse(BaseModel):

    id: int

    customer_name: str

    amount: float

    payment_method: str

    status: str

    failure_reason: str | None

    revenue_at_risk: float

    risk_score: int

    recovery_action: str

    recovery_status: str

    recovered: bool

    recovery_message: str

    class Config:

        from_attributes = True