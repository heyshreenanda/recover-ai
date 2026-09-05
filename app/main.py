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

@app.post("/verify-payment")
def verify_payment(request: VerifyPaymentRequest):

    try:

        razorpay_client.utility.verify_payment_signature({

            "razorpay_payment_id":
                request.razorpay_payment_id,

            "razorpay_order_id":
                request.razorpay_order_id,

            "razorpay_signature":
                request.razorpay_signature

        })

        return {

            "success": True,

            "message":
                "Payment verified successfully.",

            "razorpay_payment_id":
                request.razorpay_payment_id,

            "razorpay_order_id":
                request.razorpay_order_id

        }

    except Exception as e:

        print(
            "RAZORPAY SIGNATURE ERROR:",
            str(e)
        )

        raise HTTPException(
            status_code=400,
            detail="Payment signature verification failed."
        )


# ============================================================
# RECOVER PAYMENT
# ============================================================

@app.post("/recover-payment")
def recover_payment(request: RecoverPaymentRequest):

    # --------------------------------------------------------
    # Create temporary Payment object
    # --------------------------------------------------------

    payment = Payment(

        customer_name=request.customer_name,

        amount=request.amount,

        payment_method=request.payment_method,

        status="failed",

        failure_reason=request.failure_reason

    )


    # --------------------------------------------------------
    # Calculate risk
    # --------------------------------------------------------

    risk_score = calculate_risk(payment)


    # --------------------------------------------------------
    # Get customer history
    # --------------------------------------------------------

    db = SessionLocal()

    try:

        previous_payments = (

            db.query(models.Payment)

            .filter(
                models.Payment.customer_name
                == request.customer_name
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

    finally:

        db.close()


    customer_history = {

        "failed_payments":
            previous_failures,

        "recovered_payments":
            previous_recoveries

    }


    # --------------------------------------------------------
    # RecoverAI decision
    # --------------------------------------------------------

    recovery_action = recovery_decision(

        payment,

        risk_score,

        customer_history

    )


    # --------------------------------------------------------
    # AI recovery message
    # --------------------------------------------------------

    recovery_message = safe_generate_recovery_message(

        payment,

        recovery_action

    )


    # --------------------------------------------------------
    # Execute recovery
    # --------------------------------------------------------

    recovery_result = execute_recovery(

        payment,

        recovery_action

    )


    recovery_status = recovery_result["status"]

    recovered = recovery_result["recovered"]


    # --------------------------------------------------------
    # Save failed payment in database
    # --------------------------------------------------------

    db = SessionLocal()

    try:

        db_payment = models.Payment(

            customer_name=
                request.customer_name,

            amount=
                request.amount,

            payment_method=
                request.payment_method,

            status=
                "failed",

            failure_reason=
                request.failure_reason,

            revenue_at_risk=
                request.amount,

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

    finally:

        db.close()


    # --------------------------------------------------------
    # Return RecoverAI result
    # --------------------------------------------------------

    return {

        "success": True,

        "customer_name":
            request.customer_name,

        "amount":
            request.amount,

        "risk_score":
            risk_score,

        "failure_reason":
            request.failure_reason,

        "recovery_action":
            recovery_action,

        "recovery_status":
            recovery_status,

        "recovered":
            recovered,

        "recovery_message":
            recovery_message

    }


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

        payments = (

            db.query(models.Payment)

            .all()

        )


        total_payments = len(payments)


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


# ============================================================
# RAZORPAY REAL-TIME CHECKOUT DEMO
# ============================================================

@app.get(
    "/checkout",
    response_class=HTMLResponse
)
def checkout():

    return """

    <!DOCTYPE html>

    <html>

    <head>

        <title>RecoverAI Payment Demo</title>

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1"
        >

        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>


        <style>

            * {
                box-sizing: border-box;
            }

            body {

                font-family:
                    Arial,
                    sans-serif;

                background:
                    #f5f7fb;

                display:
                    flex;

                justify-content:
                    center;

                align-items:
                    center;

                min-height:
                    100vh;

                margin:
                    0;

                padding:
                    20px;

            }


            .container {

                width:
                    420px;

                max-width:
                    100%;

                background:
                    white;

                padding:
                    35px;

                border-radius:
                    15px;

                box-shadow:
                    0 10px 30px
                    rgba(0,0,0,0.1);

                text-align:
                    center;

            }


            h1 {

                margin-bottom:
                    5px;

            }


            .subtitle {

                color:
                    #666;

                margin-bottom:
                    30px;

            }


            .amount {

                font-size:
                    36px;

                font-weight:
                    bold;

                margin:
                    25px 0;

            }


            .customer {

                margin-bottom:
                    25px;

            }


            button {

                width:
                    100%;

                padding:
                    15px;

                border:
                    none;

                border-radius:
                    8px;

                background:
                    #3399cc;

                color:
                    white;

                font-size:
                    18px;

                cursor:
                    pointer;

            }


            button:hover {

                background:
                    #287fa8;

            }


            button:disabled {

                background:
                    #999;

                cursor:
                    not-allowed;

            }


            #result {

                margin-top:
                    25px;

                padding:
                    15px;

                border-radius:
                    8px;

                display:
                    none;

                text-align:
                    left;

                white-space:
                    pre-wrap;

                line-height:
                    1.5;

            }


            .success {

                background:
                    #e8f7ee;

                color:
                    #176b38;

            }


            .failure {

                background:
                    #fff0f0;

                color:
                    #a52222;

            }


            .recovery {

                background:
                    #eef4ff;

                color:
                    #174ea6;

            }


            .processing {

                background:
                    #fff8e1;

                color:
                    #795548;

            }

        </style>

    </head>


    <body>


        <div class="container">


            <h1>
                RecoverAI
            </h1>


            <div class="subtitle">

                AI-Powered Payment Recovery

            </div>


            <div class="amount">

                ₹1,000

            </div>


            <div class="customer">

                Customer:
                <strong>
                    Shree
                </strong>

            </div>


            <button
                id="payButton"
                onclick="startPayment()"
            >

                Pay ₹1,000

            </button>


            <div id="result"></div>


        </div>


        <script>


            const CUSTOMER_NAME = "Shree";

            const PAYMENT_AMOUNT = 1000;


            // =================================================
            // DISPLAY RESULT
            // =================================================

            function showResult(
                className,
                message
            ) {

                const resultBox =
                    document.getElementById(
                        "result"
                    );

                resultBox.style.display =
                    "block";

                resultBox.className =
                    className;

                resultBox.innerText =
                    message;

            }


            // =================================================
            // START PAYMENT
            // =================================================

            async function startPayment() {


                const button =
                    document.getElementById(
                        "payButton"
                    );


                button.disabled =
                    true;


                showResult(
                    "processing",
                    "⏳ Creating secure Razorpay order..."
                );


                try {


                    // -----------------------------------------
                    // STEP 1
                    // CREATE ORDER
                    // -----------------------------------------

                    const orderResponse =
                        await fetch(
                            "/create-order",
                            {

                                method:
                                    "POST",

                                headers: {

                                    "Content-Type":
                                        "application/json"

                                },

                                body:
                                    JSON.stringify({

                                        amount:
                                            PAYMENT_AMOUNT,

                                        customer_name:
                                            CUSTOMER_NAME

                                    })

                            }
                        );


                    const orderText =
                        await orderResponse.text();

                    let orderData;

                    try {

                        orderData =
                            JSON.parse(orderText);

                    } catch (parseError) {

                        throw new Error(

                            orderText
                            ||
                            "Create-order returned an invalid response."

                        );

                    }


                    if (!orderResponse.ok) {

                        throw new Error(

                            orderData.detail
                            ||
                            orderData.message
                            ||
                            "Could not create Razorpay order"

                        );

                    }


                    console.log(
                        "Razorpay Order:",
                        orderData
                    );


                    showResult(
                        "processing",
                        "🔐 Opening secure Razorpay Checkout..."
                    );


                    // -----------------------------------------
                    // STEP 2
                    // RAZORPAY OPTIONS
                    // -----------------------------------------

                    const options = {


                        key:
                            orderData.key_id,


                        amount:
                            orderData.amount,


                        currency:
                            orderData.currency,


                        name:
                            "RecoverAI",


                        description:
                            "Payment Recovery Demo",


                        order_id:
                            orderData.order_id,


                        // Explicitly request all supported payment
                        // methods, including UPI.
                        // Razorpay/account configuration can still
                        // determine which methods are ultimately shown.
                        method: {

                            card: true,

                            netbanking: true,

                            wallet: true,

                            upi: true,

                            emi: true,

                            paylater: true

                        },


                        handler:
                            async function(response) {


                                // --------------------------------
                                // PAYMENT SUCCESS
                                // --------------------------------

                                console.log(
                                    "Payment successful:",
                                    response
                                );


                                showResult(
                                    "processing",
                                    "🔍 Verifying payment securely..."
                                );


                                // --------------------------------
                                // STEP 3
                                // VERIFY PAYMENT
                                // --------------------------------

                                const verifyResponse =
                                    await fetch(
                                        "/verify-payment",
                                        {

                                            method:
                                                "POST",

                                            headers: {

                                                "Content-Type":
                                                    "application/json"

                                            },

                                            body:
                                                JSON.stringify({

                                                    razorpay_order_id:
                                                        response.razorpay_order_id,

                                                    razorpay_payment_id:
                                                        response.razorpay_payment_id,

                                                    razorpay_signature:
                                                        response.razorpay_signature

                                                })

                                        }
                                    );


                                const verifyText =
                                    await verifyResponse.text();

                                let verifyResult;

                                try {

                                    verifyResult =
                                        JSON.parse(verifyText);

                                } catch (parseError) {

                                    throw new Error(

                                        verifyText
                                        ||
                                        "Payment verification returned an invalid response."

                                    );

                                }


                                if (!verifyResponse.ok) {

                                    throw new Error(

                                        verifyResult.detail
                                        ||
                                        verifyResult.message
                                        ||
                                        "Payment verification failed"

                                    );

                                }


                                // --------------------------------
                                // SUCCESS
                                // --------------------------------

                                showResult(

                                    "success",

                                    "✅ PAYMENT SUCCESSFUL\\n\\n" +

                                    "Payment verified by Razorpay.\\n\\n" +

                                    JSON.stringify(
                                        verifyResult,
                                        null,
                                        2
                                    )

                                );


                                button.disabled =
                                    false;

                            },


                        // -----------------------------------------
                        // PAYMENT FAILED
                        // -----------------------------------------

                        modal: {

                            ondismiss:
                                function() {

                                    console.log(
                                        "Razorpay checkout closed"
                                    );

                                    button.disabled =
                                        false;

                                    showResult(
                                        "failure",
                                        "ℹ️ Payment window closed."
                                    );

                                }

                        },


                        // -----------------------------------------
                        // CUSTOMER DETAILS
                        // -----------------------------------------

                        prefill: {

                            name:
                                CUSTOMER_NAME,

                            email:
                                "shree@example.com",

                            contact:
                                "9999999999"

                        },


                        notes: {

                            customer:
                                CUSTOMER_NAME,

                            application:
                                "RecoverAI"

                        },


                        theme: {

                            color:
                                "#3399cc"

                        }

                    };


                    // -----------------------------------------
                    // CREATE RAZORPAY INSTANCE
                    // -----------------------------------------

                    const razorpay =
                        new Razorpay(
                            options
                        );


                    // -----------------------------------------
                    // REAL-TIME PAYMENT FAILURE
                    // -----------------------------------------

                    razorpay.on(
                        "payment.failed",
                        async function(response) {


                            console.log(
                                "PAYMENT FAILED:",
                                response
                            );


                            const error =
                                response.error
                                || {};


                            const reason =
                                error.reason
                                ||
                                "payment_failed";


                            const description =
                                error.description
                                ||
                                "Payment failed";


                            // --------------------------------
                            // DISPLAY FAILURE
                            // --------------------------------

                            showResult(

                                "failure",

                                "❌ PAYMENT FAILED\\n\\n" +

                                description +

                                "\\n\\n" +

                                "⚡ RecoverAI is analyzing the failure. AI availability will not affect the payment status."

                            );


                            try {


                                // --------------------------------
                                // TRIGGER RECOVERY ENGINE
                                // --------------------------------

                                const recoveryResponse =
                                    await fetch(
                                        "/recover-payment",
                                        {

                                            method:
                                                "POST",

                                            headers: {

                                                "Content-Type":
                                                    "application/json"

                                            },

                                            body:
                                                JSON.stringify({

                                                    customer_name:
                                                        CUSTOMER_NAME,

                                                    amount:
                                                        PAYMENT_AMOUNT,

                                                    payment_method:
                                                        "razorpay",

                                                    failure_reason:
                                                        reason

                                                })

                                        }
                                    );


                                // Read the response safely. This prevents
                                // errors such as:
                                // Unexpected token 'I', "Internal S"... is not valid JSON
                                // when a server/proxy returns plain text.
                                const recoveryText =
                                    await recoveryResponse.text();

                                let recoveryResult;

                                try {

                                    recoveryResult =
                                        JSON.parse(recoveryText);

                                } catch (parseError) {

                                    throw new Error(

                                        recoveryText
                                        ||
                                        "Recovery engine returned an invalid response."

                                    );

                                }


                                if (!recoveryResponse.ok) {

                                    throw new Error(

                                        recoveryResult.detail
                                        ||
                                        recoveryResult.message
                                        ||
                                        "Recovery engine failed"

                                    );

                                }


                                // --------------------------------
                                // DISPLAY RECOVERY RESULT
                                // --------------------------------

                                showResult(

                                    "recovery",

                                    "⚡ RECOVERAI RECOVERY ENGINE\\n\\n" +

                                    "Payment failed: " +
                                    reason +

                                    "\\n\\n" +

                                    JSON.stringify(
                                        recoveryResult,
                                        null,
                                        2
                                    )

                                );


                            }

                            catch(error) {


                                console.error(
                                    error
                                );


                                showResult(

                                    "failure",

                                    "❌ Payment failed.\\n\\n" +

                                    "RecoverAI recovery analysis could not be completed.\\n\\n" +

                                    error.message

                                );

                            }


                            button.disabled =
                                false;

                        }
                    );


                    // -----------------------------------------
                    // OPEN RAZORPAY
                    // -----------------------------------------

                    razorpay.open();

                }


                catch(error) {


                    console.error(
                        "Payment error:",
                        error
                    );


                    showResult(

                        "failure",

                        "❌ Error\\n\\n" +
                        error.message

                    );


                    button.disabled =
                        false;

                }

            }


        </script>


    </body>

    </html>

    """