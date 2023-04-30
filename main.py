import banana_dev as banana
import asyncio
import os
import random
import re
import websockets
import json

# import whisperx
import datetime

# from whisperx.utils import write_srt
# from whisperx.utils import write_ass


async def ConvertSubtitleTheme(subtitle_file, new_subtitle_file, comment=None):
    with open(subtitle_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(new_subtitle_file, "w", encoding="utf-8") as f:
        for line in lines:
            if line.startswith("Dialogue:"):
                if comment is not None:
                    f.write(
                        "Dialogue: 0,0:00:0.00,00:00:8.00,Default,,0,0,0,,{\\fad(0,150)\\pos(960,850)}"
                        + comment
                        + "\n"
                    )
                break
            f.write(line)

        last_line = None
        last_text = None
        last_time_end = datetime.timedelta(seconds=0)
        last_time_start = datetime.timedelta(seconds=0)
        last_raw_line = None
        for line in lines:
            if line.startswith("Dialogue:"):
                match = re.search("}(.*?){", line)
                if not match:
                    continue

                text = match.group(1)
                if last_line is not None:
                    time_fields = line.strip().split(",")
                    epoch_time = datetime.datetime.strptime("0", "%f")
                    hours, minutes, seconds = map(float, time_fields[1].split(":"))
                    start_time_ms = datetime.timedelta(
                        hours=hours, minutes=minutes, seconds=seconds
                    )
                    hours, minutes, seconds = map(float, time_fields[2].split(":"))
                    end_time_ms = datetime.timedelta(
                        hours=hours, minutes=minutes, seconds=seconds
                    )
                    end_time = (epoch_time + end_time_ms).strftime("%H:%M:%S.%f")[:-4]

                    temp_text = last_text + " " + text

                    if (
                        len(temp_text) <= 12
                        and "." not in last_text
                        and text in last_raw_line
                        and "!" not in last_text
                        and "?" not in last_text
                        and not last_text.rstrip().endswith(",")
                    ):
                        last_text_fields = last_line.strip().split(",,")
                        last_time_fields = last_line.strip().split(",")
                        last_temp_fields = last_text_fields[0].strip().split(",")

                        last_raw_line = line
                        last_text = temp_text
                        last_line = (
                            last_temp_fields[0]
                            + ","
                            + last_temp_fields[1]
                            + ","
                            + end_time
                            + ","
                            + last_temp_fields[3]
                            + ",,"
                            + last_text_fields[1]
                            + ",,"
                            + last_text
                            + "\n"
                        )
                        continue

                    timeAmount = last_time_end - last_time_start
                    last_time_end = last_time_end + max(
                        datetime.timedelta(seconds=0),
                        datetime.timedelta(microseconds=1250000) - timeAmount,
                    )
                    last_time_end = min(last_time_end, start_time_ms)

                    last_time_end_normal = (epoch_time + last_time_end).strftime(
                        "%H:%M:%S.%f"
                    )[:-4]

                    temp_fields = last_line.strip().split(",,")
                    last_text = (
                        last_text.replace(".", "")
                        .replace(",", "")
                        .replace("!", "")
                        .upper()
                    )
                    timingNew_fields = temp_fields[0].strip().split(",")
                    margin_fields = temp_fields[1].strip().split(",")
                    last_line = (
                        timingNew_fields[0]
                        + ","
                        + timingNew_fields[1]
                        + ","
                        + last_time_end_normal
                        + ","
                        + timingNew_fields[3]
                        + ",,"
                        + margin_fields[0]
                        + ","
                        + margin_fields[1]
                        + ","
                        + margin_fields[2]
                        + ",,"
                        + "{\\fad(20,20)\pos(960,500)}"
                        + last_text
                        + "\n"
                    )

                    last_time_end = end_time_ms
                    last_time_start = start_time_ms
                    f.write(last_line)

                last_line = line
                last_text = text
                last_raw_line = line


async def generateClips(ws, result, clip_length, clipping_start, clipping_end):
    id = str(random.randint(1, 10000))

    with open(f"subtitles{id}.ass", "w", encoding="utf-8") as file:
        write_ass(
            result["segments"],
            file=file,
            resolution="word",
            font="Mercadillo Bold",
            font_size=80,
            underline=False,
            xRes="1920",
            yRes="1080",
            **{"Bold": "1", "Alignment": "5", "Outline": "6", "Shadow": "6"},
        )

    with open(f"subtitles{id}.srt", "w", encoding="utf-8") as file:
        write_srt(result["segments"], file=file)

    # Open the SRT file and read its contents
    with open(f"subtitles{id}.srt", "r") as f:
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
                str(clipping_start), "%H:%M:%S,%f"
            )
            clipping_end_datetime = datetime.datetime.strptime(
                str(clipping_end), "%H:%M:%S,%f"
            )
            if clipping_start_datetime > start_time:
                continue
            if clipping_end_datetime <= start_time:
                break
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
            type = data["type"]
            if type == "export_video" or type == "transcribe_audio":
                result_json = await handle_banana_dev(data)
                await websocket.send(result_json)
            elif type == "gen_clips":
                clip_length = data["clip_length"]
                start_time = data["start_time"]
                end_time = data["end_time"]
                segments_stuff = await handle_banana_dev(data)
                await websocket.send(segments_stuff)  # "transcribed audio")
                # output = await generateClips(
                #    websocket, segments_stuff, clip_length, start_time, end_time
                # )
                # await websocket.send(output)
        except json.JSONDecodeError:
            print("Invalid JSON received")
            await websocket.send("Invalid JSON format")


async def main():
    async with websockets.serve(handle_websocket, "0.0.0.0", 443):
        print("WebSocket server started")
        await asyncio.Future()  # Keep the event loop running


asyncio.run(main())
