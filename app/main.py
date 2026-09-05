from fastapi import FastAPI

from app.schemas import Payment, PaymentResponse
from app.risk_engine import calculate_risk
from app.recovery_engine import recovery_decision
from app.recovery_service import execute_recovery
from app.ai_engine import generate_recovery_message

from app.database import engine, Base, SessionLocal
from app import models


# ==========================================
# CREATE DATABASE TABLES
# ==========================================

Base.metadata.create_all(bind=engine)


# ==========================================
# FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="RecoverAI",
    description="AI-powered revenue recovery agent",
    version="0.1.0"
)


# ==========================================
# ROOT ENDPOINT
# ==========================================

@app.get("/")
def root():

    return {
        "message": "RecoverAI is running!"
    }


# ==========================================
# CREATE PAYMENT
# ==========================================

@app.post("/payments", response_model=PaymentResponse)
def create_payment(payment: Payment):

    db = SessionLocal()

    try:

        # ======================================
        # 1. CALCULATE REVENUE AT RISK
        # ======================================

        if payment.status == "failed":
            revenue_at_risk = payment.amount
        else:
            revenue_at_risk = 0


        # ======================================
        # 2. CALCULATE RISK SCORE
        # ======================================

        risk_score = calculate_risk(payment)


        # ======================================
        # 3. DECIDE RECOVERY ACTION
        # ======================================

        recovery_action = recovery_decision(
            payment,
            risk_score
        )


        # ======================================
        # 4. EXECUTE RECOVERY
        # ======================================

        recovery_result = execute_recovery(
            payment,
            recovery_action
        )


        # ======================================
        # 5. GENERATE AI CUSTOMER MESSAGE
        # ======================================

        recovery_message = generate_recovery_message(
            payment,
            recovery_action
        )


        # ======================================
        # 6. CREATE DATABASE RECORD
        # ======================================

        db_payment = models.Payment(

            customer_name=payment.customer_name,

            amount=payment.amount,

            payment_method=payment.payment_method,

            status=payment.status,

            failure_reason=payment.failure_reason,

            revenue_at_risk=revenue_at_risk,

            risk_score=risk_score,

            recovery_action=recovery_action,

            recovery_status=recovery_result["status"],

            recovered=recovery_result["recovered"],

            recovery_message=recovery_message
        )


        # ======================================
        # 7. SAVE TO DATABASE
        # ======================================

        db.add(db_payment)

        db.commit()

        db.refresh(db_payment)


        # ======================================
        # 8. RETURN RESULT
        # ======================================

        return db_payment

    finally:

        db.close()


# ==========================================
# GET ALL PAYMENTS
# ==========================================

@app.get(
    "/payments",
    response_model=list[PaymentResponse]
)
def get_payments():

    db = SessionLocal()

    try:

        payments = db.query(
            models.Payment
        ).all()

        return payments

    finally:

        db.close()