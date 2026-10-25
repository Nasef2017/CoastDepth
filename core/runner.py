"""Processing worker bridge: no Qt, credentials only through stdin."""
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess  # nosec B404
import threading
import time
import uuid
from .events import RunLog, event

class WorkerFailure(Exception):
    def __init__(self, code, log_path=None):
        self.code = code
        self.log_path = log_path
        super().__init__(event(code)["message"])

def worker_environment():
    environment = os.environ.copy()
    for name in ("PYTHONHOME", "PYTHONPATH", "GDAL_DATA", "PROJ_LIB", "PROJ_DATA"):
        environment.pop(name, None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["COPERNICUSMARINE_DISABLE_SSL_CONTEXT"] = "False"
    return environment

def execute_worker(python, worker, request, credentials, feedback, timeout_minutes=30):
    run_id = str(uuid.UUID(request["run_id"]))
    root = Path(request["output"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    log_path = root / ("coastdepth_" + run_id + ".jsonl")
    partial = root / (".coastdepth_partial_" + run_id)
    log = RunLog()
    log.add(event("start"))
    proc = None
    complete = None
    last_error = "FAILED"
    channel = queue.Queue()
    deadline = time.monotonic() + timeout_minutes * 60
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        proc = subprocess.Popen([str(python), str(worker)], stdin=subprocess.PIPE,  # nosec B603
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=worker_environment(), creationflags=flags)
        def read_lines():
            try:
                for line in proc.stdout:
                    channel.put(line)
            finally:
                channel.put(None)
        reader = threading.Thread(target=read_lines, daemon=True)
        reader.start()
        payload = dict(request, username=credentials[0], password=credentials[1])
        proc.stdin.write(json.dumps(payload).encode("utf-8") + b"\n")
        proc.stdin.close()
        payload.clear()
        ended = False
        while not ended:
            if feedback.isCanceled():
                raise WorkerFailure("cancelled", log_path)
            if time.monotonic() > deadline:
                raise WorkerFailure("timeout", log_path)
            try:
                line = channel.get(timeout=.1)
            except queue.Empty:
                continue
            if line is None:
                ended = True
                continue
            try:
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError()
                clean = log.add(value)
            except (ValueError, TypeError):
                raise WorkerFailure("FAILED", log_path) from None
            feedback.setProgress(max(feedback.progress(), clean["progress"]))
            feedback.pushInfo(clean["message"])
            if clean["code"] in ("AUTH", "NETWORK", "SCHEMA", "DEPENDENCY", "FAILED"):
                last_error = clean["code"]
            if clean["code"] == "complete":
                complete = value.get("result")
        proc.wait(timeout=5)
        if proc.returncode or not complete:
            raise WorkerFailure(last_error, log_path)
        return complete, str(log_path)
    except WorkerFailure as exc:
        log.add(event(exc.code))
        raise
    except (OSError, ValueError, subprocess.SubprocessError):
        log.add(event("FAILED"))
        raise WorkerFailure("FAILED", log_path) from None
    finally:
        if proc is not None:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)
            if proc.stdout:
                proc.stdout.close()
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()
        if partial.is_dir() and not partial.is_symlink() and partial.resolve().parent == root:
            try:
                shutil.rmtree(partial)
            except OSError:
                feedback.pushInfo("Partial cleanup failed. See troubleshooting.")
        log.export(log_path)
