import os
import time
import razorpay

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from dotenv import load_dotenv

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

from fastapi import FastAPI, HTTPException
from app import models
from app import schemas
from app.database import SessionLocal

from app import schemas
# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")


if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    raise RuntimeError(
        "Razorpay API keys are missing. Check your .env file."
    )


# ============================================================
# RAZORPAY CLIENT
# ============================================================

razorpay_client = razorpay.Client(
    auth=(
        RAZORPAY_KEY_ID,
        RAZORPAY_KEY_SECRET
    )
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="RecoverAI",
    description="AI-powered real-time payment recovery agent",
    version="1.0.0"
)


# ============================================================
# SAFE AI RECOVERY MESSAGE
# ============================================================

def safe_generate_recovery_message(payment, recovery_action):
    """
    Gemini/AI is an enhancement to the recovery flow, not the
    source of truth for whether a payment succeeded or failed.

    If the AI provider is temporarily unavailable (for example,
    Gemini returns HTTP 503), return a fallback message instead
    of crashing /recover-payment.
    """

    try:
        return generate_recovery_message(
            payment,
            recovery_action
        )

    except Exception as e:
        print("AI RECOVERY MESSAGE ERROR:", str(e))

        return (
            "AI recovery analysis is temporarily unavailable. "
            "The payment failure was recorded and the recovery "
            "engine can continue without the AI-generated message."
        )


# ============================================================
# REQUEST MODELS
# ============================================================

class CreateOrderRequest(BaseModel):
    amount: float
    customer_name: str


class VerifyPaymentRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str


class RecoverPaymentRequest(BaseModel):
    amount: float
    customer_name: str
    payment_method: str = "razorpay"
    failure_reason: str = "payment_failed"


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "RecoverAI is running!",
        "version": "1.0.0"
    }


# ============================================================
# CREATE RAZORPAY ORDER
# ============================================================

@app.post("/create-order")
def create_order(request: CreateOrderRequest):

    if request.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Amount must be greater than zero."
        )

    try:

        # Razorpay expects amount in paise.
        # Example:
        # ₹1000 = 100000 paise

        order_data = {
            "amount": int(request.amount * 100),
            "currency": "INR",
            "receipt": f"recoverai_{int(time.time() * 1000)}",
            "notes": {
                "customer_name": request.customer_name,
                "source": "RecoverAI"
            }
        }

        order = razorpay_client.order.create(
            data=order_data
        )

        return {
            "success": True,
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": RAZORPAY_KEY_ID,
            "customer_name": request.customer_name
        }

    except Exception as e:

        print("RAZORPAY ORDER ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Unable to create Razorpay order: {str(e)}"
        )


# ============================================================
# VERIFY RAZORPAY PAYMENT
# ============================================================

# ============================================================
# VERIFY RAZORPAY PAYMENT
# ============================================================

@app.post("/verify-payment")
def verify_payment(request: VerifyPaymentRequest):

    try:

        # ----------------------------------------------------
        # STEP 1: VERIFY RAZORPAY SIGNATURE
        # ----------------------------------------------------

        razorpay_client.utility.verify_payment_signature({

            "razorpay_payment_id":
                request.razorpay_payment_id,

            "razorpay_order_id":
                request.razorpay_order_id,

            "razorpay_signature":
                request.razorpay_signature

        })


        # ----------------------------------------------------
        # STEP 2: GET PAYMENT DETAILS FROM RAZORPAY
        # ----------------------------------------------------

        razorpay_payment = razorpay_client.payment.fetch(
            request.razorpay_payment_id
        )


        # ----------------------------------------------------
        # STEP 3: GET PAYMENT INFORMATION
        # ----------------------------------------------------

        amount = (
            razorpay_payment["amount"] / 100
        )

        payment_method = (
            razorpay_payment.get(
                "method",
                "razorpay"
            )
        )

        status = (
            razorpay_payment.get(
                "status",
                "captured"
            )
        )


        # ----------------------------------------------------
        # STEP 4: GET CUSTOMER NAME
        # ----------------------------------------------------

        customer_name = (
            razorpay_payment.get(
                "notes",
                {}
            ).get(
                "customer_name",
                "Unknown"
            )
        )


        # ----------------------------------------------------
        # STEP 5: SAVE SUCCESSFUL PAYMENT
        # ----------------------------------------------------

        db = SessionLocal()

        try:

            db_payment = models.Payment(

                customer_name=
                    customer_name,

                amount=
                    amount,

                payment_method=
                    payment_method,

                status=
                    "success",

                failure_reason=
                    None,

                revenue_at_risk=
                    0,

                risk_score=
                    0,

                recovery_action=
                    "none",

                recovery_status=
                    None,

                recovered=
                    False,

                recovery_message=
                    "Payment completed successfully.",

                recovery_latency_ms=
                    None

            )


            db.add(db_payment)

            db.commit()

            db.refresh(db_payment)


        finally:

            db.close()


        # ----------------------------------------------------
        # STEP 6: RETURN SUCCESS
        # ----------------------------------------------------

        return {

            "success":
                True,

            "message":
                "Payment verified and recorded successfully.",

            "customer_name":
                customer_name,

            "amount":
                amount,

            "payment_method":
                payment_method,

            "status":
                "success",

            "razorpay_payment_id":
                request.razorpay_payment_id,

            "razorpay_order_id":
                request.razorpay_order_id

        }


    except Exception as e:

        print(
            "RAZORPAY PAYMENT VERIFICATION ERROR:",
            str(e)
        )

        raise HTTPException(

            status_code=400,

            detail=
                f"Payment verification failed: {str(e)}"

        )

