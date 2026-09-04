from sqlalchemy import Column, Integer, String, Float
from app.database import Base
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key = True, index= True )
    customer_name = Column(String, nullable=False)
    amount = Column(Float, nullable= False)
    payment_method = Column(String, nullable= False)
    status = Column(String, nullable= False)
    failure_reason = Column(String, nullable= True)
    revenue_at_risk = Column(Float, default= 0)
    risk_score = Column(Float, default=0)