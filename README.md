# Northstar Live Inventory Sync Service

## Overview
This service provides real-time inventory visibility for Northstar Retail Co. support agents to check item stock levels accurately.

---

## Current Architecture — Day 3 (Original Spec)

### Approach
* **Polling Model:** The service runs an automated background scheduler (`APScheduler`) that polls the external Warehouse API every 30 seconds.
* **In-Memory Caching:** Stock data fetched from the warehouse is cached locally in memory for instant queries.
* **Query API:** Exposes a fast REST endpoint (`GET /inventory/{item_id}`) for customer support tools.

### Technology Stack
* **Language:** Python 3.x
* **Framework:** FastAPI
* **Server:** Uvicorn
* **HTTP Client:** HTTPX (for async polling)
* **Scheduler:** APScheduler (AsyncIOScheduler)

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Health check endpoint |
| `GET` | `/inventory/{item_id}` | Query cached stock level for a specific item |
| `GET` | `/mock-warehouse/stock` | Simulated external warehouse inventory API |

---

## Scope Delta Analysis (Pending Day 4 Pivot)

> *This section will document architectural changes, dropped features, and trade-offs when the non-negotiable client pivot is announced.*

* **Dropped Features:** TBD (Day 4)
* **Added Features:** TBD (Day 4)
* **Modified Features:** TBD (Day 4)
* **Architectural Trade-offs:** TBD (Day 4)