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

## Scope Delta Analysis ( Day 4 Pivot)

> *This section will document architectural changes, dropped features, and trade-offs when the non-negotiable client pivot is announced.*

# Solstice Events - Live Check-In & Webhook Service

## Overview
This service provides event check-in and badge-printing synchronization for Solstice Events Co. support staff and kiosk displays.

---

## Architecture Evolution

### Day 3 (Original Spec - Polling Model)
* **Approach:** Polled external APIs on a periodic background loop (`APScheduler`) to sync inventory cache locally.
* **Query API:** Provided immediate status responses directly from memory[cite: 1].

### Day 4 (Pivot - Asynchronous Message Queue & Webhook Model)
* **Approach:** Switched to an asynchronous model due to vendor API deprecation.
* **Asynchronous Queue:** Kiosk QR scans push print jobs to a background message queue and set the attendee status to `PENDING`.
* **Webhook Processing:** The vendor processes the print job and sends a callback to `/webhook/print-completed`.
* **HMAC Verification:** Incoming webhook callbacks are verified using `HMAC-SHA256` signatures and a shared secret key.

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Health check endpoint |
| `POST` | `/check-in` | Accepts attendee QR scan and queues badge print job |
| `POST` | `/webhook/print-completed` | Secure callback endpoint for vendor print completion |
| `GET` | `/attendee/{attendee_id}` | Query current attendee check-in and badge status |

---

## Scope Delta Analysis (Pivot Impact)

* **Dropped Features:**
  * Synchronous REST print requests that blocked execution while waiting for printer response.
  * `APScheduler` periodic polling loop[cite: 1].

* **Added Features:**
  * `POST /webhook/print-completed` callback endpoint.
  * `HMAC-SHA256` signature verification middleware (`X-Signature` header validation).
  * Background worker queue simulation using FastAPI `BackgroundTasks`.

* **Modified Features:**
  * Kiosk UI flow now tracks a temporary `PENDING` state rather than expecting immediate `CHECKED_IN` completion.

* **Duplicate Protection Strategy:**
  * State-based locking on `attendees_db`: Any scan attempt for an attendee already in `PENDING` or `CHECKED_IN` state returns an HTTP 400 error immediately, preventing double badge prints even if webhooks arrive out of order.
