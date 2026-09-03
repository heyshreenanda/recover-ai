def diagnose_payment(payment):
    if payment.status != "failed":
        return {
            "root_cause":"No failure",
            "recovery_probability": 0,
            "recommended_action":"no_action",
            "confidence": 1.0
        }
    if payment.failure_reason == "authorization_failure":
            return {
                "root_cause":"Card authorization failure",
                "recovery_probability": 0.85,
                "recommended_action":"payment_retry",
                "confidence": 0.92
            }

    if payment.failure_reason == "timeout":
                return {
                    "root_cause":"Temporary payment timeout",
                    "recovery_probability": 0.70,
                    "recommended_action":"payment_retry",
                    "confidence": 0.85
                }

    return {
           "root_cause":"Unknown payment failure",
                               "recovery_probability": 0.40,
                               "recommended_action":"send_reminder",
                               "confidence": 0.60
    }