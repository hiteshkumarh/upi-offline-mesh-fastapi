from pydantic import BaseModel
   
class PaymentInstruction(BaseModel):
    senderVpa: str
    receiverVpa: str
    amount: float
    pinHash: str
    nonce: str
    signedAt: int
