from typing import List
from schemas.mesh_packet import MeshPacket

class VirtualDevice:
    def __init__(self, device_id: str, has_internet: bool):
        self.deviceId = device_id
        self.hasInternet = has_internet
        self.held_packets = {}

    def has_internet(self) -> bool:
        return self.hasInternet

    def get_device_id(self) -> str:
        return self.deviceId

    def hold(self, packet: MeshPacket):
        self.held_packets[packet.packetId] = packet

    def holds(self, packet_id: str) -> bool:
        return packet_id in self.held_packets

    def get_held_packets(self) -> List[MeshPacket]:
        return list(self.held_packets.values())

    def packet_count(self) -> int:
        return len(self.held_packets)

    def clear(self):
        self.held_packets.clear()
