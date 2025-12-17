# tools/run_dev.py

import uvicorn


def main():
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )


if __name__ == "__main__":
    main()
