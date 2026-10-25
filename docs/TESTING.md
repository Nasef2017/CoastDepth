# Test and release validation — 24 October 2026

The initial validation below describes the 0.2.0 implementation, with a correctly structured local installation ZIP and offscreen tests using the actual installed QGIS 4.0.2 / Qt6 runtime. The user's open project and installed plugin were not modified by these tests.

## Executed checks

- QGIS 4.0.2 offscreen tests (14 passed) include automatic startup dependency checking without a click, missing-package error text, copied commands, download gating and quiet healthy startup. They also cover plugin construction/lifecycle, main dialog, Login dialog/password mode, modal dialog execution, missing-dependency dialog, polygon hole snapshot, empty/selected features, extent snapshot, scoped QProcess enums and the real QGIS plugin manager's version-acceptance function. See `qgis4-test-results.txt`.

- A disposable private Python 3.12.1 environment was created using the same dependency bootstrap shipped in the plugin. Setup succeeded without modifying global Python or QGIS.
- The dependency probe imported the real packages and reported ready: copernicusmarine 2.4.0, NumPy 2.5.4, xarray 2026.9.0, netCDF4 1.7.5.1.post1 and rasterio 1.5.2. Exact resolved versions are environment-specific, not a cross-platform lock.
- The offline suite verifies bounds, dateline/oversize rejection, secret and URL redaction, allowlisted log exports, transient retry, fixed auth errors, live catalogue schema, legacy elevation and live height, method indicator, ascending/descending coordinates, north-up affine placement, quality classes, masks with holes and multipart geometry, nodata, missing metadata, real attribute preservation, checksums, complete three-method batch output and rollback after a later dataset fails.
- Signature checks import the actual pinned Toolbox; no network/account is used by those tests.
- A separate live metadata check queried the official catalogue through that Toolbox and verified all three requested IDs, version 202511, variables and static-arco service. The sanitized snapshot is included. No marine observation data were downloaded.
- The release builder parses all Python source, validates plugin metadata, checks required files and ZIP integrity, enforces a single top-level plugin directory and excludes caches/environments. SHA-256 sums accompany the release.

The final isolated-environment suite passed **53 tests**, with no skips or failures. Output is recorded in `test-results.txt` alongside this document. An earlier run using the host Python passed the processing tests but skipped Toolbox import checks; the isolated-environment run is the release evidence. One initial transaction test hit Windows sandbox restrictions in the system temporary directory; rerunning with a workspace-owned temporary directory passed.

## Not executed

- Interactive use in the user's running QGIS session, real toolbar/menu integration (the offscreen lifecycle test uses an interface harness), progress/cancel/retry during live downloads, or adding GDAL raster subdatasets to a real project. QGIS 3 runtime tests were not repeated for 0.2.0.
- Real Copernicus username/password validation, encrypted QGIS auth persistence or master-password unlock behavior.
- An authenticated live subset, actual source NetCDF attributes, coverage within a real ROI or scientific comparison with producer values.
- Dependency installation from an actual QGIS-distributed Python executable on Windows/Linux/macOS. The setup path was tested using workspace Python; QGIS distribution differences remain a manual check.
- A hard cancellation during a real transfer, operating-system shutdown, no-disk-space behavior or cleanup of files locked by third-party software.
- Public QGIS plugin repository validation, name/trademark clearance, publication or remote installation.

## Manual acceptance checklist

1. On QGIS 4.0.2 (or QGIS 3.40 with Python 3.12), Install from ZIP and enable the plugin. Run Dependencies with QGIS Python; verify ready state and unchanged global packages.
2. Verify an invalid account, then a real account. Save/reopen credentials with QGIS master password, test session-only mode and Forget.
3. Use a small coastal polygon and all three methods. Repeat with Selected Features, a polygon hole, a MultiPolygon, projected CRS, raster layer extent and an empty selection.
4. Export both formats and inspect height/sign, method flags, quality values, fill values, affine location, source metadata, DOI, licence, version and provenance SHA-256 hashes. Compare against the official subset for identical bounds.
5. Try no-data ROI, no connection, expired credentials, cancellation and timeout. Confirm no completed folder for an incomplete batch and no credential-bearing logs. Retry must create a new run UUID.
6. Reload NetCDF-only and GeoTIFF-only runs into QGIS; disable/unload plugin while a job is running and verify process exit/cleanup. Repeat on supported platforms before declaring a stable release.

