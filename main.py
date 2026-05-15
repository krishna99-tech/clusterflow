from fastapi import FastAPI, WebSocket
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from datetime import datetime
import socket
import uvicorn

# =====================================================
# FastAPI App
# =====================================================

app = FastAPI()

hostname = socket.gethostname()

# =====================================================
# MongoDB Connection
# =====================================================

MONGO_URL = "mongodb://192.168.0.179:27017"

mongo_client = AsyncIOMotorClient(MONGO_URL)

db = mongo_client["ems"]

meter_collection = db["meters"]

# =====================================================
# Schema
# =====================================================

class MeterData(BaseModel):

    meter_id: str
    plant: str
    voltage: float
    current: float
    power: float
    frequency: float
    power_factor: float
    timestamp: datetime

# =====================================================
# Home Route
# =====================================================

@app.get("/")
async def home():

    return {
        "server": hostname,
        "message": "EMS Backend Running"
    }

# =====================================================
# Insert Meter Data
# =====================================================

@app.post("/meters")
async def add_meter(data: MeterData):

    meter_data = data.dict()

    await meter_collection.insert_one(meter_data)

    return {
        "status": "saved",
        "meter_id": data.meter_id,
        "server": hostname
    }

# =====================================================
# Get All Data
# =====================================================

@app.get("/meters")
async def get_meters():

    data = []

    async for meter in meter_collection.find({}, {"_id": 0}):

        data.append(meter)

    return data

# =====================================================
# Get Data By Meter ID
# =====================================================

@app.get("/meters/{meter_id}")
async def get_meter(meter_id: str):

    data = []

    async for meter in meter_collection.find(
        {"meter_id": meter_id},
        {"_id": 0}
    ):

        data.append(meter)

    return data

# =====================================================
# Latest Meter Data
# =====================================================

@app.get("/latest/{meter_id}")
async def latest_meter(meter_id: str):

    data = await meter_collection.find_one(
        {"meter_id": meter_id},
        sort=[("timestamp", -1)],
        projection={"_id": 0}
    )

    return data

# =====================================================
# WebSocket
# =====================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    while True:

        latest = await meter_collection.find_one(
            sort=[("timestamp", -1)],
            projection={"_id": 0}
        )

        await websocket.send_json({
            "server": hostname,
            "latest_data": latest
        })

# =====================================================
# Run Server
# =====================================================

if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )