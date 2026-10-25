"""Standard-library-only helper; invoked in a child Python process."""
import importlib
import importlib.metadata
import contextlib
import json
import logging
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess  # nosec B404
import sys
import venv
try:
    from .runtime_paths import configure_runtime_dlls
except ImportError:  # Executed as a child script rather than a package import.
    from runtime_paths import configure_runtime_dlls

PACKAGES = {"copernicusmarine": "copernicusmarine", "numpy": "numpy", "xarray": "xarray",
            "netCDF4": "netCDF4", "rasterio": "rasterio", "packaging": "packaging"}
SPECS = {"copernicusmarine": "==2.4.0", "numpy": ">=2.1,<3", "xarray": ">=2024.10,<2027",
         "netCDF4": ">=1.7,<2", "rasterio": ">=1.4.3,<2", "packaging": ">=24"}

def requirement_names(modules=None):
    selected = set(PACKAGES if modules is None else modules)
    return [name + SPECS[module] for module, name in PACKAGES.items() if module in selected]

def missing_environment_result():
    return {"ready": False, "environment_missing": True, "compatible_python": True,
            "missing": list(PACKAGES), "broken": [], "incompatible": [], "packages": {}}

def shell_commands(base_python, environment, result, windows=None):
    """Copyable commands for OSGeo4W Shell; never run implicitly."""
    import shlex
    windows = os.name == "nt" if windows is None else windows
    def quote(value):
        value = str(value)
        if windows:
            if any(c in value for c in ('"', '%', '!', '\r', '\n')):
                raise ValueError("This path cannot be safely represented in an OSGeo4W Shell command.")
            return '"' + value + '"'
        return shlex.quote(value)
    commands = []
    if result.get("environment_missing"):
        commands.append(quote(base_python) + " -m venv " + quote(environment))
    if windows:
        commands.extend(['set "PYTHONHOME="', 'set "PYTHONPATH="'])
    else:
        commands.extend(["unset PYTHONHOME", "unset PYTHONPATH"])
    issues = result.get("missing", []) + result.get("broken", []) + result.get("incompatible", [])
    requirements = requirement_names(issues) or requirement_names()
    worker = (PureWindowsPath(environment) / "Scripts/python.exe" if windows else
              PurePosixPath(environment) / "bin/python")
    commands.append(quote(worker) + " -m pip --isolated install --upgrade --disable-pip-version-check "
                    "--only-binary=:all: --index-url https://pypi.org/simple " + quote("pip>=26.2.2"))
    repair = "--force-reinstall " if result.get("broken") else ""
    commands.append(quote(worker) + " -m pip --isolated install " + repair + "--only-binary=:all: "
                    "--index-url https://pypi.org/simple " + " ".join(quote(r) for r in requirements))
    return "\n".join(commands)

def environment_python(root):
    return Path(root) / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

def probe():
    configure_runtime_dlls()
    result = {"python": sys.version.split()[0], "executable": sys.executable,
              "compatible_python": sys.version_info >= (3, 10), "packages": {}, "ready": True,
              "environment_missing": False, "missing": [], "broken": [], "incompatible": []}
    for module, distribution in PACKAGES.items():
        try:
            with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                importlib.import_module(module)
            result["packages"][module] = importlib.metadata.version(distribution)
        except ModuleNotFoundError as exc:
            status = "missing" if exc.name == module else "broken"
            result[status].append(module)
            result["packages"][module] = "not installed" if status == "missing" else "import failed"
            result["ready"] = False
        except Exception:
            result["packages"][module] = "import failed"
            result["broken"].append(module)
            result["ready"] = False
    try:
        from packaging.specifiers import SpecifierSet
        for name, spec in SPECS.items():
            if name in result["missing"] or name in result["broken"]:
                continue
            if not SpecifierSet(spec).contains(result["packages"][name]):
                result["incompatible"].append(name)
                result["ready"] = False
    except Exception:
        result["ready"] = False
    result["ready"] = result["ready"] and result["compatible_python"]
    return result

def setup(root):
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10 or newer required")
    root = Path(root).resolve()
    # Allow repair of a previously created venv, never convert a non-venv directory.
    if root.exists() and any(root.iterdir()) and not (root / "pyvenv.cfg").exists():
        raise ValueError("Target is not a virtual environment")
    venv.EnvBuilder(with_pip=True, system_site_packages=False).create(root)
    environment = os.environ.copy()
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    stages = (["--upgrade", "pip>=26.2.2"],
              ["-r", str(Path(__file__).with_name("requirements-worker.txt"))])
    for requirements in stages:
        subprocess.run([str(environment_python(root)), "-m", "pip", "--isolated", "install",  # nosec B603
            "--disable-pip-version-check", "--only-binary=:all:", "--index-url", "https://pypi.org/simple",
            "--retries", "1", "--timeout", "30", *requirements],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
            env=environment)

if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--setup":
            setup(sys.argv[2])
            print(json.dumps({"setup": True}))
        else:
            print(json.dumps(probe()))
    except Exception:
        print(json.dumps({"setup": False, "code": "SETUP"}))
        sys.exit(1)
