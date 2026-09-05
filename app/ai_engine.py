# app/ai_engine.py

import os
from google import genai


# ==========================================
# 1. GET GEMINI API KEY
# ==========================================

api_key = os.getenv("MY_API_KEY")

if not api_key:
    raise RuntimeError(
        "MY_API_KEY is not set. "
        "Please set your Gemini API key in PowerShell."
    )


# ==========================================
# 2. CREATE GEMINI CLIENT
# ==========================================

client = genai.Client(api_key=api_key)


# ==========================================
# 3. GENERATE AI RECOVERY MESSAGE
# ==========================================

def generate_recovery_message(payment, recovery_action):
    """
    Uses Gemini to generate a customer-friendly
    payment recovery message.
    """

    customer_name = payment.customer_name
    amount = payment.amount
    failure_reason = payment.failure_reason

    # ------------------------------------------
    # Prompt
    # ------------------------------------------

    prompt = f"""
You are a professional payment recovery assistant
for a fintech company.

Generate a short, polite, empathetic and professional
message for a customer whose payment needs recovery.

Payment details:

Customer name: {customer_name}
Amount: ₹{amount}
Failure reason: {failure_reason}
Recovery action: {recovery_action}

Follow these rules carefully:

1. Address the customer by name.

2. Mention the payment amount.

3. Explain the payment issue in simple language.

4. Clearly tell the customer what they should do next.

5. Be polite, professional and reassuring.

6. NEVER mention the internal risk score.

7. NEVER mention AI, Gemini, prompts, models,
   internal systems or technical implementation.

8. Keep the message under 60 words.

9. Do not promise that the payment will definitely succeed.

10. Do not promise a refund unless the information
    explicitly says a refund is available.

11. If recovery_action is "manual_review":
    Explain that the payment requires additional review
    and that the customer will receive an update.

12. If recovery_action is "payment_retry":
    Ask the customer to retry the payment.

13. If recovery_action is "retry_and_notify":
    Ask the customer to retry the payment and explain
    that they will be notified about further updates.

14. If recovery_action is "no_action":
    Confirm that the payment was completed successfully.

Return ONLY the customer-facing message.
Do not add quotation marks.
Do not add headings.
"""


    # ==========================================
    # 4. CALL GEMINI
    # ==========================================

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )


    # ==========================================
    # 5. RETURN GENERATED MESSAGE
    # ==========================================

    return response.text.strip()