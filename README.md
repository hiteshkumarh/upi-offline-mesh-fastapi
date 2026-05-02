# UPI Offline Mesh — FastAPI Demo

A FastAPI backend that demonstrates **offline UPI payments routed through a mesh network simulation**.

Imagine being in a location with zero internet connectivity. You send your friend ₹500. Your device encrypts the payment and broadcasts it to nearby devices. The transaction propagates hop-by-hop across a mesh network until a device regains internet access and uploads it to the backend. The backend then securely decrypts, validates, deduplicates, and settles the transaction.

This repository contains the **Python FastAPI backend** along with a **software-based mesh simulator**, allowing the complete offline payment flow to be demonstrated on a single system without requiring real Bluetooth hardware.
