import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_recovery_message(payment, recovery_action):

    if recovery_action == "no_action":
        return f"Hi {payment.customer_name}, your payment of ₹{payment.amount} was completed successfully. Thank you for your payment."

    if recovery_action == "manual_review":
        prompt = f"""
Generate a professional recovery message for a failed payment.

Customer: {payment.customer_name}
Amount: ₹{payment.amount}
Failure reason: {payment.failure_reason}
Recovery action: manual review

Explain that the payment requires additional review.
Keep the message under 40 words.
Do not mention internal risk scores.
"""

    elif recovery_action == "payment_retry":
        prompt = f"""
Generate a professional recovery message for a failed payment.

Customer: {payment.customer_name}
Amount: ₹{payment.amount}
Failure reason: {payment.failure_reason}
Recovery action: payment retry

Ask the customer to retry the payment.
Keep the message under 40 words.
Do not mention internal risk scores.
"""

    elif recovery_action == "retry_and_notify":
        prompt = f"""
Generate a professional recovery message for a failed payment.

Customer: {payment.customer_name}
Amount: ₹{payment.amount}
Failure reason: {payment.failure_reason}
Recovery action: retry and notify

Tell the customer to retry the payment and explain that they will be notified about updates.
Keep the message under 40 words.
Do not mention internal risk scores.
"""

    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    return response.output_text