from fastapi import FastAPI
from app.schemas import Payment, PaymentResponse
from app.risk_engine import calculate_risk
from app.ai_engine import generate_recovery_message
from app.database import engine, Base, SessionLocal
from app import models
from app.recovery_engine import recovery_decision
from app.ai_engine import generate_recovery_message

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
    else:
        revenue_at_risk = 0

    risk_score = calculate_risk(payment)

    recovery_action = recovery_decision(payment, risk_score)
    recovery_message = generate_recovery_message(payment, recovery_action)

    db_payment = models.Payment(
            customer_name = payment.customer_name,
            amount = payment.amount,
            payment_method = payment.payment_method,
            status = payment.status,
            failure_reason = payment.failure_reason,
            revenue_at_risk = revenue_at_risk,
            risk_score=risk_score,
            recovery_action=recovery_action,
            recovery_message=recovery_message
            )
    
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