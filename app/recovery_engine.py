def recovery_decision(payment, risk_score, customer_history=None):

    # Successful payments need no recovery
    if payment.status == "success":
        return "no_action"

    # Customer history
    previous_failures = 0
    previous_recoveries = 0

    if customer_history:
        previous_failures = customer_history.get(
            "failed_payments", 0
        )

        previous_recoveries = customer_history.get(
            "recovered_payments", 0
        )

    # ---------------------------------------------
    # HIGH RISK
    # ---------------------------------------------

    if risk_score >= 80:
        return "manual_review"

    # ---------------------------------------------
    # REPEATED FAILURES
    # ---------------------------------------------

    if previous_failures >= 2:
        return "manual_review"

    # ---------------------------------------------
    # CUSTOMER RECOVERED BEFORE
    # ---------------------------------------------

    if previous_recoveries >= 1:
        return "retry_and_notify"

    # ---------------------------------------------
    # MEDIUM RISK
    # ---------------------------------------------

    if risk_score >= 50:
        return "retry_and_notify"

    # ---------------------------------------------
    # LOW RISK FAILURE
    # ---------------------------------------------

    return "payment_retry"