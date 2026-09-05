````markdown
# RecoverAI 💳🤖

> AI-Powered Payment Recovery System built with FastAPI, Razorpay, risk analysis, and intelligent recovery strategies.

## 📌 Overview

RecoverAI is a payment recovery platform designed to detect failed payments, analyze payment risk, and automatically determine suitable recovery actions.

The system combines payment processing, risk scoring, recovery logic, and an interactive dashboard to help track failed payments and recovered revenue.

## ✨ Features

- 💳 Razorpay payment integration
- 🔐 Payment verification
- ❌ Failed payment detection
- 🧠 AI-powered payment recovery
- 📊 Risk score calculation
- 🔄 Automated recovery strategy selection
- 💰 Revenue-at-risk tracking
- ✅ Recovered payment tracking
- 📈 Recovery rate calculation
- 📋 Payment activity dashboard
- ⚡ FastAPI REST APIs
- 🗄️ Database-backed payment records
- 📖 Swagger API documentation

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │      Frontend       │
                    │  Payment Dashboard  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │      Backend        │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │    Risk     │  │  Recovery   │  │     AI      │
       │   Engine    │  │   Engine    │  │   Engine    │
       └─────────────┘  └─────────────┘  └─────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │      Database       │
                    │      Payments       │
                    └─────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      Razorpay       │
                    │   Payment Gateway   │
                    └─────────────────────┘
````

## 🛠️ Tech Stack

* **Python**
* **FastAPI**
* **SQLAlchemy**
* **SQLite**
* **Razorpay API**
* **Pydantic**
* **HTML / CSS / JavaScript**
* **AI-based recovery logic**
* **Uvicorn**

## 📂 Project Structure

```text
RAZORPAY/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── ai_engine.py
│   ├── risk_engine.py
│   ├── recovery_engine.py
│   └── recovery_service.py
│
├── venv/
│
├── .env
├── .gitignore
├── README.md
└── recoveryai_old.db
```

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
```

Never commit real API keys or secrets to GitHub.

## 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/your-username/RecoverAI.git
cd RecoverAI
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv razorpay
```

## ▶️ Run the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The application will run at:

```text
http://127.0.0.1:8000
```

## 📖 API Documentation

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

OpenAPI specification:

```text
http://127.0.0.1:8000/openapi.json
```

## 🔌 API Endpoints

### Create Payment Order

```http
POST /create-order
```

Creates a Razorpay payment order.

### Verify Payment

```http
POST /verify-payment
```

Verifies the Razorpay payment signature and records the payment.

### Recover Payment

```http
POST /recover-payment
```

Analyzes a failed payment and determines an appropriate recovery action.

Example recovery response:

```json
{
  "success": true,
  "customer_name": "Shree",
  "amount": 1000,
  "risk_score": 50,
  "failure_reason": "card_declined",
  "recovery_action": "retry_and_notify",
  "recovery_status": "recovered",
  "recovered": true,
  "recovery_message": "Payment of ₹1000.0 was successfully recovered.",
  "recovery_latency_ms": 120
}
```

## 📊 Dashboard

RecoverAI provides a payment recovery dashboard containing:

* Total Payments
* Failed Payments
* Recovered Payments
* Revenue at Risk
* Recovered Revenue
* Recovery Rate
* Payment Activity
* Customer information
* Payment amount
* Payment method
* Payment status
* Risk score
* Recovery status

Example:

```text
Payment Recovery Dashboard

Total Payments       4
Failed Payments      2
Recovered Payments   1

Revenue at Risk      ₹2000
Recovered Revenue    ₹1000
Recovery Rate        50%
```

## 🧠 Recovery Flow

```text
Payment Attempt
       │
       ▼
Payment Successful?
   ┌───┴───┐
  YES      NO
   │        │
   ▼        ▼
Record    Analyze
Payment    Failure
            │
            ▼
       Risk Scoring
            │
            ▼
      Recovery Engine
            │
      ┌─────┼─────┐
      ▼     ▼     ▼
    Retry  Notify  Alternative
                    Method
            │
            ▼
      Recovery Result
            │
            ▼
       Update Database
            │
            ▼
          Dashboard
```

## 🎯 Risk Analysis

The system assigns a risk score to failed payments.

The risk score can be used by the recovery engine to determine the most suitable recovery strategy.

For example:

```text
Payment Failure
      │
      ▼
Risk Analysis
      │
      ├── Low Risk ──────► Retry
      │
      ├── Medium Risk ───► Retry + Notify
      │
      └── High Risk ─────► Alternative Recovery
```

## 🔄 Payment Recovery

RecoverAI is designed to turn failed transactions into successful revenue by applying recovery strategies based on:

* Payment failure reason
* Payment method
* Risk score
* Customer information
* Recovery history

The recovery process records whether the failed payment was successfully recovered.

## 📈 Key Metrics

### Revenue at Risk

Total monetary value associated with failed payments.

```text
Revenue at Risk = Sum of failed payment amounts
```

### Recovered Revenue

Total value recovered through successful recovery attempts.

```text
Recovered Revenue = Sum of recovered payment amounts
```

### Recovery Rate

```text
Recovery Rate =
(Recovered Payments / Failed Payments) × 100
```

## 🔒 Security

* API credentials are stored using environment variables.
* Sensitive credentials should never be committed to Git.
* Razorpay payment signatures are verified before accepting payment results.
* Database records are used to maintain payment and recovery state.

## 🧪 Testing

The APIs can be tested using Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Recommended testing flow:

```text
1. Create payment order
        ↓
2. Complete/test payment
        ↓
3. Verify payment
        ↓
4. Create a failed payment scenario
        ↓
5. Call /recover-payment
        ↓
6. Check recovery response
        ↓
7. Open /dashboard
        ↓
8. Verify updated metrics
```

## 💡 Future Improvements

* Real-time payment failure webhooks
* More advanced ML-based risk prediction
* Customer-specific recovery strategies
* Email/SMS notifications
* Payment retry scheduling
* Multiple payment gateway support
* Advanced analytics and charts
* Authentication and role-based access
* Production-grade PostgreSQL database
* Background task processing
* Recovery success prediction
* Detailed transaction history

## 👩‍💻 Author

**Shreenanda**

Built as a project to explore:

* Generative AI
* Backend Development
* FastAPI
* Payment Systems
* Risk Analysis
* AI-powered Automation
* Database Design

---

⭐ If you found this project interesting, consider giving the repository a star!
PLSPLSPLS 😭👆🏻
