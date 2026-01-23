# host/api_server.py

import uvicorn
from host.api.router import app

def start_api_server():
    print("[Host] Starting FastAPI server on port 8000…")
    uvicorn.run(app, host="0.0.0.0", port=8000)
