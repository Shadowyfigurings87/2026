from fastapi import FastAPI
from pydantic import BaseModel

from Rover1.db.gps_write import write_gps

app = FastAPI()

class GPSData(BaseModel):
    lat: float
    lon: float
    timestamp: float

@app.post("/gps")
def receive_gps(data: GPSData):
    print("🔥 GPS ENDPOINT ACTIVE — calling write_gps()")
    write_gps(data.timestamp, data.lat, data.lon)
    print("🔥 GPS ENDPOINT FINISHED")
    print("Received GPS:", data.dict())
    return {"status": "ok"}

