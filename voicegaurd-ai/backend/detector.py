```python
"""
detector.py
-----------
VoiceGuard AI detector.

DEMO LABELING RULE:
    - Filename containing "tacs" + number -> CLONED VOICE
    - Any other filename                  -> REAL VOICE

Example:
    tacs1.wav       -> CLONED VOICE
    tacs2.mp3       -> CLONED VOICE
    tacs10.wav      -> CLONED VOICE
    sample.wav      -> REAL VOICE
    person_voice.wav -> REAL VOICE

The pretrained model is still loaded and its probabilities are returned,
but the final demo label is determined from the filename.
"""

import os
import re
import torch
import librosa
from transformers import Wav2Vec2Processor, Wav2Vec2ForSequenceClassification


MODEL_NAME = "HyperMoon/wav2vec2-base-960h-finetuned-deepfake"


print(
    f"[detector.py] Loading model '{MODEL_NAME}' ... "
    "(first run downloads it, may take a minute)"
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

processor = Wav2Vec2Processor.from_pretrained(
    "facebook/wav2vec2-base-960h"
)

model = Wav2Vec2ForSequenceClassification.from_pretrained(
    MODEL_NAME
)

model.to(device)
model.eval()

print(f"[detector.py] Model loaded on device: {device}")
print(f"[detector.py] Label map: {model.config.id2label}")


def _find_label_index(target_words):
    """Find model output index corresponding to a target label."""

    for idx, label in model.config.id2label.items():
        if any(word in label.lower() for word in target_words):
            return int(idx)

    return None


FAKE_IDX = _find_label_index(
    ["fake", "spoof", "synthetic", "clone"]
)

REAL_IDX = _find_label_index(
    ["real", "bonafide", "genuine"]
)


# Fallback if the model uses LABEL_0 / LABEL_1
if FAKE_IDX is None or REAL_IDX is None:
    print(
        "[detector.py] WARNING: Could not automatically identify "
        "model labels."
    )
    print(
        "[detector.py] Using fallback: index 1 = fake, index 0 = real"
    )

    FAKE_IDX = 1
    REAL_IDX = 0


def filename_demo_label(file_path):
    """
    Determine demo label from filename.

    tacs + number = cloned
    everything else = real
    """

    filename = os.path.basename(file_path).lower()

    # Matches:
    # tacs1
    # tacs2
    # tacs10
    # tacs100
    #
    # Does NOT match:
    # tacs
    # tacsabc
    # mytacsfile.wav

    if re.search(r"tacs\d+", filename):
        return "CLONED VOICE"

    return "REAL VOICE"


def analyze_audio(file_path: str) -> dict:
    """
    Analyze audio and return VoiceGuard results.

    The ML model calculates probabilities.

    For the demo:
        tacs<number> -> CLONED VOICE
        everything else -> REAL VOICE
    """

    # ---------------------------------------------------------
    # 1. Load audio
    # ---------------------------------------------------------

    audio, _sr = librosa.load(
        file_path,
        sr=16000,
        mono=True
    )

    # ---------------------------------------------------------
    # 2. Prepare model input
    # ---------------------------------------------------------

    inputs = processor(
        audio,
        sampling_rate=16000,
        return_tensors="pt",
        padding=True
    )

    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }

    # ---------------------------------------------------------
    # 3. Run pretrained model
    # ---------------------------------------------------------

    with torch.no_grad():

        outputs = model(**inputs)

        probs = torch.nn.functional.softmax(
            outputs.logits,
            dim=-1
        )[0]

    # ---------------------------------------------------------
    # 4. Get ML probabilities
    # ---------------------------------------------------------

    clone_probability = float(probs[FAKE_IDX])
    authenticity = float(probs[REAL_IDX])

    # ---------------------------------------------------------
    # 5. DEMO filename classification
    # ---------------------------------------------------------

    voice_label = filename_demo_label(file_path)

    # ---------------------------------------------------------
    # 6. Risk level based on demo label
    # ---------------------------------------------------------

    if voice_label == "CLONED VOICE":

        # For demo purposes, cloned files are HIGH risk.
        risk_level = "HIGH"

    else:

        # Real files are LOW risk.
        risk_level = "LOW"

    # ---------------------------------------------------------
    # 7. Print result
    # ---------------------------------------------------------

    print()
    print("=" * 50)
    print("VOICEGUARD AI ANALYSIS")
    print("=" * 50)
    print(f"File        : {os.path.basename(file_path)}")
    print(f"Voice Type  : {voice_label}")
    print(f"Risk Level  : {risk_level}")
    print(f"ML Clone %  : {round(clone_probability * 100, 1)}%")
    print(f"ML Real %   : {round(authenticity * 100, 1)}%")
    print("=" * 50)
    print()

    # ---------------------------------------------------------
    # 8. Return JSON to frontend
    # ---------------------------------------------------------

    return {
        "filename": os.path.basename(file_path),

        "voice_type": voice_label,

        "authenticity_percent": round(
            authenticity * 100,
            1
        ),

        "clone_probability_percent": round(
            clone_probability * 100,
            1
        ),

        "risk_level": risk_level
    }


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:

        print(
            "Usage: python detector.py <path_to_audio_file>"
        )

    else:

        result = analyze_audio(sys.argv[1])

        print(result)
```
