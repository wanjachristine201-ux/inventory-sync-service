import hmac
import hashlib
import os
import asyncio
from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Solstice Events - Asynchronous Check-In & Webhook Service")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "solstice_secret_key_123")

attendees_db = {
    "ATT-001": {"name": "Alice Johnson", "status": "NOT_CHECKED_IN", "badge_printed": False},
    "ATT-002": {"name": "Bob Smith", "status": "NOT_CHECKED_IN", "badge_printed": False},
    "ATT-003": {"name": "Charlie Brown", "status": "NOT_CHECKED_IN", "badge_printed": False},
}

message_queue = []

class CheckInRequest(BaseModel):
    attendee_id: str

class WebhookPayload(BaseModel):
    attendee_id: str
    status: str


def verify_signature(body_bytes: bytes, x_signature: str | None) -> bool:
    if not x_signature:
        return False
    expected_hash = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        body_bytes,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_hash, x_signature)


async def process_queue_and_send_webhook(attendee_id: str, raw_payload: str):
    """Simulates vendor picking up job from queue and sending back a signed webhook."""
    await asyncio.sleep(3)  # Simulate processing delay
    
    signature = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        raw_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    import httpx
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://127.0.0.1:8000/webhook/print-completed",
            content=raw_payload,
            headers={
                "Content-Type": "application/json",
                "X-Signature": signature
            }
        )


@app.post("/check-in", tags=["Kiosk"])
async def scan_attendee(request: CheckInRequest, background_tasks: BackgroundTasks):
    """
    Handles attendee QR scan.
    Prevents duplicate scans and publishes print job to queue.
    """
    attendee_id = request.attendee_id

    if attendee_id not in attendees_db:
        raise HTTPException(status_code=404, detail="Attendee not found")

    attendee = attendees_db[attendee_id]

    if attendee["status"] in ["PENDING", "CHECKED_IN"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Duplicate scan rejected. Attendee is already in state: {attendee['status']}"
        )

    attendee["status"] = "PENDING"
    
    payload_str = f'{{"attendee_id": "{attendee_id}", "status": "PRINT_COMPLETED"}}'
    message_queue.append({"attendee_id": attendee_id, "payload": payload_str})

    background_tasks.add_task(process_queue_and_send_webhook, attendee_id, payload_str)

    return {
        "message": "Scan accepted. Print job queued.",
        "attendee_id": attendee_id,
        "status": attendee["status"]
    }

@app.post("/webhook/print-completed", tags=["Vendor Webhook"])
async def handle_print_completed_webhook(
    payload: WebhookPayload,
    request: BackgroundTasks, # Used to access request body
    x_signature: str | None = Header(None)
):
    """
    Receives vendor webhook callback, verifies HMAC signature, and completes check-in.
    """

    raw_body = f'{{"attendee_id": "{payload.attendee_id}", "status": "{payload.status}"}}'.encode("utf-8")

    if not verify_signature(raw_body, x_signature):
        raise HTTPException(status_code=401, detail="Invalid or missing webhook signature")

    attendee = attendees_db.get(payload.attendee_id)
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")

    attendee["status"] = "CHECKED_IN"
    attendee["badge_printed"] = True

    return {
        "message": "Webhook processed successfully",
        "attendee_id": payload.attendee_id,
        "current_status": attendee["status"]
    }

@app.get("/attendee/{attendee_id}", tags=["Kiosk UI"])
def get_attendee_status(attendee_id: str):
    """Exposes status for Kiosk UI polling."""
    if attendee_id not in attendees_db:
        raise HTTPException(status_code=404, detail="Attendee not found")
    return {"attendee_id": attendee_id, "data": attendees_db[attendee_id]}


@app.get("/", tags=["Health Check"])
def root():
    return {"status": "Active", "service": "Solstice Events Check-In Service"}