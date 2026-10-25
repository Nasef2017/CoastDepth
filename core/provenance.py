import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path
import xarray as xr
from .catalogue import PRODUCT, DATASETS, DOI, LICENCE, PUM, citation
from .security import scrub
from ..brand import VERSION, RELEASE_STATUS

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def provenance(source, catalogue, key, bounds, polygon, response, outputs, secrets=()):
    with xr.open_dataset(source) as ds:
        attrs = dict(ds.attrs)
        variables = {name: {"dimensions": list(v.dims), "attributes": dict(v.attrs),
                     "storage": {k: v.encoding[k] for k in ("dtype", "_FillValue", "scale_factor", "add_offset") if k in v.encoding}}
                     for name, v in ds.variables.items()}
        # These fields deliberately remain null unless present in the file itself.
        def first(*names):
            return next((attrs[n] for n in names if n in attrs), None)
        observed = dict(source=first("source", "platform"),
            image_dates=first("image_dates", "acquisition_dates", "acquisition_date"),
            temporal_coverage={n: attrs[n] for n in ("time_coverage_start", "time_coverage_end") if n in attrs},
            method=first("method", "processing_method"),
            datum=first("vertical_datum", "geospatial_vertical_datum"),
            citation=first("citation", "references"), licence=first("licence", "license"))
    now = datetime.now(timezone.utc)
    versions = {}
    for name in ("copernicusmarine", "xarray", "numpy", "rasterio", "netCDF4"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not installed"
    raw_response = response.model_dump(mode="json") if hasattr(response, "model_dump") else response
    return scrub({"schema_version": 1, "plugin": {"name": "CoastDepth", "version": VERSION,
                                                "release_status": RELEASE_STATUS},
        "retrieved_utc": now.isoformat(), "product_id": PRODUCT, "dataset_id": DATASETS[key][1],
        "dataset_name": DATASETS[key][0],
        "request": {"bounds_epsg4326": vars(bounds), "polygon": polygon, "pixel_rule": "center inside polygon",
                    "coordinates_selection_method": "inside"},
        "observed_file_metadata": observed, "source_global_attributes": attrs,
        "source_variables": variables, "live_catalogue": catalogue, "toolbox_response": raw_response,
        "documentation_context": {"source": PUM, "checked_on": "2026-10-24",
            "method": DATASETS[key][0], "datum": "Mean Sea Level (FES 2014)",
            "units": "metres (bathymetry); dimensionless (quality)",
            "upstream_image_period": ["2019-01-01", "2024-12-31"],
            "note": "Product-wide documentation period, not per-pixel acquisition dates. Keep original sign."},
        "citation": citation(now.date().isoformat()), "product_doi": DOI,
        "licence_reference": LICENCE,
        "attribution": "Generated using E.U. Copernicus Marine Service Information; " + DOI,
        "processing": ["Official bounding-box subset", "Optional local polygon mask", "No resampling or vertical transformation"],
        "software_versions": versions,
        "files": [{"name": Path(p).name, "sha256": sha256(p)} for p in outputs],
        "missing_metadata_policy": "null means unavailable in source; no image dates inferred from static label or retrieval date"}, secrets)

def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