## Reproduce

```text
<private-environment-python> tools/run_tests.py
<private-environment-python> tools/live_catalogue_check.py
python tools/build_release.py
```

The live catalogue check needs network access but no account. Authenticated tests need the user's own account inside QGIS; never put credentials into test fixtures, shell arguments, repository files or test reports.

The new dependency tests simulate missing packages, transitive import failures, binary import failures and incompatible versions, and verify exact pip requirements, path quoting, private-environment targeting and repair commands. No libraries were installed by the startup/error-dialog tests. A real manual installation via OSGeo4W Shell has not been executed.

## QGIS private-runtime validation for 0.2.0

The actual user private environment created from QGIS Python 3.12.13 passed all 53 core/contract/dependency/runtime-path tests. Its dependency probe returned ready=true for Copernicus Marine 2.4.0, NumPy 2.5.4, xarray 2026.9.0, netCDF4 1.7.5.1.post1, rasterio 1.5.2 and packaging 26.3. The reproduced failure before the fix was ImportError for the standard-library _sqlite3 DLL. No marine data or account login was used. Four new tests cover verified QGIS DLL paths, ordinary Python paths, idempotence/handle lifetime and unavailable paths.

## Height-only layer loading in 0.2.0

Four additional QGIS 4.0.2 tests use actual GDAL GeoTIFF and NetCDF layers. They verify one height layer per requested method, clear names, no duplicate height layers when both formats are saved, legacy elevation/short-folder compatibility, and byte-for-byte preservation of every saved file. The QGIS suite passes 14 tests; the private-runtime processing suite passes 53. No real marine data or user project was used by the tests.

## CoastDepth 0.2.0 Processing migration

For the subsequent 0.2.1 local audit, 59 private-runtime tests and 17 QGIS 4.0.2 offscreen tests passed. Bandit reported four reviewed low-severity subprocess findings and no medium/high findings; detect-secrets reported none. Flake8 retains informational style findings. The full environment vulnerability audit identified old pip 25.0.1; version 0.2.1 adds a private pip upgrade before manual/advanced dependency installation, but the existing environment was not updated by the audit. The 72 runtime distributions excluding pip had no known advisories. Missing publication email/public repository links remain unresolved. Raw audit evidence accompanies this release outside the plugin ZIP.

The private-runtime suite passes 58 tests, including five new tests with actual child processes for stdin-only credentials, fixed auth messages, untrusted-protocol suppression, cancellation cleanup and timeout. The QGIS 4.0.2 suite passes 17 tests: native provider registration/removal, all five algorithms and citations, real Processing dialog construction, parameter preparation and postprocessing with synthetic worker results, height-only GeoTIFF/NetCDF layer loading and earlier ROI/dependency checks. No toolbar action is registered. An authenticated download, real remote cancellation and live batch/model workflows have not been run for this update.

## English-only distribution (0.2.2)

The README was translated into English. Authored interface labels, messages, help, documentation links and workflow labels were reviewed. A release guard scanned 56 UTF-8 text files, including HTML entities, decoded JSON and Python string literals, and found no letters outside the English alphabet. The guard does not detect foreign words written with English letters; wording was reviewed separately. The existing workflow PNG was visually checked. The actual QGIS 4.0.2 offscreen suite passed all 17 checks after the language update. No live account download was performed. Native QGIS/OS widgets follow the host application language; source metadata and user-provided names remain unchanged. Older archived releases retain their historical content.

## CoastDepth naming consistency (0.2.4)

The project consistently uses CoastDepth in source, interface labels, notices, settings and generated output/log names. The private worker environment was relocated to the CoastDepth application data directory, recreated with the matching QGIS base Python, and its 15 console entry points were regenerated. Stored authentication configuration identifiers were migrated without exporting credential values. All 59 private-runtime tests and 17 QGIS 4.0.2 integration tests passed after these changes. No live authenticated download was performed.

## Release presentation (0.2.5)

Dialog titles, help content, metadata and provenance release status were verified with 59 private-runtime tests and 17 QGIS 4.0.2 integration tests, all passing. README links were verified, the English-only text guard passed, and the updated workflow PNG was visually inspected. Processing help and standalone Help use the same maintained content with full author and documentation credits. No live authenticated download was performed for this update; the user has separately reported successful interactive use.
