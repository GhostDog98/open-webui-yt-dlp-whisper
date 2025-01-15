"""
title: Youtube Auto-Annotate
author: Your Name
author_url: https://website.com
git_url: https://github.com/username/string-reverse.git
description: This tool downloads a YouTube video and gets SRT subtitles using YouTubeDL and Whisper. 
required_open_webui_version: 0.4.0
requirements: yt-dlp, pydub, requests
version: 0.4.0
licence: MIT
"""

import yt_dlp
import io
import requests
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from pydantic import BaseModel, Field
import time
import os

class Tools:
    def __init__(self):
        pass

    async def get_subtitles(self, url: str, __event_emitter__=None) -> str:
        start_time = time.time()  # Start timing the entire function
        await __event_emitter__(
            {
                "type": "status",
                "data": {"description":"Downloading audio...", "done": False}
            }
        )
        

        video_id = url.split('v=')[-1]

        # Define options for YouTubeDL to extract audio in m4a format
        ydl_opts = {
            'extract_flat': 'discard_in_playlist',
            'final_ext': 'wav',
            'format': 'bestaudio/best',
            'fragment_retries': 10,
            'ignoreerrors': 'only_download',
            'outtmpl': {'default': '%(id)s.%(ext)s'},
            'paths': {'home': '/tmp/'},
            'postprocessor_args': {'ffmpeg': ['-ar', '16000']},
            'postprocessors': [{'key': 'FFmpegExtractAudio',
                               'nopostoverwrites': False,
                               'preferredcodec': 'wav',
                               'preferredquality': '5'},
                              {'key': 'FFmpegConcat',
                               'only_multi_video': True,
                               'when': 'playlist'}],
            'retries': 10}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_id, download=True)
            await __event_emitter__(
            {
                "type": "status",
                "data": {"description":"Saving Audio to temp file...", "done": False}
            }
        )
            with open(f'/tmp/{video_id}.wav', 'rb') as f:
                audio_data = f.read()

        download_time = time.time() - start_time
        print(f"Downloaded {video_id} in {download_time:.2f} seconds")


        print("Audio Metadata")
        important_metadata = {
            'id': info_dict['id'],
            'title': info_dict['title'],
            'description': info_dict['description'],
            'tags': info_dict['tags'],
            'location': info_dict['location'],
            'channel': info_dict['channel'],
        }
        metadata_str = '\n'.join([f"{key}: {value}" for key, value in important_metadata.items()])

        await __event_emitter__(
            {
                "type": "status",
                "data": {"description":"Sending Audio to Whisper model for transcription...", "done": False}
            }
        )


        # Define the URL for the Whisper inference server
        whisper_server_url = "http://localhost:8192/inference"

        # Prepare the WAV file and additional data for the Whisper API request
        files = {
            # Send wav file
            'file': ('input.wav', io.BytesIO(audio_data), 'audio/wav')  
        }
        data = {
            'temperature': '0.0',  # Set temperature for inference
            'temperature_inc': '0.2',  # Set temperature increment
            'response_format': 'vtt'  # Request response in VTT format
        }

        # Send the audio data to the Whisper server for transcription
        whisper_start = time.time()
        response = requests.post(whisper_server_url, files=files, data=data)
        await __event_emitter__(
            {
                "type": "status",
                "data": {"description":"Saving whisper transcription...", "done": False}
            }
        )

        # Log the time taken for Whisper inference
        whisper_time = time.time() - whisper_start
        print(f"Whisper inference completed in {whisper_time:.2f} seconds")

        # Log the total time taken for the entire function
        total_time = time.time() - start_time
        print(f"Total execution time: {total_time:.2f} seconds")

        print(f"Cleaning up temporary files...")
        os.remove(f'/tmp/{video_id}.wav')

        await __event_emitter__(
            {
                "type":"message",
                "data": {"content": f"Whisper transcription completed in {whisper_time:.2f} seconds"}
            }
        )

        # Check if the Whisper inference was successful
        if response.status_code == 200:
            print("Whisper inference successful!")
            return_object = metadata_str + "\n\nTranscription:\n```\n" + response.text + '\n```'
            return return_object
        else:
            return "Whisper inference failed."
        

        