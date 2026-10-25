# Installation and startup dependency errors

## QGIS installation

Target: QGIS 3.34–3.x with Qt5 or QGIS 4.0.x with Qt6, Python 3.10+. QGIS 4.0.2 has been tested offscreen. Install `CoastDepth-0.2.5-QGIS.zip` through **Plugins → Manage and Install Plugins → Install from ZIP**, then enable the plugin. Replace an older version and restart QGIS if its Python modules remain loaded.

QGIS calls the dependency check at the first activation immediately after installation and at later activations/startups. A ZIP copy itself does not execute Python until QGIS activates the plugin. The check runs in a separate process and does not freeze QGIS. It does not install packages automatically.

## Missing-library ERROR

If the required private environment or any required library is missing, an **ERROR** dialog opens automatically. It lists each missing package by name, distinguishes import failures and incompatible versions, and shows copyable pip commands. Opening the downloader is blocked until **Recheck libraries** succeeds. If everything is ready, startup stays quiet.

1. Open **OSGeo4W Shell** from the QGIS installation / Windows Start menu (sometimes shown as OSGeo4W Shell for QGIS).
2. In the error dialog, verify the selected Python executable belongs to QGIS. Automatic discovery usually finds it; **Choose QGIS Python** can select it manually. Python must be 3.10 or later.
3. Click **Copy pip install commands** and paste the commands into OSGeo4W Shell in the displayed order. Wait for installation to finish successfully.
4. Return to the error dialog and click **Recheck libraries**. If libraries are ready, the startup error closes; open the desired download algorithm under Processing Toolbox → CoastDepth — Copernicus Marine SDB.

The generated commands contain the exact machine-specific paths; copy them from the dialog. For a missing environment they first create a private venv using QGIS Python. They clear shell PYTHONHOME/PYTHONPATH overrides, then run the private interpreter's `-m pip --isolated install` with the required library names and compatible version bounds. A broken import gets `--force-reinstall`; an existing environment otherwise gets commands only for missing/incompatible libraries.

Illustrative command structure (replace paths with the actual copied values; do not paste placeholders):

```bat
"<QGIS Python>" -m venv "<private environment>"
set "PYTHONHOME="
set "PYTHONPATH="
"<private environment>/Scripts/python.exe" -m pip --isolated install --upgrade --disable-pip-version-check --only-binary=:all: --index-url https://pypi.org/simple "pip>=26.2.2"
"<private environment>/Scripts/python.exe" -m pip --isolated install --only-binary=:all: --index-url https://pypi.org/simple "copernicusmarine==2.4.0" "numpy>=2.1,<3" "xarray>=2024.10,<2027" "netCDF4>=1.7,<2" "rasterio>=1.4.3,<2" "packaging>=24"
```

Use the QGIS shell and the exact private interpreter, rather than a bare `pip` that could target another Python. This protects QGIS's own NumPy and other plugin libraries. These shell settings apply only to that shell session. On Linux/macOS the dialog generates POSIX commands and uses `bin/python`; OSGeo4W Shell is a Windows instruction.

Version 0.2.1 adds a first pip command to update **only the private environment's installer** to pip 26.2.2 or newer before installing libraries. Stop if that upgrade fails. This addresses known advisories affecting older pip releases, including wheel extraction and URL handling; see the [official pip changelog](https://pip.pypa.io/en/stable/news/). It does not update pip in QGIS/global Python and does not run automatically. To update an existing environment, run the private-interpreter pip upgrade command shown above, using the actual environment path.

## Libraries checked

| Library | Requirement | Purpose |
|---|---|---|
| copernicusmarine | ==2.4.0 | Official login, catalogue and subset API |
| numpy | >=2.1,<3 | Array operations |
| xarray | >=2024.10,<2027 | CF dataset and attributes |
| netCDF4 | >=1.7,<2 | NetCDF read/write |
| rasterio | >=1.4.3,<2 | GeoTIFF and polygon mask |
| packaging | >=24 | Version compatibility check |

QGIS/PyQGIS/PyQt come from QGIS and are not installed by pip. Other dependencies are resolved by pip. Exact runtime versions are recorded in provenance; direct version bounds are not a complete cross-platform lockfile.

## Environment and repair

The private environment is `<QStandardPaths.AppLocalDataLocation>/coastdepth/worker-v1`; the actual path is visible in the installation commands. It uses no system site packages. Packages are imported only by the worker process, not by QGIS. Installation uses HTTPS official PyPI and binary wheels only; it does not upgrade global pip or modify QGIS's application directory. If binary wheels are unavailable, installation stops instead of compiling source packages. Create the environment at the displayed location; do not move an installed virtual environment manually.

The plugin's Python package and installation folder are `coastdepth`. Install only one copy of CoastDepth. Restart QGIS after upgrading.

For network/certificate/disk-space failures, review the output locally in OSGeo4W Shell, correct the cause, repeat the command, and Recheck. Do not disable TLS verification. Do not share proxy credentials or unreviewed shell output. Unsupported Python versions require a recent QGIS/Python distribution.

The advanced `dependencies.py --setup <environment>` helper remains available for scripted private-environment setup, but it is not run automatically by the plugin. For an incomplete environment that cannot start, close jobs, rename only the displayed worker-v1 folder to a backup, and let the dialog generate fresh-environment commands. Do not remove unrelated QGIS/Python folders.

Uninstalling the plugin preserves outputs and the worker environment. **Forget saved credentials** removes its QGIS authentication entry when requested; authentication is separate from dependency setup.

## Windows sqlite3 DLL import failure

Version 0.2.0 fixes a QGIS-created venv issue where Copernicus is installed but fails to import because the standard-library sqlite3 module cannot find QGIS bin/sqlite3.dll. The private child explicitly registers DLL directories from its own base QGIS installation. It does not enable system site packages, add another plugin to Python paths, or reinstall libraries automatically. Upgrade the plugin and Recheck; repeating pip install is unnecessary when this is the cause.

Always copy the complete installation commands from the dialog. A bare pip install in OSGeo4W Shell targets QGIS global packages and can change shared dependencies such as botocore, whereas the copied command names the private interpreter.

## Upgrade to the CoastDepth Processing interface

The plugin now appears under Processing Toolbox as CoastDepth — Copernicus Marine SDB. Enable the built-in Processing plugin if the Toolbox is unavailable. Restart QGIS after upgrading so the previous toolbar action is unloaded. The internal plugin directory, encrypted authentication configuration key and private worker directory are retained to preserve existing libraries and account settings. The new archive has the same single internal plugin folder and upgrades the existing plugin rather than adding a second copy.
