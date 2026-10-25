"""Child process protocol: one JSON request on stdin; fixed JSON events on stdout."""
import contextlib
import json
import logging
import os
from pathlib import Path
import shutil
import sys
import uuid

# Executed by absolute filename; ensure the package directory and DLLs are configured.
package_dir = Path(__file__).resolve().parent
plugins_dir = package_dir.parent
if str(plugins_dir) not in sys.path:
    sys.path.insert(0, str(plugins_dir))

if "coastdepth" not in sys.modules:
    try:
        import coastdepth
    except ModuleNotFoundError:
        import importlib
        sys.modules["coastdepth"] = importlib.import_module(package_dir.name)

from coastdepth.runtime_paths import configure_runtime_dlls
configure_runtime_dlls()

from coastdepth.core.catalogue import DATASETS, DATASET_FOLDERS, DOI, select_variables
from coastdepth.core.events import event
from coastdepth.core.models import Bounds
from coastdepth.core.provider import MarineProvider, ProviderError

PROTOCOL = sys.stdout

def emit(code, progress=0, **kw):
    value = event(code, progress, **kw)
    if "result" in kw:
        value["result"] = kw["result"]
    PROTOCOL.write(json.dumps(value, ensure_ascii=False) + "\n")
    PROTOCOL.flush()

def run(request, provider_factory=MarineProvider):
    configure_runtime_dlls()
    from coastdepth.core.raster import export_subset
    from coastdepth.core.provenance import provenance, write_json
    username, password = request.pop("username", ""), request.pop("password", "")
    provider = provider_factory(username, password, emit)
    provider.validate()
    if request.get("action") == "login":
        emit("complete", 100)
        return
    keys = request["datasets"]
    if not keys or len(keys) != len(set(keys)) or any(k not in DATASETS for k in keys):
        raise ValueError("Invalid datasets")
    bounds = Bounds(**request["bounds"]).validate()
    formats = request["formats"]
    if not formats or not set(formats) <= {"netcdf", "geotiff"}:
        raise ValueError("Invalid formats")
    root = Path(request["output"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    run_id = str(uuid.UUID(request["run_id"]))
    partial = root / (".coastdepth_partial_" + run_id)
    final = root / ("coastdepth_" + run_id)
    partial.mkdir(exist_ok=False)
    try:
        relative_outputs = []
        netcdf_variables = {}
        for index, key in enumerate(keys):
            directory = partial / DATASET_FOLDERS[key]
            directory.mkdir()
            catalogue = provider.describe(key)
            emit("subset", 10 + int(index * 80 / len(keys)), dataset=key)
            response = provider.subset(key, bounds, directory)
            source = directory / "source.nc"
            if not source.is_file():
                raise ProviderError("SCHEMA")
            emit("processing", 10 + int((index + .65) * 80 / len(keys)), dataset=key)
            paths = export_subset(source, directory, request.get("polygon"), formats,
                {"product_doi": DOI, "dataset_id": DATASETS[key][1], "provenance": "provenance.json"},
                secrets=(username, password))
            info = provenance(source, catalogue, key, bounds, request.get("polygon"), response,
                              paths, (username, password))
            for path in paths:
                if path.suffix == ".nc":
                    netcdf_variables[str(path.relative_to(partial))] = select_variables(info["source_variables"])
            write_json(directory / "provenance.json", info)
            source.unlink()
            relative_outputs.extend(str(p.relative_to(partial)) for p in paths)
        write_json(partial / "manifest.json", {"schema_version": 1, "run_id": run_id,
                   "datasets": keys, "dataset_directories": {k: DATASET_FOLDERS[k] for k in keys},
                   "outputs": relative_outputs, "netcdf_variables": netcdf_variables, "status": "complete"})
        # Same filesystem rename: no completed directory before all datasets succeed.
        partial.rename(final)
        emit("complete", 100, result={"directory": str(final), "outputs": relative_outputs, "netcdf_variables": netcdf_variables})
    finally:
        if partial.exists():
            shutil.rmtree(partial)
        provider.auth.clear()
        username = password = None

def main():
    logging.disable(logging.CRITICAL)
    os.environ["COPERNICUSMARINE_DISABLE_SSL_CONTEXT"] = "False"
    # Never allow upstream progress, URLs or exceptions into protocol or parent logs.
    with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        try:
            request = json.loads(sys.stdin.readline())
            run(request)
        except (ImportError, ModuleNotFoundError):
            emit("DEPENDENCY")
            return 2
        except ProviderError as exc:
            emit(exc.code)
            return 3
        except Exception:
            emit("FAILED")
            return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
