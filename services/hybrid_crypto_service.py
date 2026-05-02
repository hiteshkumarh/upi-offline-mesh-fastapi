import json
import base64
import os
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from schemas.payment_instruction import PaymentInstruction
from services.server_key_holder import server_key_holder

RSA_ENCRYPTED_KEY_BYTES = 256
GCM_IV_BYTES = 12
GCM_TAG_BYTES = 16

class HybridCryptoService:
    @staticmethod
    def encrypt(instruction: PaymentInstruction) -> str:
        plaintext = json.dumps(instruction.model_dump()).encode('utf-8')

        # 1. Generate AES key
        aes_key = os.urandom(32) # 256 bits

        # 2. AES-GCM encrypt
        iv = os.urandom(GCM_IV_BYTES)
        encryptor = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(iv),
            backend=default_backend()
        ).encryptor()
        
        aes_ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        tag = encryptor.tag

        # 3. RSA-OAEP encrypt AES key
        encrypted_aes_key = server_key_holder.public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # 4. Pack: [encrypted AES key 256][IV 12][AES ciphertext + tag 16]
        packed = encrypted_aes_key + iv + aes_ciphertext + tag
        return base64.b64encode(packed).decode('utf-8')

    @staticmethod
    def decrypt(base64_ciphertext: str) -> PaymentInstruction:
        raw_data = base64.b64decode(base64_ciphertext)
        
        min_length = RSA_ENCRYPTED_KEY_BYTES + GCM_IV_BYTES + GCM_TAG_BYTES
        if len(raw_data) < min_length:
            raise ValueError("Ciphertext too short")

        encrypted_aes_key = raw_data[:RSA_ENCRYPTED_KEY_BYTES]
        iv = raw_data[RSA_ENCRYPTED_KEY_BYTES:RSA_ENCRYPTED_KEY_BYTES + GCM_IV_BYTES]
        aes_ciphertext_with_tag = raw_data[RSA_ENCRYPTED_KEY_BYTES + GCM_IV_BYTES:]
        
        tag = aes_ciphertext_with_tag[-GCM_TAG_BYTES:]
        aes_ciphertext = aes_ciphertext_with_tag[:-GCM_TAG_BYTES]

        # 1. RSA-decrypt the AES key
        aes_key = server_key_holder.private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # 2. AES-GCM decrypt + verify tag
        decryptor = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(iv, tag),
            backend=default_backend()
        ).decryptor()
        
        plaintext = decryptor.update(aes_ciphertext) + decryptor.finalize()
        data = json.loads(plaintext.decode('utf-8'))
        return PaymentInstruction(**data)

    @staticmethod
    def hash_ciphertext(base64_ciphertext: str) -> str:
        digest = hashlib.sha256(base64_ciphertext.encode('utf-8')).hexdigest()
        return digest
