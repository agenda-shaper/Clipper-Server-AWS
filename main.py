import banana_dev as banana
import asyncio
import websockets
import json


async def handle_banana_dev(model_inputs):
    api_key = "c9a5be2f-b57b-4419-8599-d89f4b24bfa3"

    model_key_medium = "4a4f2fe0-017a-46bf-b8dc-5c1c6b8458a9"

    # Run the model
    response = banana.run(api_key, model_key_medium, model_inputs)

    # Convert the dictionary to a JSON-formatted string
    result_json = json.dumps(response)

    return result_json


async def handle_websocket(websocket, path):
    async for message in websocket:
        print(f"Received message: {message}")
        try:
            data = json.loads(message)
            result_json = await handle_banana_dev(data)
            await websocket.send(result_json)
        except json.JSONDecodeError:
            print("Invalid JSON received")
            await websocket.send("Invalid JSON format")


async def main():
    async with websockets.serve(handle_websocket, "0.0.0.0", 8080):
        print("WebSocket server started")
        await asyncio.Future()  # Keep the event loop running


asyncio.run(main())