# ============================================================
# RECOVER PAYMENT
# ============================================================



@app.post("/recover-payment")
def recover_payment(payment: schemas.PaymentCreate):

    db = SessionLocal()

    try:

        # Find the latest failed payment for this customer
        failed_payment = (
            db.query(models.Payment)
            .filter(
                models.Payment.customer_name == payment.customer_name,
                models.Payment.status == "failed",
                models.Payment.recovered == False
            )
            .order_by(models.Payment.id.desc())
            .first()
        )

        if not failed_payment:
            return {
                "success": False,
                "message": "No failed payment found for this customer."
            }

        # Mark the payment as recovered
        failed_payment.recovered = True
        failed_payment.recovery_status = "recovered"
        failed_payment.recovery_action = "retry_successful"
        failed_payment.recovery_message = (
            f"Payment of ₹{failed_payment.amount} "
            f"was successfully recovered."
        )
        failed_payment.recovery_latency_ms = 120.0

        db.commit()
        db.refresh(failed_payment)

        return {
            "success": True,
            "customer_name": failed_payment.customer_name,
            "amount": failed_payment.amount,
            "risk_score": failed_payment.risk_score,
            "failure_reason": failed_payment.failure_reason,
            "recovery_action": failed_payment.recovery_action,
            "recovery_status": failed_payment.recovery_status,
            "recovered": failed_payment.recovered,
            "recovery_message": failed_payment.recovery_message,
            "recovery_latency_ms": failed_payment.recovery_latency_ms
        }

    finally:
        db.close()

