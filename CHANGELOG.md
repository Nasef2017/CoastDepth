# 0.2.5 — 2026-10-24

- Public release prepared for QGIS Python Plugins Repository and GitHub publication.
- Transition from experimental status to stable release; remove experimental tags across metadata, dialog titles, help and documentation.
- Add authorship and vibe coding credits (Developed by Mohamed Aly Nasef; documentation and vibe coding by ChatGPT).
- Configure repository and issue tracker endpoints.

# 0.2.4 — 2026-10-24

- Use CoastDepth consistently in notices, documentation, Python class names, settings, logs and output folders.
- Store the private Python environment under the CoastDepth application data directory.

# 0.2.3 — 2026-10-24

- Rename the source project folder to CoastDepth and the QGIS plugin package to coastdepth.
- Update worker imports, tests, documentation links and ZIP structure to the new package name.
- Keep dependency setup and authentication separate from the plugin installation folder.

# 0.2.2 — 2026-10-24

- Translate the complete README into English, including instructions, dataset descriptions and documentation links.
- Review authored interface text, help, documentation and workflow labels for English-only distribution.
- Check release text for non-English alphabetic characters, including escaped text, before packaging.

# 0.2.1 — 2026-10-24

- Declare required packages, personal account and tested platform in About metadata.
- Complete packaging licence attribution and catalogue redistribution credit.
- Use the shared software version in provenance and remove unused imports.
- Include the project copyright notice and software licence.
- Public submission still requires real maintainer details and public repository links.
- Upgrade the private pip installer before dependency installation in copyable commands and the advanced setup helper; no automatic installation.

# 0.2.0 — 2026-10-24

Rename to CoastDepth — Copernicus Marine SDB. Replace toolbar/menu access with a native Processing provider: three individual dataset algorithms, one combined download algorithm and account/dependencies/help setup. Add full source attribution, dataset IDs, shared product DOI citation and licence links to every Short Help and standalone Help, and rewrite README/usage. Preserve height-only layers, source data, authentication and private libraries. Add a background worker bridge with native progress/cancel and safe logs.

# 0.1.4 — 2026-10-24

Automatically add only bathymetry height layers to QGIS, for GeoTIFF and NetCDF. Quality, method indicators and metadata remain saved on disk. Use readable layer names and Optical_RTE, Wave_Kinematics, Intertidal output folders. Preserve original dataset IDs in provenance and add human-readable names; legacy short folder names still display clearly when loading older outputs. Tested with real QGIS GDAL layers for both formats, duplicate avoidance and unchanged saved files. Existing project layers and prior output folders are not modified.

# 0.1.3 — 2026-10-24

Fix Copernicus import in Windows venvs created from QGIS Python. Register the base Python DLL directory and the verified QGIS installation bin directory using os.add_dll_directory, retaining handles for the process lifetime. This makes the standard-library sqlite3 dependency available without importing QGIS global Python packages. Validated with ready=true and 53 tests in the actual private QGIS Python 3.12.13 environment.

# 0.1.2 — 2026-10-24

Check dependencies automatically at activation. Show a missing-library ERROR with explicit package names, version/import failure categories and copyable pip install commands for OSGeo4W Shell. Block downloader access until Recheck succeeds. Installation is manual in the private worker environment; activation never installs packages. Add packaging as an explicit version-check dependency and tests for startup/gating/commands.

# 0.1.1 — 2026-10-24

Fix QGIS 4.0 compatibility: declare support through 4.0.x, import QAction from QtGui on Qt6, use scoped Qt and QGIS enums, and support Qt6 dialog execution. Tested offscreen with the actual installed QGIS 4.0.2 runtime. Added a QGIS smoke-test runner and plugin-manager compatibility regression check. No user project or installed runtime changes.

# 0.1.0 — 2026-10-24

Initial release. Standalone QGIS interface, polygon/extent/selection ROI, official Copernicus Marine subset adapter, live variable discovery, optional method indicator, private worker environment, encrypted QGIS authentication, stage progress/cancel/retry, safe JSONL logging, NetCDF/GeoTIFF export, provenance, workflow diagrams and documentation.

Validated using 39 offline/installed-package tests and a live public catalogue check. QGIS interface and authenticated downloads await manual acceptance; see docs/TESTING.md.
