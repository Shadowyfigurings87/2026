# tools/test_ws_all.py

import asyncio
import json
import websockets


WS_URL = "ws://localhost:8080/ws/all"


async def main():
    async with websockets.connect(WS_URL) as ws:
        print(f"Connected to {WS_URL}")
        try:
            while True:
                msg = await ws.recv()
                event = json.loads(msg)
                table = event.get("table")
                data = event.get("data")
                print(f"\n[{table}] --------------------------------")
                print(json.dumps(data, indent=2))
        except KeyboardInterrupt:
            print("Interrupted by user")


if __name__ == "__main__":
    asyncio.run(main())
