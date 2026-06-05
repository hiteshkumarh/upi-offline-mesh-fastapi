from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from db.database import get_db
from models.account import Account
from models.transaction import Transaction
from services.server_key_holder import server_key_holder
from services.demo_service import demo_service
from services.mesh_simulator_service import mesh_simulator_service
from services.bridge_ingestion_service import BridgeIngestionService
from services.idempotency_service import idempotency_service
from schemas.mesh_packet import MeshPacket
import concurrent.futures
    
router = APIRouter(prefix="/api")

class SendRequest(BaseModel):
    senderVpa: str
    receiverVpa: str
    amount: float
    pin: str
    ttl: Optional[int] = 5
    startDevice: Optional[str] = "phone-alice"

@router.get("/server-key")
def get_server_key():
    return {
        "publicKey": server_key_holder.get_public_key_base64(),
        "algorithm": "RSA-2048 / OAEP-SHA256",
        "hybridScheme": "RSA-OAEP encrypts an AES-256-GCM session key"
    }

@router.get("/accounts")
def get_accounts(db: Session = Depends(get_db)):
    accounts = db.query(Account).all()
    return [{"vpa": a.vpa, "holderName": a.name, "balance": a.balance} for a in accounts]

@router.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    txs = db.query(Transaction).order_by(Transaction.id.desc()).limit(20).all()
    return [
        {
            "id": t.id,
            "senderVpa": t.sender_vpa,
            "receiverVpa": t.receiver_vpa,
            "amount": t.amount,
            "status": t.status.value if hasattr(t.status, 'value') else t.status,
            "bridgeNodeId": t.bridge_node_id,
            "hopCount": t.hop_count,
            "settledAt": t.settled_at
        }
        for t in txs
    ]

@router.post("/demo/send")
def demo_send(req: SendRequest):
    packet = demo_service.simulate_sender_device(
        req.senderVpa, req.receiverVpa, req.amount, req.pin, req.ttl, req.startDevice
    )
    return {
        "packetId": packet.packetId,
        "ciphertextPreview": packet.ciphertext[:64] + "...",
        "ttl": packet.ttl,
        "injectedAt": req.startDevice
    }

@router.get("/mesh/state")
def get_mesh_state():
    deviceData = []
    for d in mesh_simulator_service.get_devices():
        deviceData.append({
            "deviceId": d.get_device_id(),
            "hasInternet": d.has_internet(),
            "packetCount": d.packet_count(),
            "packetIds": [p.packetId[:8] for p in d.get_held_packets()]
        })
    return {
        "devices": deviceData,
        "idempotencyCacheSize": idempotency_service.size()
    }

@router.post("/mesh/gossip")
def run_gossip():
    res = mesh_simulator_service.gossip_once()
    return {
        "transfers": res["transfers"],
        "deviceCounts": res["deviceCounts"]
    }

@router.post("/mesh/flush")
def flush_bridges():
    uploads = mesh_simulator_service.collect_bridge_uploads()
    results = []
    
    def process_upload(up):
        from db.database import SessionLocal
        local_db = SessionLocal()
        try:
            res = BridgeIngestionService.ingest(local_db, up["packet"], up["bridgeNodeId"], 5 - up["packet"].ttl)
            return {
                "bridgeNode": up["bridgeNodeId"],
                "packetId": up["packet"].packetId[:8],
                "outcome": res["outcome"],
                "reason": res["reason"] or "",
                "transactionId": res["transactionId"] or -1
            }
        finally:
            local_db.close()

    if uploads:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(uploads)) as executor:
            futures = [executor.submit(process_upload, up) for up in uploads]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

    # clear devices
    for d in mesh_simulator_service.get_devices():
        if d.has_internet():
            d.clear()
            
    return {
        "uploadsAttempted": len(uploads),
        "results": results
    }

@router.post("/mesh/reset")
def reset_mesh():
    mesh_simulator_service.reset_mesh()
    idempotency_service.clear()
    return {"status": "mesh and idempotency cache cleared"}

@router.post("/bridge/ingest")
def bridge_ingest(
    packet: MeshPacket, 
    x_bridge_node_id: Optional[str] = Header("unknown", alias="X-Bridge-Node-Id"), 
    x_hop_count: Optional[int] = Header(0, alias="X-Hop-Count"),
    db: Session = Depends(get_db)
):
    return BridgeIngestionService.ingest(db, packet, x_bridge_node_id, x_hop_count)
