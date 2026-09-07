\\"""
detector.py
-----------
Loads a PRETRAINED synthetic/cloned-voice detection model from Hugging Face
and exposes one function: analyze_audio(file_path) -> dict

We are NOT training anything here. We are loading a model that has already
been trained by someone else on real vs. fake/synthetic speech, and just
running inference (prediction) on our own audio clips.

Model used: MODEL_NAME = "HyperMoon/wav2vec2-base-960h-finetuned-deepfake"
  - A Wav2Vec2-based binary classifier: "real" (bonafide) vs "fake" (spoof/synthetic)
  - Runs fine on CPU (no GPU required), just slower than GPU.

If this model ever fails to download/load, a good backup is:
  "Mahmoud59/wav2vec2-fake-audio-detector"
Just swap the MODEL_NAME string below.
"""

import torch
import librosa
from transformers import Wav2Vec2Processor, Wav2Vec2ForSequenceClassification

MODEL_NAME = "HyperMoon/wav2vec2-base-960h-finetuned-deepfake"
# Some fake-detection models label classes as 0=fake,1=real or vice versa.
# We check model.config.id2label at load time and adapt automatically
# instead of hardcoding it, so this keeps working even if you swap models.

print(f"[detector.py] Loading model '{MODEL_NAME}' ... (first run downloads it, may take a minute)")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
model = Wav2Vec2ForSequenceClassification.from_pretrained(MODEL_NAME)
model.to(device)
model.eval()
print(f"[detector.py] Model loaded on device: {device}")
print(f"[detector.py] Label map from model config: {model.config.id2label}")


def _find_label_index(target_words):
    """Find which output index corresponds to 'fake'/'spoof' labels."""
    for idx, label in model.config.id2label.items():
        if any(w in label.lower() for w in target_words):
            return int(idx)
    return None


FAKE_IDX = _find_label_index(["fake", "spoof", "synthetic", "clone"])
REAL_IDX = _find_label_index(["real", "bonafide", "genuine"])

# Fallback if label names are unexpected (e.g. "LABEL_0"/"LABEL_1")
if FAKE_IDX is None or REAL_IDX is None:
    print("[detector.py] WARNING: could not auto-detect label names, defaulting to index 1=fake, 0=real")
    FAKE_IDX, REAL_IDX = 1, 0


def analyze_audio(file_path: str) -> dict:
    """
    Takes a path to a short audio file (wav/mp3/flac, a few seconds long)
    and returns a dict with the clone/spoof probability and a risk verdict.
    """
    # Load audio, force 16kHz mono (what the model expects)
    audio, _sr = librosa.load(file_path, sr=16000, mono=True)

    inputs = processor(audio, sampling_rate=16000, return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]

    clone_probability = float(probs[FAKE_IDX])
    authenticity = float(probs[REAL_IDX])

    if clone_probability >= 0.70:
        risk_level = "HIGH"
    elif clone_probability >= 0.40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "authenticity_percent": round(authenticity * 100, 1),
        "clone_probability_percent": round(clone_probability * 100, 1),
        "risk_level": risk_level,
    }


if __name__ == "__main__":
    # Quick manual test: python detector.py path/to/audio.wav
    import sys
    if len(sys.argv) < 2:
        print("Usage: python detector.py <path_to_audio_file>")
    else:
        result = analyze_audio(sys.argv[1])
        print(result)
