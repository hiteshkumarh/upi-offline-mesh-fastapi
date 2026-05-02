# UPI Offline Mesh (Python FastAPI)

## Description

A distributed offline payment system using Bluetooth mesh simulation and secure cryptography.

## Features

* Offline payment simulation
* RSA + AES encryption
* Idempotent transaction handling
* Mesh network packet propagation
* SQLite transactional backend
* FastAPI REST APIs

## Tech Stack

* Python (FastAPI)
* SQLAlchemy
* SQLite
* Cryptography

## How to Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:
http://127.0.0.1:8000

## Demo Flow

1. Inject payment
2. Gossip packets
3. Flush to backend
