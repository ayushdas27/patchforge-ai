import re
from typing import Any

SENSITIVE_PATTERNS = [
    # (pattern, replacement)
    (r"(?i)(bearer\s+)[a-zA-Z0-9_\-\.]{8,}", r"\g<1>[REDACTED]"),
    (r"(?i)(api[_-]?key\s*[:=]\s*['\"]?)[a-zA-Z0-9_\-\.]{8,}(['\"]?)", r"\g<1>[REDACTED]\g<2>"),
    (r"(?i)(secret\s*[:=]\s*['\"]?)[a-zA-Z0-9_\-\.]{8,}(['\"]?)", r"\g<1>[REDACTED]\g<2>"),
    (r"(?i)(token\s*[:=]\s*['\"]?)[a-zA-Z0-9_\-\.]{8,}(['\"]?)", r"\g<1>[REDACTED]\g<2>"),
    (r"(?i)(authorization\s*:\s*Bearer\s+)[a-zA-Z0-9_\-\.]+", r"\g<1>[REDACTED]"),
]

def redact_secrets(text: str) -> str:
    """Redacts potential secrets, auth tokens, and API keys from logs or output."""
    if not text:
        return ""
    redacted = text
    for pattern, repl in SENSITIVE_PATTERNS:
        redacted = re.sub(pattern, repl, redacted)
    return redacted

def mask_api_key(key: str | None) -> str:
    """Safely masks an API key showing only prefix/suffix without exposing credentials."""
    if not key:
        return "Not Set"
    stripped = key.strip()
    if len(stripped) <= 8:
        return "****"
    return f"{stripped[:4]}...{stripped[-4:]}"
