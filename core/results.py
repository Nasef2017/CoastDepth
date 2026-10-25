"""Validate completed-run paths and select only height sources for display."""
from pathlib import Path
from .catalogue import VARIABLES, dataset_display_name

def height_sources(request, result, run_id):
    expected = Path(request["output"]).resolve() / ("coastdepth_" + run_id)
    if Path(result.get("directory", "")).resolve() != expected:
        raise ValueError("Unexpected result directory")
    sources = []
    for relative in result.get("outputs", []):
        path = (expected / relative).resolve()
        if expected not in path.parents or not path.is_file():
            raise ValueError("Invalid result file")
        label = dataset_display_name(path.parent.name) + " — Height"
        if path.suffix == ".tif" and path.stem in ("height", "elevation"):
            sources.append((str(path), label))
        elif path.suffix == ".nc" and "geotiff" not in request["formats"]:
            variables = result.get("netcdf_variables", {}).get(relative, list(VARIABLES))
            for variable in variables:
                if variable in ("height", "elevation"):
                    sources.append(('NETCDF:"' + str(path) + '":' + variable, label))
    return sources
