from fastapi import FastAPI, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx
from datetime import datetime

app = FastAPI(title="Northstar Live Inventory Sync Service")

inventory_cache = {
    "ITEM-101": {"name": "Wireless Mouse", "stock": 45, "last_updated": "Initial"},
    "ITEM-102": {"name": "Mechanical Keyboard", "stock": 12, "last_updated": "Initial"}
}

scheduler = AsyncIOScheduler()

@app.get("/mock-warehouse/stock", tags=["Mock Warehouse"])
def mock_warehouse_api():
    """Simulates an external warehouse API returning stock levels."""
    return {
        "ITEM-101": {"name": "Wireless Mouse", "stock": 50},
        "ITEM-102": {"name": "Mechanical Keyboard", "stock": 8}
    }

async def poll_warehouse_stock():
    """Polls warehouse API every interval to sync local inventory cache."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8000/mock-warehouse/stock")
            if response.status_code == 200:
                data = response.json()
                for item_id, details in data.items():
                    inventory_cache[item_id] = {
                        "name": details["name"],
                        "stock": details["stock"],
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [POLL] Sync complete. Cache updated.")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [POLL ERROR] Failed: {e}")

@app.on_event("startup")
def start_scheduler():
    
    scheduler.add_job(poll_warehouse_stock, "interval", seconds=30, id="warehouse_poll_job")
    scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()

@app.get("/inventory/{item_id}", tags=["Support Tool API"])
def query_inventory(item_id: str):
    """Allows support tools to query item stock levels."""
    if item_id not in inventory_cache:
        raise HTTPException(status_code=404, detail="Item not found in inventory")
    return {
        "item_id": item_id,
        "data": inventory_cache[item_id]
    }

@app.get("/", tags=["Health Check"])
def root():
    return {"status": "Active", "service": "Live Inventory Sync"}