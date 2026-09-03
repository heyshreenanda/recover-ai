def calculate_risk(payment):
    score = 0

    if payment.status == "failed":
        score += 50

    if payment.amount >= 10000:
        score += 20

    if payment.payment_method == "card":
        score += 10

    if payment.failure_reason == "authorization_failure":
        score += 20

    if score > 100:
        score = 100

    return score