import banana_dev as banana
import asyncio
import websockets
import json


async def handle_youtube(message):
    # Process the YouTube message here
    print(f"Processing YouTube message: {message}")


async def handle_websocket(websocket, path):
    async for message in websocket:
        print(f"Received message: {message}")
        try:
            data = json.loads(message)
            if data.get("type") == "youtube":
                await handle_youtube(data)
            else:
                response = f"You sent: {message}"
                await websocket.send(response)
        except json.JSONDecodeError:
            print("Invalid JSON received")
            await websocket.send("Invalid JSON format")


async def main():
    async with websockets.serve(handle_websocket, "0.0.0.0", 8080):
        print("WebSocket server started")
        await asyncio.Future()  # Keep the event loop running


asyncio.run(main())
