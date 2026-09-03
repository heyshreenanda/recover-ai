from fastapi import FastAPI
from app.schemas import Payment
from app.risk_engine import calculate_risk
from app.ai_engine import diagnose_payment


app = FastAPI(
    title="RecoverAI",
    description="AI-powered revenue recovery agent",
    version="0.1.0"
)

@app.get("/")
def root():
    return{
        "message" : "RecoverAI is running!"
    }

@app.post("/payments")
def create_payment(payment: Payment):
    revenue_at_risk = 0

    if payment.status == "failed":
        revenue_at_risk = payment.amount

    risk_score = calculate_risk(payment)

    diagnosis = diagnose_payment(payment)

    return{
        "customer": payment.customer_name,
        "amount": payment.amount,
        "status": payment.status,
        "revenue_at_risk" : revenue_at_risk,
        "risk_score": risk_score,
        "diagnose" : diagnosis
    }