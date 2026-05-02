from sqlalchemy import Column, String, Float, Integer
from db.database import Base

class Account(Base):
    __tablename__ = "accounts"

    vpa = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    balance = Column(Float, nullable=False, default=0.0)
    version = Column(Integer, nullable=False, default=0) # For optimistic locking
