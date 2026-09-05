import time


def execute_recovery(payment, recovery_action):

    """
    Executes the recovery strategy.

    This project currently simulates the payment gateway retry.
    In production, this function would call the actual payment
    gateway API.
    """

    start_time = time.perf_counter()

    # ---------------------------------------------
    # NO ACTION
    # ---------------------------------------------

    if recovery_action == "no_action":

        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        return {
            "status": "completed",
            "message": "Payment completed successfully.",
            "recovered": True,
            "recovery_latency_ms": round(latency_ms, 3)
        }

    # ---------------------------------------------
    # PAYMENT RETRY
    # ---------------------------------------------

    if recovery_action == "payment_retry":

        # Simulated instant payment gateway retry
        retry_success = True

        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        if retry_success:

            return {
                "status": "recovered",
                "message": "Payment retry succeeded and the payment was recovered.",
                "recovered": True,
                "recovery_latency_ms": round(latency_ms, 3)
            }

        return {
            "status": "retry_failed",
            "message": "Automatic payment retry failed.",
            "recovered": False,
            "recovery_latency_ms": round(latency_ms, 3)
        }

    # ---------------------------------------------
    # RETRY + NOTIFY
    # ---------------------------------------------

    if recovery_action == "retry_and_notify":

        # Simulated instant retry
        retry_success = True

        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        if retry_success:

            return {
                "status": "recovered_and_notified",
                "message": (
                    "Payment retry succeeded and the customer "
                    "notification was prepared."
                ),
                "recovered": True,
                "recovery_latency_ms": round(latency_ms, 3)
            }

        return {
            "status": "retry_failed_notification_pending",
            "message": (
                "Payment retry failed. Customer notification "
                "has been prepared."
            ),
            "recovered": False,
            "recovery_latency_ms": round(latency_ms, 3)
        }

    # ---------------------------------------------
    # MANUAL REVIEW
    # ---------------------------------------------

    if recovery_action == "manual_review":

        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        return {
            "status": "under_review",
            "message": (
                "Payment sent for manual review because "
                "automatic recovery is considered unsafe."
            ),
            "recovered": False,
            "recovery_latency_ms": round(latency_ms, 3)
        }

    # ---------------------------------------------
    # UNKNOWN ACTION
    # ---------------------------------------------

    latency_ms = (
        time.perf_counter() - start_time
    ) * 1000

    return {
        "status": "recovery_failed",
        "message": "Unknown recovery action.",
        "recovered": False,
        "recovery_latency_ms": round(latency_ms, 3)
    }