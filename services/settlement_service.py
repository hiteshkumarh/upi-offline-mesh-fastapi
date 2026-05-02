from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from models.account import Account
from models.transaction import Transaction, TransactionStatus
from schemas.payment_instruction import PaymentInstruction
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SettlementService:
    @staticmethod
    def settle(db: Session, instruction: PaymentInstruction, packet_hash: str, bridge_node_id: str, hop_count: int) -> Transaction:
        # We handle transactions manually via session
        sender = db.query(Account).filter(Account.vpa == instruction.senderVpa).with_for_update().first()
        if not sender:
            raise ValueError(f"Unknown sender VPA: {instruction.senderVpa}")

        receiver = db.query(Account).filter(Account.vpa == instruction.receiverVpa).with_for_update().first()
        if not receiver:
            raise ValueError(f"Unknown receiver VPA: {instruction.receiverVpa}")

        amount = instruction.amount
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if sender.balance < amount:
            logger.warning(f"Insufficient balance: {sender.vpa} has {sender.balance}, tried to send {amount}")
            return SettlementService.record_rejected(db, instruction, packet_hash, bridge_node_id, hop_count)

        sender.balance -= amount
        sender.version += 1
        receiver.balance += amount
        receiver.version += 1

        tx = Transaction(
            packet_hash=packet_hash,
            sender_vpa=instruction.senderVpa,
            receiver_vpa=instruction.receiverVpa,
            amount=amount,
            signed_at=datetime.fromtimestamp(instruction.signedAt / 1000.0),
            settled_at=datetime.utcnow(),
            bridge_node_id=bridge_node_id,
            hop_count=hop_count,
            status=TransactionStatus.SETTLED
        )
        db.add(tx)
        
        try:
            db.commit()
            db.refresh(tx)
            logger.info(f"SETTLED {amount} from {sender.vpa} to {receiver.vpa} (packetHash={packet_hash[:12]}..., bridge={bridge_node_id}, hops={hop_count})")
            return tx
        except StaleDataError:
            db.rollback()
            raise ValueError("Optimistic lock failed")
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def record_rejected(db: Session, instruction: PaymentInstruction, packet_hash: str, bridge_node_id: str, hop_count: int) -> Transaction:
        tx = Transaction(
            packet_hash=packet_hash,
            sender_vpa=instruction.senderVpa,
            receiver_vpa=instruction.receiverVpa,
            amount=instruction.amount,
            signed_at=datetime.fromtimestamp(instruction.signedAt / 1000.0),
            settled_at=datetime.utcnow(),
            bridge_node_id=bridge_node_id,
            hop_count=hop_count,
            status=TransactionStatus.REJECTED
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx
