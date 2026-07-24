#!/usr/bin/env bash
# exit on error
set -o errexit

# Install FFmpeg and ffprobe for yt-dlp merging and analysis
apt-get update && apt-get install -y ffmpeg

# Install Python dependencies
pip install -r requirements.txt