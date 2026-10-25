"""Scrub exports; never export arbitrary exception messages or process output."""
import math
import re
from urllib.parse import urlsplit, urlunsplit

SENSITIVE = re.compile(r"password|passwd|secret|token|authorization|credential|username|cookie|api.?key", re.I)
URL = re.compile(r"https?://[^\s<>\"']+")

def safe_url(match):
    try:
        value = urlsplit(match.group(0))
        host = value.hostname or ""
        if value.port:
            host += ":" + str(value.port)
        return urlunsplit((value.scheme, host, value.path, "", ""))
    except ValueError:
        return "[redacted URL]"

def scrub(value, secrets=()):
    if isinstance(value, dict):
        return {str(k): ("[redacted]" if SENSITIVE.search(str(k)) else scrub(v, secrets))
                for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [scrub(v, secrets) for v in value]
    if hasattr(value, "tolist"):
        return scrub(value.tolist(), secrets)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, str):
        value = URL.sub(safe_url, value)
        for secret in sorted((s for s in secrets if s), key=len, reverse=True):
            value = value.replace(secret, "[redacted]")
        return value
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return scrub(str(value), secrets)
