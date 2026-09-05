from fastapi import FastAPI

from app.schemas import (
    Payment,
    PaymentResponse,
    CustomerHistoryResponse
)

from app.risk_engine import calculate_risk
from app.ai_engine import generate_recovery_message

from app.database import engine, Base, SessionLocal
from app import models

from app.recovery_engine import recovery_decision
from app.recovery_service import execute_recovery


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="RecoverAI",
    description="AI-powered revenue recovery agent",
    version="0.3.0"
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "RecoverAI is running!",
        "version": "0.3.0"
    }


# ============================================================
# CREATE PAYMENT
# ============================================================

@app.post(
    "/payments",
    response_model=PaymentResponse
)
def create_payment(payment: Payment):

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # REVENUE AT RISK
        # ----------------------------------------------------

        if payment.status == "failed":

            revenue_at_risk = payment.amount

        else:

            revenue_at_risk = 0


        # ----------------------------------------------------
        # RISK SCORE
        # ----------------------------------------------------

        risk_score = calculate_risk(payment)


        # ----------------------------------------------------
        # CUSTOMER HISTORY
        # ----------------------------------------------------

        previous_payments = (
            db.query(models.Payment)
            .filter(
                models.Payment.customer_name
                == payment.customer_name
            )
            .all()
        )


        # Only count previous failed payments
        previous_failures = sum(
            1
            for p in previous_payments
            if p.status == "failed"
        )


        # IMPORTANT:
        # Only failed payments that were actually recovered
        # should count as previous recoveries.
        previous_recoveries = sum(
            1
            for p in previous_payments
            if p.status == "failed"
            and p.recovered is True
        )


        customer_history = {

            "failed_payments": previous_failures,

            "recovered_payments": previous_recoveries

        }


        # ----------------------------------------------------
        # RECOVERY DECISION
        # ----------------------------------------------------

        recovery_action = recovery_decision(

            payment,

            risk_score,

            customer_history

        )


        # ----------------------------------------------------
        # AI MESSAGE
        # ----------------------------------------------------

        recovery_message = generate_recovery_message(

            payment,

            recovery_action

        )


        # ----------------------------------------------------
        # EXECUTE RECOVERY
        # ----------------------------------------------------

        recovery_result = execute_recovery(

            payment,

            recovery_action

        )


        recovery_status = recovery_result[
            "status"
        ]

        recovered = recovery_result[
            "recovered"
        ]

        recovery_latency_ms = recovery_result[
            "recovery_latency_ms"
        ]


        # ----------------------------------------------------
        # SAVE PAYMENT
        # ----------------------------------------------------

        db_payment = models.Payment(

            customer_name=payment.customer_name,

            amount=payment.amount,

            payment_method=payment.payment_method,

            status=payment.status,

            failure_reason=payment.failure_reason,

            revenue_at_risk=revenue_at_risk,

            risk_score=risk_score,

            recovery_action=recovery_action,

            recovery_status=recovery_status,

            recovered=recovered,

            recovery_message=recovery_message,

            recovery_latency_ms=recovery_latency_ms

        )


        db.add(db_payment)

        db.commit()

        db.refresh(db_payment)


        return db_payment


    finally:

        db.close()


# ============================================================
# GET ALL PAYMENTS
# ============================================================

@app.get(
    "/payments",
    response_model=list[PaymentResponse]
)
def get_payments():

    db = SessionLocal()

    try:

        payments = (
            db.query(models.Payment)
            .order_by(
                models.Payment.id.desc()
            )
            .all()
        )

        return payments

    finally:

        db.close()


# ============================================================
# CUSTOMER HISTORY
# ============================================================

@app.get(
    "/customers/{customer_name}/history",
    response_model=CustomerHistoryResponse
)
def get_customer_history(
    customer_name: str
):

    db = SessionLocal()

    try:

        payments = (
            db.query(models.Payment)
            .filter(
                models.Payment.customer_name
                == customer_name
            )
            .order_by(
                models.Payment.id.desc()
            )
            .all()
        )


        # ----------------------------------------------------
        # BASIC COUNTS
        # ----------------------------------------------------

        total_payments = len(payments)


        successful_payments = sum(
            1
            for p in payments
            if p.status == "success"
        )


        failed_payments = sum(
            1
            for p in payments
            if p.status == "failed"
        )


        # ----------------------------------------------------
        # REVENUE AT RISK
        # ----------------------------------------------------

        total_revenue_at_risk = sum(
            p.revenue_at_risk or 0
            for p in payments
        )


        # ----------------------------------------------------
        # RECOVERED REVENUE
        # ----------------------------------------------------

        recovered_revenue = sum(

            p.revenue_at_risk or 0

            for p in payments

            if p.status == "failed"
            and p.recovered is True

        )


        # ----------------------------------------------------
        # RECOVERY RATE
        # ----------------------------------------------------

        recovered_count = sum(

            1

            for p in payments

            if p.status == "failed"
            and p.recovered is True

        )


        if failed_payments > 0:

            recovery_rate = (

                recovered_count
                / failed_payments

            ) * 100

        else:

            recovery_rate = 0


        return {

            "customer_name": customer_name,

            "total_payments": total_payments,

            "successful_payments":
                successful_payments,

            "failed_payments":
                failed_payments,

            "total_revenue_at_risk":
                total_revenue_at_risk,

            "recovered_revenue":
                recovered_revenue,

            "recovery_rate_percent":
                round(
                    recovery_rate,
                    2
                ),

            "payment_history":
                payments

        }

    finally:

        db.close()


# ============================================================
# ANALYTICS
# ============================================================

@app.get("/analytics")
def get_analytics():

    db = SessionLocal()

    try:

        payments = (
            db.query(models.Payment)
            .all()
        )


        # ----------------------------------------------------
        # COUNTS
        # ----------------------------------------------------

        total_payments = len(payments)


        failed_payments = sum(

            1

            for p in payments

            if p.status == "failed"

        )


        # IMPORTANT:
        # Only failed payments recovered by RecoverAI
        # count as recovered payments.

        recovered_payments = sum(

            1

            for p in payments

            if p.status == "failed"
            and p.recovered is True

        )


        # ----------------------------------------------------
        # REVENUE AT RISK
        # ----------------------------------------------------

        total_revenue_at_risk = sum(

            p.revenue_at_risk or 0

            for p in payments

        )


        # ----------------------------------------------------
        # RECOVERED REVENUE
        # ----------------------------------------------------

        recovered_revenue = sum(

            p.revenue_at_risk or 0

            for p in payments

            if p.status == "failed"
            and p.recovered is True

        )


        # ----------------------------------------------------
        # RECOVERY RATE
        # ----------------------------------------------------

        if failed_payments > 0:

            recovery_rate = (

                recovered_payments
                / failed_payments

            ) * 100

        else:

            recovery_rate = 0


        return {

            "total_payments":
                total_payments,

            "failed_payments":
                failed_payments,

            "recovered_payments":
                recovered_payments,

            "total_revenue_at_risk":
                total_revenue_at_risk,

            "recovered_revenue":
                recovered_revenue,

            "recovery_rate_percent":
                round(
                    recovery_rate,
                    2
                )

        }

    finally:

        db.close()