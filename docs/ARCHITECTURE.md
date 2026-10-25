# Architecture

```text
plugin.py        native Processing provider registration and lifecycle
ui.py            dialogs, nonblocking QProcess, protocol, completion, layer loading
auth.py          QGIS Authentication Manager; QSettings stores authcfg ID only
roi.py           GUI-thread layer snapshot, selection, geometry, CRS transform
dependencies.py  isolated runtime probe, package issue lists, safe shell commands
dependency_ui.py  automatic activation check, ERROR dialog, copy commands, recheck gate
worker.py        child entrypoint, transactional staging, protocol and safe failures
core/catalogue.py     product registry, variables, DOI
core/models.py        bounded geographic request model
core/provider.py      official Toolbox adapter, login, catalogue validation, retry
core/raster.py        CF grid validation, local polygon mask, exports
core/provenance.py    actual metadata, documented context, checksums
core/security.py      recursive secret and signed-URL scrubbing
core/events.py        allowlisted structured logging
```

The GUI uses only QGIS and the Python standard library. A subprocess created from a private environment owns all remote I/O and scientific imports. Using a separate process prevents NumPy 2 dependencies from replacing QGIS's NumPy or other plugin libraries. Communication is one JSON request through an anonymous stdin pipe and newline JSON stage events through stdout. There is no local HTTP server or listening port.

ROI reads and all QGIS objects remain on the GUI thread. The worker receives a geometry dictionary and bounds, never a QgsLayer reference. A layer change during download therefore cannot mutate the current request. Main-thread layer creation happens after successful completion.

For each requested method: validate live product/dataset identity and discover variable names → official `subset` requesting bathymetry, quality and available method indicator → validate source grid/variables → optional local polygon mask → export → provenance. The request is spatial only because the product is static. No unsupported acquisition date filter is sent.

Each run uses a UUID. Files live in a same-filesystem `.coastdepth_partial_<uuid>` directory until every dataset succeeds. A single directory rename publishes a completed batch. Errors roll back staging. The parent kills a cancelled process and cleans only that run's verified staging directory. Previous completed outputs are never overwritten. A process or machine crash may leave a partial directory; it has no complete manifest and is documented in troubleshooting.

Progress reflects stages, not byte counts. Retry applies to recognized transient network exceptions/statuses; auth/schema/programming errors require a correction. The UI has a separate overall timeout. Third-party internal retry behavior is outside the stage percentages. No background threads touch QWidget/QgsProject objects.

## Extension points

Add dataset definitions to the registry, a dedicated schema/variable mapping to the provider, and fixtures for its actual CF structure. The raster exporter intentionally rejects time dimensions, curvilinear grids and irregular spacing rather than guessing. Add separate exporters/providers for those data models. Do not loosen the scientific schema merely to make a different product pass.

New output formats belong in an exporter module, not the GUI. If adding per-pixel observation dates, extract only documented variables and their real calendar/units. If new Toolbox API versions are adopted, update the exact pin, signature tests, live metadata smoke test and release validation record together.

## Activation dependency gate (0.2.0)

initGui schedules a dependency check on the event loop. Missing or incompatible packages produce an automatic ERROR dialog with their names and quoted pip install commands for OSGeo4W Shell. Healthy startup shows no dialog. Downloader access waits for a successful check. No package installation is triggered by plugin activation. Probe timeouts and process failures produce fixed diagnostics; unload stops pending checks.

The runtime_paths module prepares native DLL lookup in Windows children before Copernicus/scientific imports. QGIS venvs inherit their base Python standard library but not the global site-package startup hooks that normally register the QGIS bin directory. The bootstrap registers only the matching base installation DLL directories, retains their handles and leaves Python module isolation intact.

## Native Processing provider (0.2.0)

plugin.py registers provider coastdepth with four native download algorithms and one setup/help algorithm. It creates no toolbar or Plugins-menu action. processing_provider.py captures layer geometry and credentials in prepareAlgorithm on the main thread, executes an independent child in processAlgorithm, and adds height layers during postProcessAlgorithm. core/runner.py feeds credentials only through stdin, forwards allowlisted events to Processing feedback, supports cancellation/timeout and exports safe logs. help_content.py supplies both Short Help and standalone HELP.html from one source. The prior FetchDialog remains an internal compatibility helper, not a registered entry point. Internal package/settings/environment names remain stable across the rename.
