# tools/test_ws_frames.py

import asyncio
import json
import websockets


WS_URL = "ws://localhost:8080/ws/frames"


async def main():
    async with websockets.connect(WS_URL) as ws:
        print(f"Connected to {WS_URL}")
        try:
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                print(json.dumps(data, indent=2))
        except KeyboardInterrupt:
            print("Interrupted by user")


if __name__ == "__main__":
    asyncio.run(main())
