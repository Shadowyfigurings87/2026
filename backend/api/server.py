from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "rf_archive_online"}
