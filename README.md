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
10. [Limitations](#limitations)

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

---




