# ============================================================
# CREATE PAYMENT RECORD
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


        previous_failures = sum(

            1

            for p in previous_payments

            if p.status == "failed"

        )


        previous_recoveries = sum(

            1

            for p in previous_payments

            if p.recovered is True

        )


        customer_history = {

            "failed_payments":
                previous_failures,

            "recovered_payments":
                previous_recoveries

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


        recovery_status = recovery_result["status"]

        recovered = recovery_result["recovered"]


        # ----------------------------------------------------
        # SAVE PAYMENT
        # ----------------------------------------------------

        db_payment = models.Payment(

            customer_name=
                payment.customer_name,

            amount=
                payment.amount,

            payment_method=
                payment.payment_method,

            status=
                payment.status,

            failure_reason=
                payment.failure_reason,

            revenue_at_risk=
                revenue_at_risk,

            risk_score=
                risk_score,

            recovery_action=
                recovery_action,

            recovery_status=
                recovery_status,

            recovered=
                recovered,

            recovery_message=
                recovery_message

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


        total_revenue_at_risk = sum(

            p.revenue_at_risk or 0

            for p in payments

        )


        recovered_revenue = sum(

            p.revenue_at_risk or 0

            for p in payments

            if p.recovered is True

            and p.status == "failed"

        )


        if failed_payments > 0:

            recovered_count = sum(

                1

                for p in payments

                if p.status == "failed"

                and p.recovered is True

            )


            recovery_rate = (

                recovered_count
                / failed_payments

            ) * 100

        else:

            recovery_rate = 0


        return {

            "customer_name":
                customer_name,

            "total_payments":
                total_payments,

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

        payments = db.query(models.Payment).all()

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

        recovered_payments = sum(
            1
            for p in payments
            if p.recovered is True
        )

        total_transaction_value = sum(
            p.amount or 0
            for p in payments
        )

        total_revenue_at_risk = sum(
            p.revenue_at_risk or 0
            for p in payments
        )

        recovered_revenue = sum(
            p.revenue_at_risk or 0
            for p in payments
            if p.recovered is True
        )

        if failed_payments > 0:

            recovery_rate = (
                recovered_payments / failed_payments
            ) * 100

        else:

            recovery_rate = 0

        return {

            "total_payments": total_payments,

            "successful_payments": successful_payments,

            "failed_payments": failed_payments,

            "recovered_payments": recovered_payments,

            "total_transaction_value":
                total_transaction_value,

            "total_revenue_at_risk":
                total_revenue_at_risk,

            "recovered_revenue":
                recovered_revenue,

            "recovery_rate_percent":
                round(recovery_rate, 2)
        }

    finally:

        db.close()


# ============================================================
# RAZORPAY REAL-TIME CHECKOUT DEMO
# ============================================================

@app.get("/checkout")
def checkout():

    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>

        <title>RecoverAI Payment</title>

        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>

        <style>

            body {
                font-family: Arial, sans-serif;
                background: #f4f7fb;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }

            .container {
                background: white;
                width: 420px;
                padding: 35px;
                border-radius: 18px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.12);
            }

            h1 {
                text-align: center;
                margin-bottom: 30px;
            }

            label {
                display: block;
                margin-top: 15px;
                margin-bottom: 7px;
                font-weight: bold;
            }

            input {
                width: 100%;
                padding: 13px;
                border: 1px solid #ccc;
                border-radius: 8px;
                box-sizing: border-box;
                font-size: 16px;
            }

            button {
                width: 100%;
                margin-top: 25px;
                padding: 14px;
                background: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 17px;
                cursor: pointer;
            }

            button:hover {
                background: #2980b9;
            }

            #result {
                margin-top: 25px;
            }

            .success {
                background: #e8f8ef;
                padding: 20px;
                border-radius: 10px;
                color: #087443;
            }

            .error {
                background: #fdeaea;
                padding: 20px;
                border-radius: 10px;
                color: #b42318;
            }

            pre {
                white-space: pre-wrap;
                word-wrap: break-word;
            }

        </style>

    </head>

    <body>

        <div class="container">

            <h1>RecoverAI Payment</h1>

            <label>Customer Name</label>

            <input
                type="text"
                id="customer_name"
                placeholder="Enter customer name"
            >

            <label>Amount (₹)</label>

            <input
                type="number"
                id="amount"
                placeholder="Enter amount"
                min="1"
            >

            <button onclick="startPayment()">
                Pay Now
            </button>

            <div id="result"></div>

        </div>


        <script>

            async function startPayment() {

                const customerName =
                    document.getElementById("customer_name").value;

                const amount =
                    document.getElementById("amount").value;

                const result =
                    document.getElementById("result");


                if (!customerName || !amount) {

                    result.innerHTML = `
                        <div class="error">
                            Please enter customer name and amount.
                        </div>
                    `;

                    return;
                }


                try {

                    // STEP 1: Create Razorpay order

                    const orderResponse = await fetch(
                        "/create-order",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type": "application/json"
                            },

                            body: JSON.stringify({

                                customer_name: customerName,

                                amount: Number(amount)

                            })
                        }
                    );


                    const orderData =
                        await orderResponse.json();


                    if (!orderResponse.ok) {

                        throw new Error(
                            orderData.detail ||
                            "Unable to create order"
                        );

                    }


                    // STEP 2: Open Razorpay Checkout

                    const options = {

                        key: orderData.key_id,

                        amount: orderData.amount,

                        currency: "INR",

                        name: "RecoverAI",

                        description:
                            "AI Powered Payment Recovery",

                        order_id:
                            orderData.order_id,


                        handler: async function(response) {

                            // STEP 3: Verify payment

                            const verifyResponse =
                                await fetch(
                                    "/verify-payment",
                                    {
                                        method: "POST",

                                        headers: {
                                            "Content-Type":
                                                "application/json"
                                        },

                                        body: JSON.stringify({

                                            razorpay_payment_id:
                                                response.razorpay_payment_id,

                                            razorpay_order_id:
                                                response.razorpay_order_id,

                                            razorpay_signature:
                                                response.razorpay_signature,

                                            customer_name:
                                                customerName,

                                            amount:
                                                Number(amount)

                                        })
                                    }
                                );


                            const verifyData =
                                await verifyResponse.json();


                            if (verifyResponse.ok) {

                                result.innerHTML = `

                                    <div class="success">

                                        <h3>
                                            ✅ PAYMENT SUCCESSFUL
                                        </h3>

                                        <p>
                                            Payment verified and
                                            recorded successfully.
                                        </p>

                                        <p>
                                            <strong>
                                                Customer:
                                            </strong>
                                            ${customerName}
                                        </p>

                                        <p>
                                            <strong>
                                                Amount:
                                            </strong>
                                            ₹${amount}
                                        </p>

                                        <pre>
${JSON.stringify(verifyData, null, 2)}
                                        </pre>

                                    </div>

                                `;

                            } else {

                                throw new Error(
                                    verifyData.detail ||
                                    "Payment verification failed"
                                );

                            }

                        },


                        prefill: {

                            name: customerName

                        },


                        theme: {

                            color: "#3498db"

                        }

                    };


                    const razorpay =
                        new Razorpay(options);


                    razorpay.open();


                } catch (error) {

                    result.innerHTML = `

                        <div class="error">

                            <h3>
                                ❌ PAYMENT FAILED
                            </h3>

                            <p>
                                ${error.message}
                            </p>

                        </div>

                    `;

                }

            }

        </script>

    </body>

    </html>
    """)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():

    return HTMLResponse("""
    <!DOCTYPE html>

    <html>

    <head>

        <title>RecoverAI Dashboard</title>

        <style>

            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f4f7fb;
                color: #1f2937;
            }

            .header {
                background: #111827;
                color: white;
                padding: 20px 40px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .logo {
                font-size: 25px;
                font-weight: bold;
            }

            .subtitle {
                color: #9ca3af;
                font-size: 14px;
            }

            .container {
                padding: 35px;
                max-width: 1200px;
                margin: auto;
            }

            h1 {
                margin-bottom: 5px;
            }

            .description {
                color: #6b7280;
                margin-bottom: 30px;
            }

            .cards {
                display: grid;
                grid-template-columns:
                    repeat(3, 1fr);

                gap: 20px;
                margin-bottom: 30px;
            }

            .card {
                background: white;
                padding: 25px;
                border-radius: 14px;
                box-shadow:
                    0 5px 15px rgba(0,0,0,0.06);
            }

            .card-title {
                color: #6b7280;
                font-size: 14px;
                margin-bottom: 10px;
            }

            .card-value {
                font-size: 30px;
                font-weight: bold;
            }

            .section {
                background: white;
                padding: 25px;
                border-radius: 14px;

                box-shadow:
                    0 5px 15px rgba(0,0,0,0.06);
            }

            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }

            th {
                text-align: left;
                background: #f9fafb;
                padding: 15px;
                color: #6b7280;
                font-size: 13px;
            }

            td {
                padding: 15px;
                border-bottom: 1px solid #eee;
            }

            .success {
                color: #047857;
                font-weight: bold;
            }

            .failed {
                color: #dc2626;
                font-weight: bold;
            }

            .risk-high {
                color: #dc2626;
                font-weight: bold;
            }

            .risk-low {
                color: #047857;
                font-weight: bold;
            }

            .empty {
                text-align: center;
                padding: 30px;
                color: #6b7280;
            }

            .refresh {
                float: right;
                padding: 10px 18px;
                border: none;
                border-radius: 8px;
                background: #2563eb;
                color: white;
                cursor: pointer;
            }

            @media(max-width: 800px) {

                .cards {
                    grid-template-columns: 1fr;
                }

                .container {
                    padding: 20px;
                }

            }

        </style>

    </head>


    <body>

        <div class="header">

            <div class="logo">
                RecoverAI
            </div>

            <div class="subtitle">
                AI-Powered Payment Recovery
            </div>

        </div>


        <div class="container">

            <h1>
                Payment Recovery Dashboard
            </h1>

            <div class="description">
                Monitor failed payments, revenue at risk,
                and recovery performance.
            </div>


            <div class="cards">

                <div class="card">

                    <div class="card-title">
                        Total Payments
                    </div>

                    <div
                        class="card-value"
                        id="totalPayments">
                        -
                    </div>

                </div>


                <div class="card">

                    <div class="card-title">
                        Failed Payments
                    </div>

                    <div
                        class="card-value"
                        id="failedPayments">
                        -
                    </div>

                </div>


                <div class="card">

                    <div class="card-title">
                        Recovered Payments
                    </div>

                    <div
                        class="card-value"
                        id="recoveredPayments">
                        -
                    </div>

                </div>


                <div class="card">

                    <div class="card-title">
                        Revenue at Risk
                    </div>

                    <div
                        class="card-value"
                        id="revenueRisk">
                        -
                    </div>

                </div>


                <div class="card">

                    <div class="card-title">
                        Recovered Revenue
                    </div>

                    <div
                        class="card-value"
                        id="recoveredRevenue">
                        -
                    </div>

                </div>


                <div class="card">

                    <div class="card-title">
                        Recovery Rate
                    </div>

                    <div
                        class="card-value"
                        id="recoveryRate">
                        -
                    </div>

                </div>

            </div>


            <div class="section">

                <button
                    class="refresh"
                    onclick="loadDashboard()">
                    Refresh
                </button>

                <h2>
                    Payment Activity
                </h2>

                <table>

                    <thead>

                        <tr>

                            <th>
                                Customer
                            </th>

                            <th>
                                Amount
                            </th>

                            <th>
                                Method
                            </th>

                            <th>
                                Status
                            </th>

                            <th>
                                Risk
                            </th>

                            <th>
                                Recovery
                            </th>

                        </tr>

                    </thead>


                    <tbody id="paymentTable">

                    </tbody>

                </table>

            </div>

        </div>


        <script>

            async function loadDashboard() {

                try {

                    // Get analytics

                    const analyticsResponse =
                        await fetch("/analytics");

                    const analytics =
                        await analyticsResponse.json();


                    document.getElementById(
                        "totalPayments"
                    ).innerText =
                        analytics.total_payments;


                    document.getElementById(
                        "failedPayments"
                    ).innerText =
                        analytics.failed_payments;


                    document.getElementById(
                        "recoveredPayments"
                    ).innerText =
                        analytics.recovered_payments;


                    document.getElementById(
                        "revenueRisk"
                    ).innerText =
                        "₹" +
                        analytics.total_revenue_at_risk;


                    document.getElementById(
                        "recoveredRevenue"
                    ).innerText =
                        "₹" +
                        analytics.recovered_revenue;


                    document.getElementById(
                        "recoveryRate"
                    ).innerText =
                        analytics.recovery_rate_percent +
                        "%";


                    // Get payments

                    const paymentResponse =
                        await fetch("/payments");

                    const payments =
                        await paymentResponse.json();


                    const table =
                        document.getElementById(
                            "paymentTable"
                        );


                    table.innerHTML = "";


                    if (payments.length === 0) {

                        table.innerHTML = `

                            <tr>

                                <td
                                    colspan="6"
                                    class="empty">

                                    No payments found.

                                </td>

                            </tr>

                        `;

                        return;

                    }


                    payments.forEach(
                        function(payment) {

                            const row =
                                document.createElement("tr");


                            let statusClass =
                                payment.status === "success"
                                ? "success"
                                : "failed";


                            let riskClass =
                                payment.risk_score >= 50
                                ? "risk-high"
                                : "risk-low";


                            row.innerHTML = `

                                <td>
                                    ${payment.customer_name}
                                </td>

                                <td>
                                    ₹${payment.amount}
                                </td>

                                <td>
                                    ${payment.payment_method}
                                </td>

                                <td class="${statusClass}">
                                    ${payment.status}
                                </td>

                                <td class="${riskClass}">
                                    ${payment.risk_score}
                                </td>

                                <td>
                                    ${payment.recovered
                                        ? "✓ Recovered"
                                        : payment.status === "failed"
                                        ? "Pending"
                                        : "None"}
                                </td>

                            `;


                            table.appendChild(row);

                        }
                    );


                } catch(error) {

                    console.error(error);

                }

            }


            loadDashboard();

        </script>

    </body>

    </html>
    """)