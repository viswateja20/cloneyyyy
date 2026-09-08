"""
auth.py
-------
OTP generation, storage and verification for VoiceGuard AI login.

In-memory store for now (fine for a demo / single-process dev server).
Swap for Redis if you ever run multiple workers or need persistence
across restarts.
"""

import random
import time

# phone -> {"otp": "123456", "expires_at": <epoch seconds>, "attempts": 0}
_otp_store = {}

OTP_TTL_SECONDS = 300      # 5 minutes
MAX_VERIFY_ATTEMPTS = 5    # prevent brute-forcing a 6-digit code


def generate_otp(phone: str) -> str:
    code = str(random.randint(100000, 999999))
    _otp_store[phone] = {
        "otp": code,
        "expires_at": time.time() + OTP_TTL_SECONDS,
        "attempts": 0,
    }
    return code


def verify_otp(phone: str, submitted_code: str) -> tuple[bool, str]:
    record = _otp_store.get(phone)

    if not record:
        return False, "No OTP requested for this number."

    if time.time() > record["expires_at"]:
        del _otp_store[phone]
        return False, "OTP expired. Request a new one."

    record["attempts"] += 1
    if record["attempts"] > MAX_VERIFY_ATTEMPTS:
        del _otp_store[phone]
        return False, "Too many attempts. Request a new OTP."

    if submitted_code != record["otp"]:
        return False, "Incorrect code."

    del _otp_store[phone]  # one-time use
    return True, "Verified."
