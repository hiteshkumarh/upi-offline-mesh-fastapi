from sqlalchemy import Column, String, Float, Integer, Enum, DateTime
from db.database import Base
import enum
from datetime import datetime

class TransactionStatus(enum.Enum): 
    SETTLED = "SETTLED"
    REJECTED = "REJECTED"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    packet_hash = Column(String, unique=True, index=True)
    sender_vpa = Column(String, nullable=False)
    receiver_vpa = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    signed_at = Column(DateTime, nullable=False)
    settled_at = Column(DateTime, default=datetime.utcnow)
    bridge_node_id = Column(String, nullable=True)
    hop_count = Column(Integer, nullable=True)
    status = Column(Enum(TransactionStatus), nullable=False)
