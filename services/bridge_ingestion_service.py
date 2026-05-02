from sqlalchemy.orm import Session
from schemas.mesh_packet import MeshPacket
from services.hybrid_crypto_service import HybridCryptoService
from services.idempotency_service import idempotency_service
from services.settlement_service import SettlementService
import time
import logging

logger = logging.getLogger(__name__)

class BridgeIngestionService:
    MAX_AGE_SECONDS = 86400

    @staticmethod
    def ingest(db: Session, packet: MeshPacket, bridge_node_id: str, hop_count: int) -> dict:
        try:
            packet_hash = HybridCryptoService.hash_ciphertext(packet.ciphertext)

            # 1. Idempotency Gate
            if not idempotency_service.claim(packet_hash):
                logger.info(f"DUPLICATE packet {packet_hash[:12]}... from bridge {bridge_node_id} — dropped")
                return {"outcome": "DUPLICATE_DROPPED", "packetHash": packet_hash, "reason": None, "transactionId": None}

            # 2. Decrypt
            try:
                instruction = HybridCryptoService.decrypt(packet.ciphertext)
            except Exception as e:
                logger.warning(f"Decryption failed for packet {packet_hash[:12]}...: {str(e)}")
                return {"outcome": "INVALID", "packetHash": packet_hash, "reason": "decryption_failed", "transactionId": None}

            # 3. Freshness check
            now_ms = int(time.time() * 1000)
            age_seconds = (now_ms - instruction.signedAt) / 1000

            if age_seconds > BridgeIngestionService.MAX_AGE_SECONDS:
                logger.warning(f"Packet {packet_hash[:12]}... too old ({age_seconds}s), rejected")
                return {"outcome": "INVALID", "packetHash": packet_hash, "reason": "stale_packet", "transactionId": None}
            if age_seconds < -300: # clock-skew tolerance
                return {"outcome": "INVALID", "packetHash": packet_hash, "reason": "future_dated", "transactionId": None}

            # 4. Settle
            tx = SettlementService.settle(db, instruction, packet_hash, bridge_node_id, hop_count)
            
            return {
                "outcome": tx.status.value,
                "packetHash": packet_hash,
                "reason": None,
                "transactionId": tx.id
            }

        except Exception as e:
            logger.error(f"Ingestion error: {str(e)}", exc_info=True)
            return {"outcome": "INVALID", "packetHash": "?", "reason": f"internal_error: {str(e)}", "transactionId": None}
