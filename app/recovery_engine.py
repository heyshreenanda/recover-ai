def recovery_decision(payment, risk_score):

    if payment.status == "success":
        return "no_action"
    if risk_score >= 80:
        return "manual_review"

    if payment.failure_reason == "timeout":
        return "payment_retry"

    if payment.failure_reason == "authorization_failure":
        return "payment_retry"

    return "retry_and_notify"