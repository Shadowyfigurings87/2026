# host/api/server.py

from host.api.router import app

def start_server():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
