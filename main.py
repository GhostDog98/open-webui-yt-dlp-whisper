"""
title: Youtube Auto-Annotate
author: Your Name
author_url: https://website.com
git_url: https://github.com/username/string-reverse.git
description: This tool downloads a YouTube video and gets SRT subtitles using YouTubeDL and Whisper. 
required_open_webui_version: 0.4.0
requirements: yt-dlp, pydub, requests, time
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

import yt_dlp
import io
import requests
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from pydantic import BaseModel, Field
import time  # Import the time module for timing

class Tools:
    def __init__(self):
        pass
    
    def get_subtitles(self, url: str):
        start_time = time.time()  # Start timing the entire function

        # Define options for YouTubeDL to extract audio in m4a format
        ydl_opts = {
            'format': 'm4a/bestaudio/best',  # Choose the best available audio format
            'extract_audio': True,  # Extract audio from the video
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',  # Use FFmpeg to extract audio
                'preferredcodec': 'wav',  # Prefer m4a as the audio codec,
                'preferredquality': '16k'  # Set the quality to 16k (16 kHz)
            }],
            'noplaylist': True,
            'extractaudio': True,
            
        }

        # Use YouTubeDL with the defined options
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract metadata about the video/audio without downloading it
            info_dict = ydl.extract_info(url, download=False)
            
            # Get the direct URL of the audio stream from the metadata
            audio_url = info_dict['url']
            
            # Download the audio data using requests, streaming it in chunks
            response = requests.get(audio_url, stream=True)
            
            # Use a buffer to capture the audio data as it is downloaded
            buffer = io.BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                buffer.write(chunk)  # Write each chunk to the buffer
        
        audio_data = buffer.getvalue()  # Now `buffer` contains the complete audio data

        # Log the time taken to download and buffer the audio
        download_time = time.time() - start_time
        print(f"Audio download and buffering completed in {download_time:.2f} seconds")

        # Load the audio data into a PyDub AudioSegment object
        audio_load_start = time.time()
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format='m4a')
        audio = audio.set_channels(1)  # Convert stereo audio to mono
        audio = audio.set_frame_rate(16000)  # Set the audio frame rate to 16kHz

        # Convert the audio to WAV format
        wav_buffer = io.BytesIO()
        audio.export(wav_buffer, format='wav')  # Export audio to WAV format
        wav_data = wav_buffer.getvalue()  # Get the WAV data from the buffer

        # Log the time taken to load and convert the audio
        audio_load_time = time.time() - audio_load_start
        print(f"Audio loading and conversion completed in {audio_load_time:.2f} seconds")

        # Print audio details for verification
        print("Audio verified to be valid!")
        print(f"Audio duration: {audio.duration_seconds} seconds")
        print(f"Audio channels: {audio.channels}")
        print(f"Audio sample rate: {audio.frame_rate} Hz")

        # Define the URL for the Whisper inference server
        whisper_server_url = "http://localhost:8192/inference"

        # Prepare the WAV file and additional data for the Whisper API request
        files = {
            'file': ('input.wav', io.BytesIO(wav_data), 'audio/wav')  # WAV file to be sent
        }
        data = {
            'temperature': '0.0',  # Set temperature for inference
            'temperature_inc': '0.2',  # Set temperature increment
            'response_format': 'vtt'  # Request response in VTT format
        }

        # Send the audio data to the Whisper server for transcription
        whisper_start = time.time()
        response = requests.post(whisper_server_url, files=files, data=data)

        # Log the time taken for Whisper inference
        whisper_time = time.time() - whisper_start
        print(f"Whisper inference completed in {whisper_time:.2f} seconds")

        # Log the total time taken for the entire function
        total_time = time.time() - start_time
        print(f"Total execution time: {total_time:.2f} seconds")

        # Check if the Whisper inference was successful
        if response.status_code == 200:
            print("Whisper inference successful!")
            return f"Provide a summary of the transcript from the following VTT subtitles: {response.text}"

        