# UPI Offline Mesh — FastAPI Demo

A FastAPI backend that demonstrates **offline UPI payments routed through a mesh network simulation**.

Imagine being in a location with zero internet connectivity. You send your friend ₹500. Your device encrypts the payment and broadcasts it to nearby devices. The transaction propagates hop-by-hop across a mesh network until a device regains internet access and uploads it to the backend. The backend then securely decrypts, validates, deduplicates, and settles the transaction.

This repository contains the **Python FastAPI backend** along with a **software-based mesh simulator**, allowing the complete offline payment flow to be demonstrated on a single system without requiring real Bluetooth hardware.

---

## Table of Contents

1. [What this demo proves](#what-this-demo-proves)
2. [How to run it](#how-to-run-it)
3. [Demo flow (step-by-step)](#demo-flow-step-by-step)
4. [System architecture](#system-architecture)
5. [Core challenges and solutions](#core-challenges-and-solutions)
6. [Project structure](#project-structure)
7. [API reference](#api-reference)
8. [Testing](#testing)
9. [Production considerations](#production-considerations)
10. [Limitations of the approach](#limitations)

---
---

## What this demo proves

This system demonstrates three key backend and distributed system concepts working end-to-end:

1. **Secure transaction propagation through untrusted intermediaries**  
   A payment can travel from sender to backend across multiple devices without any intermediate node being able to read or modify the data, using hybrid encryption (RSA-OAEP + AES-256-GCM).

2. **Exactly-once transaction processing under concurrency**  
   Even if the same payment is delivered multiple times by different bridge nodes, it is processed only once using idempotency based on SHA-256 hashing and atomic claim logic.

3. **Protection against tampering and replay attacks**  
   Any modified or replayed packet is detected and rejected before it reaches the settlement layer, ensuring data integrity and system reliability.

All of these behaviors can be observed in real time through the dashboard interface.

---
## How to run it

### Prerequisites

* **Python 3.9 or newer** installed
  Check with:

  ```bash
  python --version
  ```
* No external database or Redis required (uses SQLite)

---

### Setup

Clone the repository and navigate to the project folder:

```bash id="a1s9kp"
git clone <your-repo-url>
cd upi-offline-mesh-fastapi
```

Create and activate a virtual environment:

**Windows:**

```bash id="x4k2zn"
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**

```bash id="h8p3dl"
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash id="r7v2qy"
pip install -r requirements.txt
```

---

### Run the server

```bash id="q2m8df"
uvicorn main:app --reload
```

You should see:

```text id="p9w4lc"
Uvicorn running on http://127.0.0.1:8000
```

---

### Open the dashboard

Once the server is running, open:

**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

You’ll see the interactive dashboard to run the demo.

---

### Stop the server

Press:

```bash id="k6t1rv"
Ctrl + C
```

---

### Reset the database (optional)

If you want a fresh start:

```bash id="m3z8qy"
del upimesh.db   # Windows
rm upimesh.db    # Mac/Linux
```

Then restart the server.

Testing the system

Use the dashboard to simulate the flow:

Inject a payment
Run gossip rounds
Flush to backend

Verify:

Balance updates correctly
Transaction appears in ledger
Duplicate packets are ignored (idempotency)
Notes
Uses SQLite (local database file)
No additional setup required
First run may take a few seconds to install dependencies


---
## Demo flow 

The dashboard provides controls to simulate the complete offline payment pipeline.

---

### Step 1 — Compose a payment

Select sender, receiver, amount, and PIN. Click **“📤 Inject into Mesh”**.

**What happens on the backend:**

* The system simulates the sender’s device.
* A `PaymentInstruction` is created with a unique nonce and timestamp.
* The payload is encrypted using hybrid encryption (**RSA-OAEP + AES-256-GCM**).
* The encrypted payload is wrapped into a `MeshPacket` with a TTL (time-to-live).
* The packet is injected into a virtual device (e.g., `phone-alice`).

👉 You’ll see the device now holding the packet.

---

### Step 2 — Run gossip rounds

Click **“🔄 Run Gossip Round”** (one or more times).

**What happens:**

* Each device holding the packet broadcasts it to nearby devices.
* In this simulation, all devices are considered within range.
* TTL decreases with each hop.

After a few rounds:

* The packet spreads across all devices
* TTL reduces progressively

👉 This simulates real-world device-to-device propagation without internet.

---

### Step 3 — Bridge node syncs with backend

Click **“📡 Bridges Upload to Backend”**.

**What happens:**

* Devices marked as bridge nodes (with internet access) send packets to:

  ```id="g0p9c1"
  POST /api/bridge/ingest
  ```

* The backend processes each packet using the following pipeline:

1. Compute SHA-256 hash of the ciphertext
2. Attempt to claim the hash (idempotency check)
3. If first claim → decrypt payload
4. Validate freshness (timestamp within allowed window)
5. Execute debit/credit using a database transaction

👉 Result:

* Account balances update
* A new entry appears in the transaction ledger

---

### Step 4 — Demonstrate idempotency (key feature)

Reset the system and repeat:

1. Inject a single payment
2. Run gossip rounds multiple times
3. Upload via bridge

Now multiple devices may hold the **same packet**.

**What happens:**

* Multiple identical requests reach the backend
* Only the first request is processed
* Remaining requests are safely ignored

👉 This ensures **exactly-once transaction processing**, even under concurrency.

---

### Testing idempotency manually

To observe duplicate handling:

* Inject once
* Gossip multiple times
* Trigger upload multiple times quickly

👉 Only one transaction is settled; duplicates are dropped.

---

## 💡 Summary

This flow demonstrates:

* Offline transaction creation
* Mesh-based packet propagation
* Secure encrypted data transfer
* Idempotent backend processing
* Atomic financial settlement

---

## System Architecture

┌─────────────────────────────────────────────────────────────────────────┐
│                         SENDER DEVICE (offline)                         |
│  PaymentInstruction { sender, receiver, amount, pinHash, nonce, time }  │
│              │                                                          │
│              ▼ encrypt with server's RSA public key                     │
│   MeshPacket { packetId, ttl, createdAt, ciphertext }                   │
└──────────────────────────────────────┬──────────────────────────────────┘
                                       │ Mesh gossip (device-to-device)
                                       ▼
        ┌─────────┐  hop   ┌─────────┐  hop   ┌─────────┐
        │ device1 │ ─────▶ │ device2 │ ─────▶ │ bridge  │ ◀── regains internet
        └─────────┘        └─────────┘        └────┬────┘
                                                   │
                                                   ▼ HTTPS POST
┌─────────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND (this project)                     │
│                                                                         │
│  POST /api/bridge/ingest                                                │
│       │                                                                 │
│       ▼                                                                 │
│  [1] Hash ciphertext (SHA-256)                                          │
│       │                                                                 │
│       ▼                                                                 │
│  [2] IdempotencyService.claim(hash)                                     │
│       │   (thread-safe atomic check; duplicates rejected early)         │
│       ▼                                                                 │
│  [3] HybridCryptoService.decrypt(ciphertext)                            │
│       │   (RSA-OAEP unwraps AES key, AES-GCM decrypts payload           │
│       │    and verifies integrity via authentication tag)               │
│       ▼                                                                 │
│  [4] Freshness validation (timestamp within allowed window)             │
│       │                                                                 │
│       ▼                                                                 │
│  [5] SettlementService.settle()                                         │
│       │   (atomic DB transaction: debit sender, credit receiver,        │
│       │    write transaction ledger)                                    │
└─────────────────────────────────────────────────────────────────────────┘


## Core challenges and how they’re solved

### Problem 1: Untrusted intermediaries

In a mesh network, transactions pass through multiple unknown devices. How do we ensure that intermediate devices cannot read or tamper with the payment data?

**Solution: Hybrid encryption (RSA-OAEP + AES-256-GCM).**

The sender encrypts the payload using the backend’s public key. Only the backend holds the private key, so all intermediate devices see only encrypted data.

Since RSA is inefficient for large payloads, a hybrid encryption approach is used:

1. Generate a random AES-256 key for each packet
2. Encrypt the JSON payload using **AES-256-GCM** (fast and authenticated)
3. Encrypt the AES key using **RSA-OAEP**
4. Combine components into a single ciphertext:

   ```
   [RSA-encrypted AES key][IV][AES ciphertext + authentication tag]
   ```

**Why AES-GCM?**
AES-GCM provides authenticated encryption. Any modification to the ciphertext results in authentication failure during decryption, ensuring data integrity and preventing tampering.

---

### Problem 2: Duplicate transaction processing

Multiple bridge nodes may upload the same packet simultaneously. Without safeguards, this could result in multiple settlements for a single transaction.

**Solution: Idempotency using SHA-256 hashing and atomic claim.**

Each incoming packet is processed as follows:

1. Compute `SHA-256(ciphertext)` as a unique identifier
2. Attempt to claim the hash in a thread-safe store
3. Only the first successful claim proceeds to processing
4. Subsequent duplicates are rejected

Example logic:

```python id="d9k2lm"
def claim(packet_hash):
    with lock:
        if packet_hash in store:
            return False
        store[packet_hash] = current_time
        return True
```

**Why hash the ciphertext?**

* `packetId` can be altered by intermediaries
* Decrypting first is expensive
* Ciphertext integrity is protected by AES-GCM

Additionally, a **unique constraint on `packet_hash`** in the database acts as a fallback to prevent duplicate settlements.

---

### Problem 3: Replay attacks

An attacker could capture a valid packet and replay it later to trigger repeated settlements.

**Solution: Timestamp validation + nonce.**

Two layers of protection are used:

1. **Timestamp validation**

   * Each payload includes `signedAt`
   * Backend rejects packets older than a defined time window

2. **Nonce-based uniqueness**

   * Each transaction includes a unique `nonce` (UUID)
   * Even identical payments generate different ciphertexts

If an old packet is replayed:

* It fails freshness validation
* Or is rejected by idempotency checks

---

## Project Structure

upi-offline-mesh-fastapi/
├── db/
│   └── database.py                # Database setup (SQLite + SQLAlchemy)
├── models/
│   ├── account.py                # Account model (balances, versioning)
│   └── transaction.py            # Transaction ledger model
├── routers/
│   ├── api_controller.py         # REST API endpoints
│   └── dashboard_controller.py   # Serves dashboard UI
├── schemas/
│   ├── mesh_packet.py            # Packet structure (encrypted payload)
│   └── payment_instruction.py    # Decrypted transaction payload
├── services/
│   ├── bridge_ingestion_service.py   # Core pipeline: hash → claim → decrypt → settle
│   ├── demo_service.py               # Seeds data + simulates sender device
│   ├── hybrid_crypto_service.py     # RSA + AES-GCM encryption/decryption
│   ├── idempotency_service.py       # Duplicate detection (thread-safe)
│   ├── mesh_simulator_service.py    # Simulates device-to-device gossip
│   ├── server_key_holder.py         # RSA keypair management
│   ├── settlement_service.py        # Atomic debit/credit transactions
│   └── virtual_device.py            # Simulated mesh device
├── templates/
│   └── dashboard.html              # Frontend UI for demo
├── main.py                         # FastAPI application entry point
├── requirements.txt                # Python dependencies
├── .gitignore
└── README.md

---

## API Reference

| Method | Path                 | Description                                  |
| ------ | -------------------- | -------------------------------------------- |
| GET    | `/`                  | Dashboard HTML                               |
| GET    | `/api/server-key`    | Server RSA public key (base64)               |
| GET    | `/api/accounts`      | List all accounts and balances               |
| GET    | `/api/transactions`  | Last 20 transactions                         |
| GET    | `/api/mesh/state`    | Current state of virtual devices             |
| POST   | `/api/demo/send`     | Simulate sender: encrypt + inject packet     |
| POST   | `/api/mesh/gossip`   | Run one gossip round across the mesh         |
| POST   | `/api/mesh/flush`    | Bridge nodes upload packets to backend       |
| POST   | `/api/mesh/reset`    | Reset mesh + idempotency cache               |
| POST   | `/api/bridge/ingest` | **Production endpoint** for packet ingestion |

---

### Notes

* Backend is built with **FastAPI**
* Uses **SQLite (`upimesh.db`)** for persistence
* No external services (e.g., Redis) required
* Idempotency handled in-memory with DB fallback (unique `packet_hash`)

---

### Request format for `/api/bridge/ingest`

```http
POST /api/bridge/ingest
Content-Type: application/json
X-Bridge-Node-Id: phone-bridge-42
X-Hop-Count: 3

{
  "packetId": "550e8400-e29b-41d4-a716-446655440000",
  "ttl": 2,
  "createdAt": 1730000000000,
  "ciphertext": "base64-encoded-RSA-and-AES-blob"
}
```

---

### Response

```json id="zv7u9k"
{
  "outcome": "SETTLED",           
  "packetHash": "a3f8c9...",
  "reason": null,                 
  "transactionId": 42             
}
```

---

### Response fields

* `outcome` → `"SETTLED" | "DUPLICATE_DROPPED" | "INVALID"`
* `packetHash` → SHA-256 hash of ciphertext
* `reason` → error message (only for `INVALID`)
* `transactionId` → present only when `SETTLED`

---

## Tests

### Running tests

If test cases are implemented (e.g., using `pytest`), run:

```bash
pytest
```

If automated tests are not included, the system can be validated using the dashboard.

---

### Key test scenarios

* **`encrypt_decrypt_round_trip`**
  Validates that the hybrid encryption pipeline works correctly by encrypting and then decrypting a payload, ensuring data integrity.

* **`tampered_ciphertext_is_rejected`**
  Simulates a corrupted packet by modifying the ciphertext. The backend should detect tampering during AES-GCM verification and return `INVALID` instead of processing it.

* **`idempotent_processing_under_concurrency`**
  Simulates multiple concurrent requests delivering the same packet. Verifies that:

  * Exactly one request is processed (`SETTLED`)
  * Remaining requests are rejected (`DUPLICATE_DROPPED`)
  * Account balance updates occur only once

---

### Manual validation (via dashboard)

You can also test the system interactively:

1. Inject a payment
2. Run multiple gossip rounds
3. Trigger bridge upload multiple times

Verify:

* Only one transaction is settled
* Duplicate packets are ignored
* Account balances update correctly

---

## 💡 Notes

* Cryptographic validation ensures tampered data is rejected
* Idempotency guarantees exactly-once processing
* SQLite constraints act as a fallback for duplicate prevention

---


---

## Production considerations

This project is designed as a demonstration system. To make it production-ready, the following components would need to be upgraded:

| Demo Implementation                             | Production-Grade Alternative                                    |
| ----------------------------------------------- | --------------------------------------------------------------- |
| SQLite (`upimesh.db`)                           | PostgreSQL / MySQL with replication                             |
| In-memory idempotency store (dictionary + lock) | Redis with `SET NX EX` for distributed atomicity                |
| RSA keypair generated at startup                | Secure key management (AWS KMS, HashiCorp Vault, HSM)           |
| Backend-driven packet creation (`demo_service`) | Client-side implementation (mobile app – Android/iOS)           |
| Software-based mesh simulation                  | Real device communication (Bluetooth Low Energy / Wi-Fi Direct) |
| Local settlement service                        | Integration with banking systems / payment networks             |
| No authentication on `/api/bridge/ingest`       | Mutual TLS or signed device certificates                        |
| Pre-seeded accounts                             | Real users with KYC, authentication, and PIN validation         |
| No rate limiting                                | Request throttling and fraud detection mechanisms               |
| Console logging                                 | Structured logging, monitoring, and alerting systems            |

---

## 💡 Key insight

The **core system design remains valid**:

* Hybrid encryption ensures secure data transfer
* Idempotency guarantees exactly-once processing
* Transactional settlement ensures consistency

What changes in production is the **infrastructure, security, and scalability layers** around the system.

---


## Limitations of the approach

This project is designed as a conceptual demonstration. The following limitations are inherent to offline, mesh-based payment systems and are not implementation bugs:

---

### 1. No real-time balance verification

The receiver cannot verify whether the sender has sufficient funds at the time of transaction creation.

* The payment is effectively a **deferred settlement request**, not a confirmed transfer
* If the sender’s account lacks funds when the packet reaches the backend, the transaction is **rejected**
* This can result in failed payments after the fact

👉 Real-world systems (e.g., offline wallets) solve this using **pre-funded, hardware-secured balances**

---

### 2. Possibility of double spending

A malicious sender can create multiple transactions offline using the same funds.

* Example: sending ₹500 to multiple recipients before any packet reaches the backend
* Only the first transaction processed will succeed; others will be rejected

👉 This is a direct consequence of **lack of online balance synchronization**

---

### 3. Real-world device communication challenges

The project uses a simulated mesh network. In reality:

* Bluetooth Low Energy (BLE) communication is constrained by OS-level restrictions
* Background device discovery and connection reliability are limited
* Cross-platform communication (Android/iOS) introduces additional complexity

👉 Implementing a reliable real-world mesh network is significantly more challenging

---

### 4. Privacy and metadata exposure

While transaction data is encrypted:

* Devices still carry **encrypted packets**, which may expose metadata
* The presence and movement of packets could raise privacy concerns
* Real deployments would require careful consideration of **data handling and regulatory compliance**

---

---

## Troubleshooting

**`python: command not found`**
Install Python 3.9 or newer.

* Windows: `winget install Python.Python.3`
* Or download from [https://www.python.org/downloads/](https://www.python.org/downloads/)
  Verify:

```bash
python --version
```

---

**`uvicorn: command not found`**
Make sure dependencies are installed and your virtual environment is active:

```bash
pip install -r requirements.txt
```

---

**Port 8000 already in use**
Run the server on a different port:

```bash
uvicorn main:app --reload --port 8001
```

---

**Dashboard not loading**
Ensure the server is running and open:

```
http://127.0.0.1:8000
```

---

**Database locked / cannot delete `upimesh.db`**
Stop the server before deleting:

```bash
Ctrl + C
```

Then:

```bash
del upimesh.db   # Windows
rm upimesh.db    # Mac/Linux
```

---

**Changes not reflecting**
Make sure you are running with reload enabled:

```bash
uvicorn main:app --reload
```

---

**Transactions showing incorrect or old data**
Reset the database:

```bash
del upimesh.db   # Windows
rm upimesh.db    # Mac/Linux
```

Restart the server.

---
.























