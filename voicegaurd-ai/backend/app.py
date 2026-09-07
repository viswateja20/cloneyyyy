

"""
app.py
------
A tiny Flask backend with ONE endpoint: POST /analyze
It accepts an audio file (short clip, a few seconds) and returns
authenticity / clone probability / risk level as JSON.
 
This is intentionally simple (no WebSockets) so it's easy to build,
debug, and demo under time pressure. The frontend will call this
endpoint every few seconds to create a "near real-time" feel.
 
HOW TO RUN:
    1. cd backend
    2. pip install -r requirements.txt
    3. python app.py
    4. It starts on http://localhost:5000
 
HOW TO TEST (without frontend, using curl or Postman):
    curl -X POST -F "audio=@../test_audio/sample.wav" http://localhost:5000/analyze
"""
 
import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from detector import analyze_audio
 
app = Flask(__name__)
CORS(app)  # allows the frontend (running on a different port) to call this API
 
 
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "VoiceGuard AI backend is running"})
 
 
@app.route("/analyze", methods=["POST"])
def analyze():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded. Send it as form field 'audio'."}), 400
 
    audio_file = request.files["audio"]
 
    # Save to a temporary file because librosa needs a file path (or file-like object)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name
 
    try:
        result = analyze_audio(tmp_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(tmp_path)
 
 
if __name__ == "__main__":
    # debug=True auto-reloads on code changes -- useful while building,
    # turn off (debug=False) for the actual demo so it's more stable.
    app.run(host="0.0.0.0", port=5000, debug=True)
 
