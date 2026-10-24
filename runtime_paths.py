"""Make QGIS's own base-Python DLLs available to its isolated Windows venv."""
import os
from pathlib import Path
import sys

_DLL_HANDLES = []
_DLL_PATHS = set()

def configure_runtime_dlls(base_prefix=None, add_directory=None):
    if os.name != "nt" and add_directory is None:
        return []
    add_directory = add_directory or getattr(os, "add_dll_directory", None)
    if add_directory is None:
        return []
    base = Path(base_prefix or sys.base_prefix).resolve()
    candidates = [base / "DLLs"]
    root = base.parent.parent
    if (root / "apps/qgis").is_dir():
        candidates.append(root / "bin")
    added = []
    for directory in candidates:
        key = str(directory)
        if key in _DLL_PATHS or not directory.is_dir():
            continue
        try:
            handle = add_directory(key)
        except OSError:
            continue
        # The handle must live as long as imports/transfers may need these DLLs.
        _DLL_HANDLES.append(handle)
        _DLL_PATHS.add(key)
        added.append(key)
    return added
