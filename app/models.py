from sqlalchemy import Column, Integer, String, Float, Boolean

from app.database import Base


class Payment(Base):

    __tablename__ = "payments"

    # ============================================================
    # PRIMARY KEY
    # ============================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ============================================================
    # CUSTOMER INFORMATION
    # ============================================================

    customer_name = Column(
        String,
        index=True
    )

    # ============================================================
    # PAYMENT INFORMATION
    # ============================================================

    amount = Column(
        Float
    )

    payment_method = Column(
        String
    )

    status = Column(
        String
    )

    failure_reason = Column(
        String,
        nullable=True
    )

    # ============================================================
    # RAZORPAY TRANSACTION INFORMATION
    # ============================================================

    razorpay_payment_id = Column(
        String,
        nullable=True,
        index=True
    )

    razorpay_order_id = Column(
        String,
        nullable=True,
        index=True
    )

    # ============================================================
    # RECOVERAI RISK INFORMATION
    # ============================================================

    revenue_at_risk = Column(
        Float,
        default=0
    )

    risk_score = Column(
        Integer,
        default=0
    )

    # ============================================================
    # RECOVERY INFORMATION
    # ============================================================

    recovery_action = Column(
        String,
        nullable=True
    )

    recovery_status = Column(
        String,
        nullable=True
    )

    recovered = Column(
        Boolean,
        default=False
    )

    recovery_message = Column(
        String,
        nullable=True
    )

    recovery_latency_ms = Column(
        Float,
        nullable=True
    )