import json
from datetime import datetime, timezone

# The protocol is an allowlist, not a dump of third-party log records.
MESSAGES = {
    "start": "Starting request", "auth": "Checking credentials",
    "authenticated": "Credentials verified", "catalogue": "Reading live catalogue",
    "subset": "Downloading spatial subset", "processing": "Masking and exporting",
    "retry": "Transient service failure; retrying", "complete": "Completed",
    "cancelled": "Cancelled", "timeout": "Time limit reached",
    "AUTH": "Authentication failed. Check your account or try Login again.",
    "NETWORK": "Network or service unavailable. Check connectivity and retry.",
    "SCHEMA": "Unexpected dataset schema. Review catalogue/provenance and documentation.",
    "DEPENDENCY": "Required libraries are missing or incompatible. Open Dependencies.",
    "FAILED": "Request failed. Check ROI, disk space and troubleshooting guide.",
    "SETUP": "Dependency setup failed. See installation instructions.",
}

def event(code, progress=0, dataset=None, attempt=None, result=None, **unused):
    if code not in MESSAGES:
        code = "FAILED"
    record = {"utc": datetime.now(timezone.utc).isoformat(), "code": code,
              "message": MESSAGES[code], "progress": max(0, min(100, int(progress)))}
    if dataset in ("irte", "wk", "it"):
        record["dataset"] = dataset
    if isinstance(attempt, int):
        record["attempt"] = attempt
    # Result is handled separately by the UI; no raw response in the exported log.
    return record

class RunLog:
    def __init__(self):
        self.records = []

    def add(self, record):
        clean = event(**record)
        self.records.append(clean)
        return clean

    def export(self, path):
        with open(path, "w", encoding="utf-8") as stream:
            for record in self.records:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
