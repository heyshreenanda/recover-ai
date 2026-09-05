from sqlalchemy import Column, Integer, String, Float, Boolean

from app.database import Base


class Payment(Base):

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    customer_name = Column(String)

    amount = Column(Float)

    payment_method = Column(String)

    status = Column(String)

    failure_reason = Column(String, nullable=True)

    revenue_at_risk = Column(Float)

    risk_score = Column(Integer)

    recovery_action = Column(String)

    recovery_status = Column(String)

    recovered = Column(Boolean)

    recovery_message = Column(String)