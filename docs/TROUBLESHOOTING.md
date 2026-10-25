# Troubleshooting

| Symptom / code | Action |
|---|---|
| DEPENDENCY / worker does not start | Open Dependencies; verify QGIS Python 3.10+, choose python.exe, copy the listed pip install commands into OSGeo4W Shell, then Recheck libraries. |
| SETUP / pip fails | Check internet, HTTPS certificates, writable profile directory, disk space and binary-wheel support. Use INSTALL.md's manual instructions. No SSL bypass. |
| AUTH | Check Copernicus Marine account/email and password. CDSE browser SSO is not implemented as a Toolbox password substitute. Use Login/change account; saved credentials can be replaced or forgotten. |
| NETWORK | Check service notifications and network/proxy availability. The adapter retries recognized transient errors; Retry last request repeats the snapshot with a new UUID. |
| SCHEMA | Verify dataset variables/current catalogue. Keep the source product version and provenance where available. A source grid with fewer than two centers per axis cannot be exported reliably; enlarge a very small ROI. |
| FAILED | Check writable output, free space, ROI coastal coverage and memory. If no valid bathymetry exists for any requested dataset, the batch fails; try each method separately. |
| Cancel does not instantly remove a folder | The child must exit before Windows releases files. A locked file may prevent cleanup. Close readers and remove only the hidden partial directory matching that run UUID. |
| QGIS exited during download | A `.coastdepth_partial_<uuid>` folder may remain. It is incomplete and can be removed after confirming no job is using it. A complete run has a `manifest.json` and a non-partial folder. |
| NetCDF valid but layer does not load | Ensure QGIS's GDAL has NetCDF support; open the variable subdatasets manually or choose GeoTIFF. QGIS layer loading does not change saved results. |
| Wrong location | Confirm the source layer CRS and coordinate transform settings. Do not assign a guessed CRS. |
| Selected Features gives no ROI | Select features in the chosen vector layer or disable Selected Features. Empty selection never silently uses every feature. |
| Invalid ROI / dateline | Repair invalid polygons, split dateline-crossing areas, or reduce very large regions. |
| Missing image dates/datum/method in summary | Inspect source_global_attributes and source_variables. Null means the file does not supply a recognized attribute; documentation context is kept separately. |
| Quality classes unexpected | Retain producer flags, inspect QUID, and avoid interpolating class values. No class reinterpretation is applied. |

The safe exported log intentionally excludes arbitrary upstream diagnostics. It identifies the failure category without exposing account details, authentication headers or proxy URLs. For maintainer reports, include plugin/QGIS/Python versions, dataset IDs, failure code, and a non-sensitive small ROI. Do not send passwords, auth databases, private proxy settings or unsanitized tracebacks.

Startup ERROR lists MISSING, IMPORT ERROR and INCOMPATIBLE VERSION separately. All packages are listed if the private worker environment has not been created. The healthy QGIS global environment is not the worker environment; installing libraries in unrelated Python will not satisfy the check.

If copernicusmarine reports IMPORT ERROR despite being installed on Windows, upgrade to 0.2.0 for the QGIS/sqlite3 DLL bootstrap fix. sqlite3 is part of Python; do not try pip install sqlite3. If a bare global pip install caused botocore/aiobotocore version conflicts, inspect actual installed requirements and restore a compatible set with your administrator; the plugin never changes global package versions itself.
