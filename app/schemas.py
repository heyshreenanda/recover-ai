from pydantic import BaseModel
from typing import Optional


# ------------------------------------------------
# PAYMENT INPUT
# ------------------------------------------------

class Payment(BaseModel):

    customer_name: str

    amount: float

    payment_method: str

    status: str

    failure_reason: Optional[str] = None


# ------------------------------------------------
# PAYMENT RESPONSE
# ------------------------------------------------

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

    recovery_latency_ms: Optional[float] = None

    class Config:
        from_attributes = True


# ------------------------------------------------
# CUSTOMER HISTORY
# ------------------------------------------------

class CustomerHistoryResponse(BaseModel):

    customer_name: str

    total_payments: int

    successful_payments: int

    failed_payments: int

    total_revenue_at_risk: float

    recovered_revenue: float

    recovery_rate_percent: float

    payment_history: list[PaymentResponse]


# ------------------------------------------------
# CREATE RAZORPAY ORDER
# ------------------------------------------------

class RazorpayOrderResponse(BaseModel):

    order_id: str

    amount: int

    currency: str

    key_id: str


# ------------------------------------------------
# PAYMENT VERIFICATION
# ------------------------------------------------

class PaymentVerification(BaseModel):

    razorpay_payment_id: str

    razorpay_order_id: str

    razorpay_signature: str

    customer_name: str


# ------------------------------------------------
# FAILED PAYMENT FROM CHECKOUT
# ------------------------------------------------

class FailedPaymentRequest(BaseModel):

    customer_name: str

    amount: float

    payment_method: str

    failure_reason: Optional[str] = "payment_failed"



class PaymentCreate(BaseModel):
    amount: float
    customer_name: str
    payment_method: str
    failure_reason: str