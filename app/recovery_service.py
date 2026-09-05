def execute_recovery(payment, recovery_action):
    """
    Executes the recovery action for a failed payment.

    This is currently a simulation of the actual recovery process.
    In a production system, this would connect to a payment gateway,
    notification service, or manual review system.
    """

    # ------------------------------------------
    # 1. NO ACTION
    # ------------------------------------------

    if recovery_action == "no_action":
        return {
            "status": "completed",
            "message": "Payment already completed successfully.",
            "recovered": True
        }

    # ------------------------------------------
    # 2. PAYMENT RETRY
    # ------------------------------------------

    if recovery_action == "payment_retry":

        # Simulate initiating a payment retry
        return {
            "status": "retry_attempted",
            "message": "Payment retry initiated.",
            "recovered": True
        }

    # ------------------------------------------
    # 3. RETRY AND NOTIFY
    # ------------------------------------------

    if recovery_action == "retry_and_notify":

        # Simulate retry + customer notification
        return {
            "status": "retry_and_notification",
            "message": "Payment retry initiated and customer notification scheduled.",
            "recovered": True
        }

    # ------------------------------------------
    # 4. MANUAL REVIEW
    # ------------------------------------------

    if recovery_action == "manual_review":

        # Simulate sending transaction for manual review
        return {
            "status": "under_review",
            "message": "Payment sent for manual review.",
            "recovered": False
        }

    # ------------------------------------------
    # 5. UNKNOWN ACTION
    # ------------------------------------------

    return {
        "status": "failed",
        "message": "Unknown recovery action.",
        "recovered": False
    }