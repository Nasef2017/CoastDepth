# Official-source verification — 24 October 2026

## Product and IDs

The official [product page](https://data.marine.copernicus.eu/product/BATHYMETRY_GLO_PHY_COASTAL_L4_MY_016_001/description) identifies the product and DOI. The [access page](https://data.marine.copernicus.eu/product/BATHYMETRY_GLO_PHY_COASTAL_L4_MY_016_001/services) lists these datasets and Subset/Files/Maps services:

| Method | Exact dataset ID |
|---|---|
| Optical RTE | `cmems_obs-sdb_glo_phy_irte_my_100m-l4-s2_static` |
| Wave Kinematics | `cmems_obs-sdb_glo_phy_wk_my_100m-l4-s2_static` |
| Intertidal | `cmems_obs-sdb_glo_phy_it_my_100m-l4-s2_static` |

The merged `comp` dataset is outside this plugin's scope. Secchi depth is also outside scope.

Product DOI: [10.48670/mds-00364](https://doi.org/10.48670/mds-00364). Product title: Global coastal satellite derived bathymetry static.

## Live catalogue check

The project ran the actual pinned official Toolbox **2.4.0** against the live catalogue, without credentials or a marine data download. The sanitized result is saved in [live_catalogue_verified.json](live_catalogue_verified.json). All requested IDs were found under the correct product. At verification time they exposed version **202511**, a `static-arco` subset service, variables **height**, **Quality_indicator**, and **SDB_type**, and geographic longitude/latitude coordinates.

The manual's example header uses `elevation`; the live service uses `height`. The provider therefore discovers variable names from live static-arco metadata for each run, accepts exactly one of those two bathymetry names, retains the original name, requires quality and includes the method variable when offered. Unsupported/ambiguous schemas fail visibly. No API calls assume that a human-readable catalogue variable label is its short name.

## Methods, datum and dates

The [Product User Manual, Issue 1.0, November 2025](https://documentation.marine.copernicus.eu/PUM/CMEMS-GLO-PUM-SDB-016-001.pdf) documents the three methods, a static product, MSL referencing using FES 2014, and an upstream Sentinel-2 period of 2019–2024. These are product-wide documentation facts. Individual image acquisition dates are not inferred from them. Units and source attributes are read from actual output files. Refer to [QUID](https://documentation.marine.copernicus.eu/QUID/CMEMS-GLO-QUID-SDB-016-001.pdf) for method and validation details.

The manual and catalogue do not guarantee complete coverage within every coastal ROI. Output values and their signs are retained. Do not relabel signed height as positive-down depth without a separately justified conversion.

## Access and authentication

The [official Toolbox Python API](https://toolbox-docs.marine.copernicus.eu/en/v2.4.0/python-interface.html) supplies `describe`, `login(check_credentials_valid=True)` and `subset`. The package's actual function signatures were tested locally. [Login documentation](https://toolbox-docs.marine.copernicus.eu/en/stable/usage/login-usage.html) explains verification-only behavior. [Official access guidance](https://help.marine.copernicus.eu/en/articles/16733110-how-to-access-and-download-copernicus-marine-data) describes subset and file services.

The plugin uses official spatial subset, then performs local polygon masking. It does not use legacy MOTU URLs, scrape map tiles, or request the global original files. It does not implement browser/CDSE SSO; a username/password accepted by the Marine Toolbox is required. No successful real account login or authenticated data download was performed during development.

## Licence and citation

The product links the [Copernicus Marine Service Commitments and Licence](https://marine.copernicus.eu/user-corner/service-commitments-and-licence). The English agreement was retrieved successfully by HTTPS after the web preview returned 403. Its annex permits copying, adaptation and redistribution under its terms; attribution/DOI credit and traceability obligations are part of those terms. It is a dedicated Copernicus Marine licence, not a general assertion that all these data are CC BY.

[Official citation guidance](https://help.marine.copernicus.eu/en/articles/4444611-citing-copernicus-marine-products-and-services) distinguishes product DOI citation, redistribution credit, derivative credit and publication acknowledgement. See CITATIONS.md and LICENSES.md. The live agreement remains authoritative if revised.

## Verification boundaries

Verified: catalogue IDs, current variable names and subset service, official DOI/licence links, public licence text, installed Toolbox API signatures, synthetic processing and offscreen QGIS 4.0.2 dialog/ROI/lifecycle compatibility in release 0.2.0. Not verified: credentials for a real account, actual authenticated subset content, interactive behavior/auth persistence/layer loading in the user's QGIS project, platform-specific dependency installation from QGIS Python, or archive acceptance by the public QGIS plugin repository. The ZIP is structured for local Install from ZIP; it has not been published or officially endorsed.
