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
from auth import generate_otp, verify_otp


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
            from flask import Flask, request, jsonify
from flask_cors import CORS
from detector import analyze_audio
from auth import generate_otp, verify_otp

app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "VoiceGuard AI backend is running"
    })


@app.route("/analyze", methods=["POST"])
def analyze():

    # your existing analyze code here
    # ...
    
    return jsonify(result)


# =========================================================
# OTP AUTHENTICATION
# =========================================================

@app.route("/send-otp", methods=["POST"])
def send_otp():

    data = request.get_json(silent=True) or {}
    phone = data.get("phone")

    if not phone or len(phone) != 10 or not phone.isdigit():
        return jsonify({
            "error": "Valid 10-digit phone number required."
        }), 400

    code = generate_otp(phone)

    # Development only
    print(f"[DEV] OTP for {phone}: {code}")

    return jsonify({
        "status": "OTP sent"
    })


@app.route("/verify-otp", methods=["POST"])
def verify_otp_route():

    data = request.get_json(silent=True) or {}

    phone = data.get("phone")
    code = data.get("otp")

    if not phone or not code:
        return jsonify({
            "error": "phone and otp are required."
        }), 400

    ok, message = verify_otp(phone, code)

    if not ok:
        return jsonify({
            "error": message
        }), 400

    return jsonify({
        "status": "verified"
    })


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
```
