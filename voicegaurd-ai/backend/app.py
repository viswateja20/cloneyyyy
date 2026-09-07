```python
"""
app.py
------
VoiceGuard AI Flask backend.

POST /analyze
Accepts an audio file and returns the analysis result.
"""

import os
import tempfile

from flask import Flask, request, jsonify
from flask_cors import CORS

from detector import analyze_audio


app = Flask(__name__)

CORS(app)


@app.route("/", methods=["GET"])
def health_check():

    return jsonify({
        "status": "VoiceGuard AI backend is running"
    })


@app.route("/analyze", methods=["POST"])
def analyze():

    # ---------------------------------------------------------
    # Check file
    # ---------------------------------------------------------

    if "audio" not in request.files:

        return jsonify({
            "error": "No audio file uploaded. "
                     "Send it as form field 'audio'."
        }), 400

    audio_file = request.files["audio"]

    # ---------------------------------------------------------
    # Preserve original filename
    # ---------------------------------------------------------

    original_filename = audio_file.filename

    if not original_filename:

        return jsonify({
            "error": "Uploaded file has no filename."
        }), 400

    # ---------------------------------------------------------
    # Save temporary file
    # ---------------------------------------------------------

    extension = os.path.splitext(
        original_filename
    )[1]

    if not extension:
        extension = ".wav"

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extension
    ) as tmp:

        audio_file.save(tmp.name)

        tmp_path = tmp.name

    # ---------------------------------------------------------
    # Analyze
    # ---------------------------------------------------------

    try:

        result = analyze_audio(tmp_path)

        # Replace temporary filename with ORIGINAL filename
        result["filename"] = original_filename

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if os.path.exists(tmp_path):

            os.remove(tmp_path)


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
```
