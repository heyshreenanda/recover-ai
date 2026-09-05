from sqlalchemy import Column, Integer, String, Float, Boolean

from app.database import Base


class Payment(Base):

    __tablename__ = "payments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    customer_name = Column(
        String,
        index=True
    )

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

    revenue_at_risk = Column(
        Float,
        default=0
    )

    risk_score = Column(
        Integer,
        default=0
    )

    recovery_action = Column(
        String
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