import asyncio
import websockets
import banana_dev as banana


async def handle_websocket(websocket, path):
    async for message in websocket:
        print(f"Received message: {message}")
        response = f"You sent: {message}"
        await websocket.send(response)


async def main():
    async with websockets.serve(handle_websocket, "localhost", 8080):
        print("WebSocket server started")
        await asyncio.Future()  # Keep the event loop running


asyncio.run(main())
