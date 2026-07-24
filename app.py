from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
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

    if 'youtube.com/shorts/' in url:
        url = url.replace('youtube.com/shorts/', 'youtube.com/watch?v=')

    file_id = str(uuid.uuid4())
    
    ydl_opts = {
        'outtmpl': f'{SAVE_DIR}/{file_id}_%(title).50s.mp4',
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'restrictfilenames': True,
        'concurrent_fragment_downloads': 5,
        'extractor_args': {'youtube': {'client': ['android', 'web']}}
    }
    
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            if info and 'entries' in info:
                if info['entries']:
                    info = info['entries'][0]
                else:
                    return jsonify({"error": "No downloadable content found"}), 400

            file_path = ydl.prepare_filename(info)
            
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