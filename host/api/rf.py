from fastapi import APIRouter
from host.services.metrics import get_rf_status, get_alfa_status

router = APIRouter()

@router.get("/status")
async def rf_status():
    return get_rf_status()

@router.get("/alfa")
async def alfa_status():
    return get_alfa_status()
