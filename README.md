# CoastDepth — Copernicus Marine SDB

**QGIS plugin for downloading Copernicus Marine coastal satellite-derived bathymetry.**


CoastDepth provides native QGIS Processing Toolbox tools for retrieving existing **E.U. Copernicus Marine Service** bathymetry products. It is an independent application and is not an official or endorsed Copernicus product. It downloads and exports existing data; it does not calculate new satellite-derived bathymetry estimates.

## What you can try

- Download Optical RTE, Wave Kinematics or Intertidal bathymetry separately, or request all three.
- Define a region of interest using a polygon, a layer extent or selected features.
- Save NetCDF and GeoTIFF files, with only Height layers added automatically to QGIS.
- Retain quality indicators, method information, source metadata, citations and provenance on disk.
- Use QGIS Authentication Manager for optional encrypted credential storage.
- Check dependencies, follow manual installation instructions, and monitor progress or cancel a request.

## Validation and Scope

Local validation of this release passed **59 private-runtime tests** and **17 QGIS 4.0.2 integration tests** on Windows. Successful interactive use has also been reported. These results do not establish compatibility with every QGIS release, platform, dataset extent or service condition.

QGIS 3.34+ compatibility is declared in metadata, but QGIS 3, Linux and macOS have not been validated in the current test environment. Authenticated batch/model runs and behavior during extended service outages remain unverified. Source data can contain gaps and quality limitations. **The data must not be used for navigation.** See [testing](docs/TESTING.md) for the verification scope.

## Getting started

After installing and enabling the plugin, open **Processing → Toolbox** and search for **CoastDepth — Copernicus Marine SDB**. The download tools are available in the Processing Toolbox; no top toolbar button or Plugins menu action is added.

- **Account, dependencies and help**: sign in, check required libraries, open the full help, or remove saved credentials.
- **Download Optical RTE — Copernicus Marine**: retrieve physics-based optical bathymetry derived by inverting the Radiative Transfer Equation.
- **Download Wave Kinematics — Copernicus Marine**: retrieve bathymetry derived from wave kinematics.
- **Download Intertidal — Copernicus Marine**: retrieve bathymetry for intertidal areas between tidal levels.
- **Download all three Copernicus SDB datasets**: retrieve all three datasets for the same region of interest.

Open a download tool, choose an **ROI layer** and either **Polygon mask** or **Extent from layer**, and enable **Selected Features only** when needed. Choose the output format and folder, then click **Run**. The Short Help panel on the right explains the product, parameters, outputs, limitations, licence and citation. The same source information and guidance are available in the [full help](docs/HELP.html).

The plugin checks its dependencies when activated. If libraries are missing or incompatible, an **ERROR** dialog lists them and provides pip commands to copy into **OSGeo4W Shell** on Windows. Complete the installation, then click **Recheck libraries**. Libraries run in a private Python environment. The generated commands update that environment's pip before installing dependencies; packages are not installed automatically. Existing compatible worker environments and saved QGIS account settings are retained. Passwords are never included in Processing parameters or history.

## Copernicus Marine data

Parent product: **Global coastal satellite derived bathymetry static**, product ID `BATHYMETRY_GLO_PHY_COASTAL_L4_MY_016_001`.

| Dataset | Official dataset ID | Product DOI |
|---|---|---|
| Optical RTE | `cmems_obs-sdb_glo_phy_irte_my_100m-l4-s2_static` | [10.48670/mds-00364](https://doi.org/10.48670/mds-00364) |
| Wave Kinematics | `cmems_obs-sdb_glo_phy_wk_my_100m-l4-s2_static` | [10.48670/mds-00364](https://doi.org/10.48670/mds-00364) |
| Intertidal | `cmems_obs-sdb_glo_phy_it_my_100m-l4-s2_static` | [10.48670/mds-00364](https://doi.org/10.48670/mds-00364) |

All three datasets share the parent product DOI. No separate dataset DOIs have been assigned by this plugin. See the [official product and data access page](https://data.marine.copernicus.eu/product/BATHYMETRY_GLO_PHY_COASTAL_L4_MY_016_001/services).

**Data citation:** Global coastal satellite derived bathymetry static. E.U. Copernicus Marine Service Information (CMEMS). Marine Data Store (MDS). https://doi.org/10.48670/mds-00364. Include the actual access date, dataset ID and version recorded in the downloaded provenance.

**Attribution for processed outputs:** Generated using E.U. Copernicus Marine Service Information; https://doi.org/10.48670/mds-00364.

Follow the [official citation guidance](https://help.marine.copernicus.eu/en/articles/4444611-citing-copernicus-marine-products-and-services) and [data licence](https://marine.copernicus.eu/user-corner/service-commitments-and-licence). The plugin's **GPL-3.0-or-later** software licence is separate from the Copernicus Marine data licence.

## Outputs and limitations

Only **Height** layers are added to the QGIS Layers panel, with clear Optical RTE, Wave Kinematics and Intertidal names. Quality indicators, method indicators and metadata remain in the saved output folder. Each completed run has its own folder, containing the `Optical_RTE`, `Wave_Kinematics` and/or `Intertidal` subfolders, provenance, checksums and a safe log. NetCDF and GeoTIFF outputs preserve nodata and polygon holes. Values are exported without changing their sign, units or vertical datum.

The source is a static product with a nominal resolution of approximately 100 m. Coverage varies by location and method. **These data must not be used for navigation.** Image acquisition dates are recorded only when supplied by the source; the product-wide image period is not treated as a per-pixel acquisition date.

## Documentation

[Installation](docs/INSTALL.md) · [Usage](docs/USAGE.md) · [Help](docs/HELP.html) · [Architecture](docs/ARCHITECTURE.md) · [Security](docs/SECURITY.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Citations](docs/CITATIONS.md) · [Sources](docs/SOURCES.md) · [Licences](docs/LICENSES.md) · [Testing](docs/TESTING.md) · [Workflow](docs/workflow.mmd)

## Feedback and development

When reporting a problem, include the plugin version, QGIS version, operating system, selected dataset, ROI mode and a redacted run log. Never share passwords, tokens or unreviewed provenance containing private information. Issues can be opened on [GitHub Issues](https://github.com/Nasef2017/CoastDepth/issues).

## Development & Credits

- **Developed by:** Mohamed Aly Nasef ([eng.m.nasef2017@gmail.com](mailto:eng.m.nasef2017@gmail.com))
- **AI Assistance:** Documentation and vibe coding by ChatGPT.

## Licence

The software is distributed under **GPL-3.0-or-later**. Copernicus Marine data retain their own licence and attribution requirements. See [LICENSE](LICENSE), [COPYING](COPYING) and [third-party licences](docs/LICENSES.md).
