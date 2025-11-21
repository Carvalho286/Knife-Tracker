from fastapi import FastAPI, HTTPException
from knife_tracker_backend.models import RegisterDevice, UpdateFilters, UpdateNotifications
from knife_tracker_backend.database import tokens_collection, assets_collection, create_indexes
from knife_tracker_backend.pirateswap import fetch_items_PirateSwap
from knife_tracker_backend.tradeit import fetch_items_TradeIt
from contextlib import asynccontextmanager
from fastapi import Query

KNIFE_TYPES_PirateSwap = [
    "m9Bayonet","gut","bayonet","bowie","falchion","butterfly","flip",
    "huntsman","karambit","shadowDaggers","navaja","stiletto","talon",
    "classic","ursus","skeleton","nomad","paracord","survival"
]

KNIFE_TYPES_TradeIt = [
    "M9","gut","bayonet","bowie","falchion","butterfly","flip",
    "huntsman","karambit","shadow","navaja","stiletto","talon",
    "classic","ursus","skeleton","nomad","paracord","survival"
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await create_indexes()
    yield
    # shutdown (no-op for now)


app = FastAPI(lifespan=lifespan)

# ================================
#  Register a device
# ================================
@app.post("/register-device")
async def register_device(data: RegisterDevice):
    existing = await tokens_collection.find_one({"_id": data.deviceId})

    if existing:
        await tokens_collection.update_one(
            {"_id": data.deviceId},
            {"$set": {"apnsToken": data.pushToken}}
        )
        return {"status": "updated"}

    await tokens_collection.insert_one({
        "_id": data.deviceId,
        "apnsToken": data.pushToken,
        "notificationsEnabled": True,
        "filters": {
            "categories": ["butterfly"],
            "minPrice": None,
            "maxPrice": None
        }
    })

    return {"status": "new"}


# ================================
#  Update filters
# ================================
@app.post("/update-filters")
async def update_filters(data: UpdateFilters, deviceId: str):
    result = await tokens_collection.update_one(
        {"_id": deviceId},
        {"$set": {"filters": data.dict()}}
    )

    if result.matched_count == 0:
        raise HTTPException(404, "deviceId não encontrado")

    return {"status": "ok"}


# ================================
# List knife types
# ================================
@app.get("/knife-types-pirateswap")
async def get_knife_types_pirate_swap():
    return {"types": KNIFE_TYPES_PirateSwap}

@app.get("/knife-types-tradeit")
async def get_knife_types_tradeit():
    return {"types": KNIFE_TYPES_TradeIt}


# ================================
# Get items from pirateSwap
# ================================
@app.get("/items-pirateswap")
async def get_items(subcategory: list[str] = Query(...)):
    items = await fetch_items_PirateSwap(subcategory)
    return {"items": items}


# ================================
# Get items from tradeIt
# ================================
@app.get("/items-tradeit")
async def get_items(subcategory: str = Query(...)):
    items = await fetch_items_TradeIt([subcategory])
    return {"items": items}

# ================================
# Update Notifications Status
# ================================
@app.post("/update-notifications")
async def update_notifications(data: UpdateNotifications, deviceId: str):
    result = await tokens_collection.update_one(
        {"_id": deviceId},
        {"$set": {"notificationsEnabled": data.enabled}}
    )

    if result.matched_count == 0:
        raise HTTPException(404, "deviceId não encontrado")

    return {"status": "ok"}

# ================================
#  Get device data
# ================================
@app.get("/device/{deviceId}")
async def get_device(deviceId: str):
    device = await tokens_collection.find_one({"_id": deviceId})

    if not device:
        raise HTTPException(404, "deviceId não encontrado")

    # converter o _id para deviceId no output
    device["deviceId"] = device["_id"]
    del device["_id"]

    return device

# ================================
# DEBUG: Force push notification
# ================================
@app.post("/debug/send-test")
async def debug_send_test(deviceId: str):
    dev = await tokens_collection.find_one({"_id": deviceId})
    
    if not dev:
        raise HTTPException(404, "deviceId não encontrado")

    apnsToken = dev.get("apnsToken")
    if not apnsToken:
        raise HTTPException(400, "Este device não tem APNs token registado")

    from knife_tracker_backend.apns import send_apns_push
    await send_apns_push(
        apnsToken,
        title="Test Notification",
        body="If you see this, APNs is working!"
    )

    return {"status": "notification_sent"}


