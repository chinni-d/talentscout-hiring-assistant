import os
import json
from cryptography.fernet import Fernet
from datetime import datetime
import base64

EXIT_KEYWORDS = {"exit","quit","bye","end","stop","bye bye","thank you","thanks","done"}

def format_techstack(raw):
    # split on commas and semicolons, strip, and normalize
    parts = [p.strip() for p in raw.replace(";",",").split(",") if p.strip()]
    return parts

def is_end_conversation(text):
    txt = text.lower().strip()
    return any(k in txt for k in EXIT_KEYWORDS)

def _get_key():
    key = os.getenv("ENCRYPTION_KEY")
    if key:
        return key.encode()
    else:
        # create ephemeral key and warn (for demo)
        k = Fernet.generate_key()
        return k

def save_submission_encrypted(candidate_info, generated_qs, outdir="submissions"):
    os.makedirs(outdir, exist_ok=True)
    payload = {
        "candidate": candidate_info,
        "questions": generated_qs,
        "ts": datetime.utcnow().isoformat()
    }
    raw = json.dumps(payload, indent=2).encode()
    key = _get_key()
    f = Fernet(key)
    token = f.encrypt(raw)
    fname = datetime.utcnow().strftime("submission_%Y%m%dT%H%M%S.enc")
    path = os.path.join(outdir, fname)
    with open(path, "wb") as fh:
        fh.write(token)
    return path
