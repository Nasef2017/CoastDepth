# CoastDepth — Processing Toolbox usage

Open **Processing → Toolbox → CoastDepth — Copernicus Marine SDB**. Search for CoastDepth or Copernicus. Download tools are native Processing algorithms, with their Short Help on the right; no top toolbar button is installed.

## Setup

At activation the dependency check runs automatically. Use the ERROR dialog's copied commands in OSGeo4W Shell if libraries are missing, then Recheck. **Account, dependencies and help** opens login, the dependency checker, full Help or Forget saved credentials. Existing credentials and worker environment from earlier CoastDepth versions are retained. Optional persistence uses encrypted QGIS Authentication Manager; session credentials remain in memory. Never enter passwords into Processing parameters, models or history.

## Download tools

Choose **Download Optical RTE**, **Download Wave Kinematics**, **Download Intertidal**, or **Download all three Copernicus SDB datasets**. Each clearly identifies Copernicus Marine as its data source. The right-side Short Help and Help button contain dataset IDs, shared parent-product DOI, attribution, licence links and source documentation.

Parameters:

| Parameter | Meaning |
|---|---|
| ROI layer | A QGIS layer with a correct, defined CRS |
| ROI mode | Polygon mask or rectangular Extent from layer |
| Selected Features only | Restrict polygon/extent to selected features in a vector layer; empty selection is an error |
| Saved output format | NetCDF + GeoTIFF, GeoTIFF or NetCDF |
| Output parent folder | Parent for a unique, completed run folder |
| Time limit | Overall worker timeout in minutes |
| Add Height layers to QGIS | Add only bathymetry; quality/method metadata remain saved |

ROI is snapshotted and transformed before background processing. A geographic ROI wider than 180 degrees must be split at the dateline. Invalid geometries, no-data output and oversized requests fail clearly. Polygons preserve holes and pixel-center masking. The provider downloads official spatial subsets, validates actual variables and exports without changing signs or datum.

Processing's progress and Cancel control the independent worker. Transient network failures are retried; run the algorithm again after correcting a permanent failure. The safe log is saved for success, failure, cancellation and timeout. Completed outputs are published after all requested datasets succeed. Partial staging is cleaned on failure/cancel; prior completed runs are retained.

## Outputs

```text
output-parent/
  coastdepth_<uuid>.jsonl
  coastdepth_<uuid>/
    manifest.json
    Optical_RTE/              similarly Wave_Kinematics/ and Intertidal/
      bathymetry.nc           when selected; includes available variables
      height.tif              when GeoTIFF selected
      Quality_indicator.tif   when GeoTIFF selected
      SDB_type.tif            if supplied and GeoTIFF selected
      provenance.json
```

Only height/elevation sources are added, with readable method names. When both formats are saved, GeoTIFF is loaded to avoid duplicate height layers. NetCDF-only loads the height variable subdataset. Quality/method rasters can be added manually from disk. Existing project layers and old output directories are never automatically removed or renamed.

Processing returns the completed run folder, safe-log path and Height source paths. Provenance retains source attributes, dataset ID/version, actual method/units/datum/date evidence when available, software versions, citation, licence and hashes. Null means unavailable, and documented product-wide image periods are separate from observed file evidence. Read the Short Help or [full Help](HELP.html) for the product citation. Data are not for navigation.

For batch/model/headless runs, unlock saved QGIS credentials beforehand; there is no password parameter. A headless run without unlocked saved credentials fails with instructions instead of prompting. Interactive account setup requires QGIS desktop. Real authenticated batch/model execution has not been tested in this release.
