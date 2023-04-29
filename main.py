import banana_dev as banana
import asyncio
import re
import websockets
import json
import whisperx
import datetime
from whisperx.utils import write_srt
from whisperx.utils import write_ass


async def generateSubFiles():

async def generateClips(subtitle_srt_file, clip_length, clipping_start):

    subtitle_srt_file, clip_length, clipping_start = data["subtitles_raw"]

    # Open the SRT file and read its contents
    with open(subtitle_srt_file, "r") as f:
        lines = f.readlines()

    # Initialize variables
    clip_start_time = None
    clip_start_times = []
    clip_end_times = []
    wave = 0

    epoch_time = datetime.datetime.strptime("0", "%f")

    # Iterate over each line in the SRT file
    for index, line in enumerate(lines):
        if " --> " not in line:
            continue

        # Strip any leading/trailing whitespace characters from the line
        line = line.strip()

        good_phrases = [
            r"why",
            r"how",
            r"when",
            r"where",
            r"who",
            r"is it",
            r"does it",
            r"are there",
            r"is there",
            r"what",
            r"would",
            r"can i",
            r"i believe",
            r"however",
            r"i think",
        ]
        phrase = lines[index + 1]
        pattern = "|".join(good_phrases)
        matchGood = re.search(pattern, phrase.lower())

        if clip_start_time is not None:
            elapsed_time = (
                datetime.datetime.strptime(line[-12:], "%H:%M:%S,%f") - clip_start_time
            ).total_seconds()
            if elapsed_time >= clip_length or index + 4 > len(lines):
                clip_end_time = (
                    datetime.datetime.strptime(line[-12:], "%H:%M:%S,%f") - epoch_time
                ).total_seconds()
                clip_end_times.append(clip_end_time)
                clip_start_time = None
            # Check if the line contains a question mark
        elif index + 1 <= len(lines) and ("?" in phrase or matchGood):
            slang_phrases = [
                r", you know\?",
                r", huh\?",
                r", right\?",
                r"though\?",
                r", really\?",
                r"who cares",
                r"you know what i\'m trying to say\?",
                r"you know what i mean\?",
                r"you know what i\'m saying\?",
            ]
            pattern = "|".join(slang_phrases)
            match = re.search(pattern, phrase.lower())

            # filter slag question marks and short ones
            if match or len(lines[index + 1]) < 10:
                continue
            # If so, extract the start time of the previous line and subtract one second from it
            start_time = datetime.datetime.strptime(line[:12], "%H:%M:%S,%f")
            clipping_start_datetime = datetime.datetime.strptime(
                str(clipping_start), "%H"
            )
            if clipping_start_datetime > start_time:
                continue
            clip_start_time = start_time
            print(lines[index + 1])
            clip_start_times.append((clip_start_time - epoch_time).total_seconds())

    # combine clip start and end times into list of tuples
    clips = list(zip(clip_start_times, clip_end_times))

    result_json = json.dumps(clips)

    return result_json


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
            type = data["case"]
            if type == "banana_dev":
                result_json = await handle_banana_dev(data)
                await websocket.send(result_json)
            elif type == "gen_clips":
                result_json = await generateClips(data)
                await websocket.send(result_json)
        except json.JSONDecodeError:
            print("Invalid JSON received")
            await websocket.send("Invalid JSON format")


async def main():
    async with websockets.serve(handle_websocket, "0.0.0.0", 8080):
        print("WebSocket server started")
        await asyncio.Future()  # Keep the event loop running


asyncio.run(main())
