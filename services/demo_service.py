from sqlalchemy.orm import Session
from models.account import Account
from schemas.payment_instruction import PaymentInstruction
from schemas.mesh_packet import MeshPacket
from services.hybrid_crypto_service import HybridCryptoService
from services.mesh_simulator_service import mesh_simulator_service
import uuid
import time
import logging

logger = logging.getLogger(__name__)

class DemoService:
    @staticmethod
    def seed_accounts(db: Session):
        # Clear existing to ensure correct VPAs are seeded if DB already existed
        db.query(Account).delete()
        from models.transaction import Transaction
        db.query(Transaction).delete()
        
        accounts = [
            Account(name="Alice", vpa="alice@demo", phone="+91 9999900001", balance=5000.0),
            Account(name="Bob", vpa="bob@demo", phone="+91 9999900002", balance=1000.0),
            Account(name="Carol", vpa="carol@demo", phone="+91 9999900003", balance=2500.0),
            Account(name="Dave", vpa="dave@demo", phone="+91 9999900004", balance=500.0)
        ]
        db.add_all(accounts)
        db.commit()
        logger.info("Seeded 4 demo accounts")

    @staticmethod
    def simulate_sender_device(sender_vpa: str, receiver_vpa: str, amount: float, pin: str, ttl: int, start_device: str) -> MeshPacket:
        instruction = PaymentInstruction(
            senderVpa=sender_vpa,
            receiverVpa=receiver_vpa,
            amount=amount,
            pinHash=pin,
            nonce=str(uuid.uuid4()),
            signedAt=int(time.time() * 1000)
        )

        ciphertext = HybridCryptoService.encrypt(instruction)

        packet = MeshPacket(
            packetId=str(uuid.uuid4()),
            ttl=ttl,
            createdAt=instruction.signedAt,
            ciphertext=ciphertext
        )

        mesh_simulator_service.inject(start_device, packet)
        return packet

demo_service = DemoService()
