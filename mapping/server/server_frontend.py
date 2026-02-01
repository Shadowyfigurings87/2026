import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

app = FastAPI(title="Mapping Frontend Server")

# Serve the frontend directory
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

def start_frontend_server():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)

if __name__ == "__main__":
    start_frontend_server()
