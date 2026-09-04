from fastapi import FastAPI
from app.schemas import Payment, PaymentResponse
from app.risk_engine import calculate_risk
from app.ai_engine import diagnose_payment
from app.database import engine, Base, SessionLocal
from app import models

Base.metadata.create_all(bind=engine)

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

@app.post("/payments",response_model=PaymentResponse)
def create_payment(payment: Payment):
    db = SessionLocal()
    
    revenue_at_risk = 0

    if payment.status == "failed":
        revenue_at_risk = payment.amount

    risk_score = calculate_risk(payment)
    #diagnosis = diagnose_payment(payment)

    db_payment = models.Payment(
            customer_name = payment.customer_name,
            amount = payment.amount,
            payment_method = payment.payment_method,
            status = payment.status,
            failure_reason = payment.failure_reason,
            revenue_at_risk = revenue_at_risk,
            risk_score=risk_score)
    
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


@app.get("/payments",response_model=list[PaymentResponse])
def get_payments():
    db = SessionLocal()
    payments = db.query(models.Payment).all()
    db.close()

    return payments