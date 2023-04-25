import banana_dev as banana
import asyncio
import websockets
import json


async def handle_youtube_whisper(message):
    # Process the YouTube message here
    print(f"Processing YouTube message: {message}")
    model_inputs = {
        "url": message["url"],
        "start_time": message["start_time"],
        "end_time": message["end_time"],
        "kwargs": {"beam_size": 5, "temperature": [0, 0.2, 0.4, 0.6, 0.8, 1]},
    }
    print(model_inputs)

    api_key = "c9a5be2f-b57b-4419-8599-d89f4b24bfa3"

    model_key_medium = "4a4f2fe0-017a-46bf-b8dc-5c1c6b8458a9"

    # Run the model
    response = banana.run(api_key, model_key_medium, model_inputs)

    # Convert the JSON response to a Python dictionary
    result_dict = json.loads(response.text)

    # Convert the dictionary to a JSON-formatted string
    result_json = json.dumps(result_dict)

    return result_json


async def handle_websocket(websocket, path):
    async for message in websocket:
        print(f"Received message: {message}")
        try:
            data = json.loads(message)
            if data["type"] == "youtube_transcribe":
                result_json = await handle_youtube_whisper(data)
                await websocket.send(result_json)
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
