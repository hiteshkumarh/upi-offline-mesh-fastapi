from pydantic import BaseModel, Field

class MeshPacket(BaseModel):
    packetId: str
    ttl: int = Field(ge=0)
    createdAt: int
    ciphertext: str
