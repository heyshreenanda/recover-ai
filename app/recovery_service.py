def execute_recovery(payment, recovery_action):

    # ------------------------------------------------
    # NO ACTION
    # ------------------------------------------------

    if recovery_action == "no_action":

        return {
            "status": "completed",
            "message": "Payment completed successfully.",
            "recovered": True
        }

    # ------------------------------------------------
    # PAYMENT RETRY
    # ------------------------------------------------

    if recovery_action == "payment_retry":

        return {
            "status": "retry_required",
            "message": "A new payment attempt can be initiated.",
            "recovered": False,
            "retry_required": True
        }

    # ------------------------------------------------
    # RETRY + NOTIFY
    # ------------------------------------------------

    if recovery_action == "retry_and_notify":

        return {
            "status": "retry_required",
            "message": (
                "Payment failed temporarily. "
                "A recovery retry has been prepared."
            ),
            "recovered": False,
            "retry_required": True
        }

    # ------------------------------------------------
    # MANUAL REVIEW
    # ------------------------------------------------

    if recovery_action == "manual_review":

        return {
            "status": "under_review",
            "message": (
                "Payment requires additional verification "
                "before another attempt."
            ),
            "recovered": False,
            "retry_required": False
        }

    # ------------------------------------------------
    # UNKNOWN ACTION
    # ------------------------------------------------

    return {
        "status": "failed",
        "message": "Unknown recovery action.",
        "recovered": False,
        "retry_required": False
    }