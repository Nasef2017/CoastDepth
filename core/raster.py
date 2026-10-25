"""Regular geographic grids only; no inferred datum, resampling or sign changes."""
from pathlib import Path
import numpy as np
import xarray as xr
import rasterio
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
from .catalogue import select_variables
from .provider import ProviderError
from .security import scrub, SENSITIVE

def safe_attributes(attributes, secrets):
    # Preserve numeric scientific attributes (including arrays and dtypes).
    return {key: ("[redacted]" if SENSITIVE.search(str(key)) else
                  scrub(value, secrets) if isinstance(value, str) else value)
            for key, value in attributes.items()}

def spatial_grid(ds):
    axes = {}
    for axis, standard, candidates in (("x", "longitude", ("lon", "longitude")),
                                       ("y", "latitude", ("lat", "latitude"))):
        names = [n for n in ds.coords if ds[n].attrs.get("standard_name") == standard]
        if not names:
            names = [n for n in candidates if n in ds.coords]
        if len(names) != 1 or ds[names[0]].ndim != 1:
            raise ProviderError("SCHEMA")
        axes[axis] = names[0]
    x, y = axes["x"], axes["y"]
    if ds[x].dims != (x,) or ds[y].dims != (y,):
        raise ProviderError("SCHEMA")
    ds = ds.sortby(x).sortby(y, ascending=False)
    lon, lat = ds[x].values, ds[y].values
    # A single cell gives no measured spacing: fail instead of guessing.
    if len(lon) < 2 or len(lat) < 2 or not np.isfinite(lon).all() or not np.isfinite(lat).all():
        raise ProviderError("SCHEMA")
    dx, dy = np.diff(lon), -np.diff(lat)
    if (not (dx > 0).all() or not (dy > 0).all() or
            not np.allclose(dx, dx[0], rtol=1e-5, atol=1e-9) or
            not np.allclose(dy, dy[0], rtol=1e-5, atol=1e-9) or
            lon.min() < -180 or lon.max() > 180 or lat.min() < -90 or lat.max() > 90):
        raise ProviderError("SCHEMA")
    transform = from_origin(float(lon[0] - dx[0]/2), float(lat[0] + dy[0]/2),
                            float(dx[0]), float(dy[0]))
    return ds, x, y, transform

def export_subset(source, directory, polygon=None, formats=("netcdf", "geotiff"), tags=None, secrets=()):
    directory = Path(directory)
    outputs = []
    with xr.open_dataset(source) as raw:
        try:
            variables = select_variables(raw.data_vars)
        except ValueError:
            raise ProviderError("SCHEMA") from None
        ds, x, y, transform = spatial_grid(raw)
        for var in variables:
            if set(ds[var].dims) != {x, y} or ds[var].ndim != 2:
                raise ProviderError("SCHEMA")
        # CF scalar mapping variables remain attached when supplied.
        mapping_names = {ds[v].attrs.get("grid_mapping") for v in variables}
        keep = list(variables) + [n for n in mapping_names if n and n in ds and n not in variables]
        ds = ds[keep].load()
        ds.attrs = safe_attributes(ds.attrs, secrets)
        for name in ds.variables:
            ds[name].attrs = safe_attributes(ds[name].attrs, secrets)
        if polygon:
            mask = geometry_mask([polygon], out_shape=(ds.sizes[y], ds.sizes[x]),
                                 transform=transform, invert=True, all_touched=False)
            if not mask.any():
                raise ValueError("Polygon contains no pixel centers.")
            mask_da = xr.DataArray(mask, dims=(y, x), coords={y: ds[y], x: ds[x]})
            for var in variables:
                ds[var] = ds[var].where(mask_da)
        if not np.isfinite(ds[variables[0]].values).any():
            raise ValueError("No bathymetry data in ROI.")
        if "netcdf" in formats:
            path = directory / "bathymetry.nc"
            encoding = {}
            for var in variables:
                # Preserve original storage dtype, flag values and source fill value.
                original = raw[var].encoding
                dtype = original.get("dtype", ds[var].dtype)
                fill = original.get("_FillValue", np.nan)
                if np.issubdtype(np.dtype(dtype), np.integer) and (fill is None or not np.isfinite(fill)):
                    dtype, fill = "float32", np.nan
                encoding[var] = dict(dtype=dtype, _FillValue=fill, zlib=True, complevel=4)
                for field in ("scale_factor", "add_offset"):
                    if field in original:
                        encoding[var][field] = original[field]
                ds[var].encoding = {}
            ds.to_netcdf(path, engine="netcdf4", encoding=encoding)
            outputs.append(path)
        if "geotiff" in formats:
            for var in variables:
                path = directory / (var + ".tif")
                # Float32 supports NaN, exact small quality classes, and source depths.
                values = ds[var].transpose(y, x).values.astype("float32")
                with rasterio.open(path, "w", driver="GTiff", width=ds.sizes[x], height=ds.sizes[y],
                     count=1, dtype="float32", crs="EPSG:4326", transform=transform,
                     nodata=np.nan, compress="deflate", tiled=True) as raster:
                    raster.write(values, 1)
                    raster.set_band_description(1, var)
                    raster.update_tags(**(tags or {}))
                    raster.update_tags(1, **{k: str(v) for k, v in ds[var].attrs.items()})
                outputs.append(path)
        return outputs
