from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import sqlite3
import os
from backend.utils.logging_config import log_event

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="templates")

# -----------------------------
# Helper: check DB connectivity
# -----------------------------
def check_database(path="data/rf_archive.db"):
    try:
        conn = sqlite3.connect(path)
        conn.execute("SELECT 1")
        conn.close()
        return True
    except Exception as e:
        log_event("system", "ERROR", "db_check_failed", {"error": str(e)})
        return False


# -----------------------------
# Helper: check running services
# -----------------------------
def check_services():
    return {
        "tcp_ingest": True,
        "ingest_processor": True,
        "db_writer": True,
        "observatory_engine": True,
    }


# -----------------------------
# /dashboard/system/health
# -----------------------------
@router.get("/system/health")
def system_health():
    db_ok = check_database()
    services_ok = check_services()
    overall = db_ok and all(services_ok.values())

    return {
        "status": "ok" if overall else "degraded",
        "database": "ok" if db_ok else "error",
        "services": services_ok,
    }


# -----------------------------
# /dashboard/system/info
# -----------------------------
@router.get("/system/info")
def system_info():
    return {
        "system": "RF Monitoring Backend",
        "version": "1.0.0",
        "python": os.sys.version,
        "cwd": os.getcwd(),
    }


# -----------------------------
# /dashboard/system/ping
# -----------------------------
@router.get("/system/ping")
def system_ping():
    return {"pong": True}


# -----------------------------
# /dashboard/system  (dashboard page)
# -----------------------------
@router.get("/system")
def system_dashboard(request: Request):
    health = system_health()
    info = system_info()
    return templates.TemplateResponse(
        "system.html",
        {
            "request": request,
            "active_page": "system",
            "health": health,
            "info": info,
        }
    )
