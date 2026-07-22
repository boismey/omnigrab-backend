from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import imageio_ffmpeg
import os
import uuid
import threading
import time
from urllib.parse import quote

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

SAVE_DIR = "temp_downloads"
os.makedirs(SAVE_DIR, exist_ok=True)

def delayed_delete(file_path):
    """Waits 10 minutes before deleting the file to give download managers time to finish."""
    time.sleep(600) 
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Cleaned up: {file_path}")
    except Exception as e:
        print(f"Could not delete file: {e}")

# STEP 1: Download to server and return a unique ID
@app.route('/api/prepare', methods=['POST'])
def prepare_video():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    file_id = str(uuid.uuid4())
    
    ydl_opts = {
        'outtmpl': f'{SAVE_DIR}/{file_id}_%(title).50s.%(ext)s',
        # Fall back to 'best' format which avoids needing local ffmpeg merging on cloud containers
        'format': 'best',
        'quiet': True,
        'noplaylist': True,
        'restrictfilenames': True,
        'concurrent_fragment_downloads': 5,
        'cookiefile': 'cookies.txt',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            filename = os.path.basename(file_path)
            
        return jsonify({"status": "ready", "filename": filename})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# STEP 2: Stream to the user's hard drive and delete later
@app.route('/api/download/<path:filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(SAVE_DIR, filename)
    
    if not os.path.exists(file_path):
        return "File not found or expired", 404
    
    display_name = filename.split('_', 1)[1] if '_' in filename else filename
    encoded_name = quote(display_name)
    
    # Start the 10-minute countdown to delete the file in the background
    threading.Thread(target=delayed_delete, args=(file_path,)).start()
    
    # send_file natively supports IDM's multi-part chunk downloading
    response = send_file(file_path, as_attachment=True)
    
    # Safely attach the emoji-supported filename
    response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_name}"
    
    return response

if __name__ == '__main__':
    app.run(port=3000, debug=True)