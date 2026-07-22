from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import uuid
import threading
import time
from urllib.parse import quote
import imageio_ffmpeg

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

SAVE_DIR = "temp_downloads"
os.makedirs(SAVE_DIR, exist_ok=True)

def delayed_delete(file_path):
    """Waits 10 minutes before deleting the file."""
    time.sleep(600) 
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass

@app.route('/api/prepare', methods=['POST'])
def prepare_video():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # Normalize Shorts URLs to standard watch URLs for easier extraction
    if 'youtube.com/shorts/' in url:
        url = url.replace('youtube.com/shorts/', 'youtube.com/watch?v=')

    file_id = str(uuid.uuid4())
    
    ydl_opts = {
        # FIX 1: Hardcode the .mp4 extension so Flask always knows the exact filename
        'outtmpl': f'{SAVE_DIR}/{file_id}_%(title).50s.mp4',
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        # FIX 2: Explicitly force FFmpeg to merge into an .mp4 wrapper
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'restrictfilenames': True,
        'concurrent_fragment_downloads': 5,
        'ffmpeg_location': imageio_ffmpeg.get_ffmpeg_exe(),
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }
    
    # Safely load cookies if the file exists
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # FIX 3: Download in one single step to prevent filename mismatches
            info = ydl.extract_info(url, download=True)
            
            # Isolate the exact video if it's trapped in a feed/playlist dict
            if info and 'entries' in info:
                if info['entries']:
                    info = info['entries'][0]
                else:
                    return jsonify({"error": "No downloadable content found"}), 400

            file_path = ydl.prepare_filename(info)
            
            # Double-check safety net to ensure Flask searches for an .mp4
            if not file_path.endswith('.mp4'):
                file_path = os.path.splitext(file_path)[0] + '.mp4'
                
            filename = os.path.basename(file_path)
            
        return jsonify({"status": "ready", "filename": filename})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<path:filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(SAVE_DIR, filename)
    
    if not os.path.exists(file_path):
        return "File not found or expired", 404
    
    display_name = filename.split('_', 1)[1] if '_' in filename else filename
    encoded_name = quote(display_name)
    
    threading.Thread(target=delayed_delete, args=(file_path,)).start()
    response = send_file(file_path, as_attachment=True)
    response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_name}"
    
    return response

if __name__ == '__main__':
    app.run(port=3000, debug=True)