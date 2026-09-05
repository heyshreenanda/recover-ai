from pydantic import BaseModel
from typing import Optional


# =============================================
# PAYMENT INPUT
# =============================================

class Payment(BaseModel):

    customer_name: str

    amount: float

    payment_method: str

    status: str

    failure_reason: Optional[str] = None


# =============================================
# PAYMENT RESPONSE
# =============================================

class PaymentResponse(BaseModel):

    id: int

    customer_name: str

    amount: float

    payment_method: str

    status: str

    failure_reason: Optional[str]

    revenue_at_risk: float

    risk_score: int

    recovery_action: str

    recovery_status: Optional[str]

    recovered: bool

    recovery_message: Optional[str]

    recovery_latency_ms: Optional[float]

    class Config:

        from_attributes = True


# =============================================
# CUSTOMER HISTORY
# =============================================

class CustomerHistoryResponse(BaseModel):

    customer_name: str

    total_payments: int

    successful_payments: int

    failed_payments: int

    total_revenue_at_risk: float

    recovered_revenue: float

    recovery_rate_percent: float

    payment_history: list[PaymentResponse]