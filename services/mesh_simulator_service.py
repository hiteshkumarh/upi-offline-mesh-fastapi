from typing import List, Dict
from services.virtual_device import VirtualDevice
from schemas.mesh_packet import MeshPacket
import logging

logger = logging.getLogger(__name__)

class MeshSimulatorService:
    def __init__(self):
        self.devices = {}
        self.seed_default_devices()

    def seed_default_devices(self):
        self.devices["phone-alice"] = VirtualDevice("phone-alice", False)
        self.devices["phone-stranger1"] = VirtualDevice("phone-stranger1", False)
        self.devices["phone-stranger2"] = VirtualDevice("phone-stranger2", False)
        self.devices["phone-stranger3"] = VirtualDevice("phone-stranger3", False)
        self.devices["phone-bridge"] = VirtualDevice("phone-bridge", True)

    def get_devices(self) -> List[VirtualDevice]:
        return list(self.devices.values())

    def get_device(self, device_id: str) -> VirtualDevice:
        return self.devices.get(device_id)

    def inject(self, sender_device_id: str, packet: MeshPacket):
        sender = self.get_device(sender_device_id)
        if not sender:
            raise ValueError(f"Unknown device: {sender_device_id}")
        sender.hold(packet)
        logger.info(f"Packet {packet.packetId[:8]} injected at {sender_device_id} (TTL={packet.ttl})")

    def gossip_once(self) -> dict:
        transfers = 0
        device_list = self.get_devices()
        
        # Snapshot what each device holds
        snapshot = {}
        for d in device_list:
            snapshot[d.get_device_id()] = [p for p in d.get_held_packets()]
            
        for src in device_list:
            for pkt in snapshot[src.get_device_id()]:
                if pkt.ttl <= 0:
                    continue
                for dst in device_list:
                    if dst == src:
                        continue
                    if dst.holds(pkt.packetId):
                        continue
                    copy_pkt = MeshPacket(
                        packetId=pkt.packetId,
                        ttl=pkt.ttl - 1,
                        createdAt=pkt.createdAt,
                        ciphertext=pkt.ciphertext
                    )
                    dst.hold(copy_pkt)
                    transfers += 1
        
        logger.info(f"Gossip round complete: {transfers} packet transfers")
        return {"transfers": transfers, "deviceCounts": self.snapshot_map()}

    def snapshot_map(self) -> Dict[str, int]:
        return {d.get_device_id(): d.packet_count() for d in self.get_devices()}

    def collect_bridge_uploads(self) -> List[dict]:
        out = []
        for d in self.get_devices():
            if not d.has_internet():
                continue
            for pkt in d.get_held_packets():
                out.append({"bridgeNodeId": d.get_device_id(), "packet": pkt})
        return out

    def reset_mesh(self):
        for d in self.get_devices():
            d.clear()

mesh_simulator_service = MeshSimulatorService()
