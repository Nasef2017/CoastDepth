# Licences and third-party attribution

## Plugin code

CoastDepth source, documentation, original icon and workflow artwork are distributed under **GPL-3.0-or-later**. See LICENSE and complete COPYING. No Bathymetrix-AI source, images, code or modules are imported or bundled. The workflow is independently implemented for this project. No Copernicus or QGIS logos are reproduced as the plugin icon.

## Marine data

Downloaded data retain the **Copernicus Marine Service licence**. The authoritative [English agreement](https://marine.copernicus.eu/user-corner/service-commitments-and-licence) is linked from the product page and was checked on 24 October 2026. Its permissions include reuse, modification and redistribution subject to its terms. Credit with the product DOI, preserve traceability, and propagate applicable obligations when redistributing. Do not represent the data licence as the GPL or invent a CC BY identifier. The plugin records the live source's licence attributes when supplied and the agreement reference separately.

The producer explicitly excludes navigation use. [Product information](https://data.marine.copernicus.eu/product/BATHYMETRY_GLO_PHY_COASTAL_L4_MY_016_001/description) and [PUM](https://documentation.marine.copernicus.eu/PUM/CMEMS-GLO-PUM-SDB-016-001.pdf) provide scientific limitations. The software does not improve or independently validate the producer's scientific estimates.

The sanitized live catalogue snapshot is Copernicus Marine Service information redistributed for verification. Redistribution credit: E.U. Copernicus Marine Service Information; https://doi.org/10.48670/mds-00364. Data ownership is not transferred by the plugin licence.

## Runtime packages

Third-party libraries are installed externally in the user's private environment, not bundled in the plugin ZIP. Preserve their notices if redistributing that environment. This table identifies the direct components; their installed package metadata and licence files are authoritative, including transitive packages and binary dependencies.

| Component | Licence / notice source |
|---|---|
| Copernicus Marine Toolbox 2.4.0 | EUPL-1.2, verified from the actual wheel's METADATA/LICENSE.txt; https://github.com/mercator-ocean/copernicus-marine-toolbox |
| NumPy | BSD-3-Clause; https://numpy.org/doc/stable/license.html |
| xarray | Apache-2.0; https://github.com/pydata/xarray/blob/main/LICENSE |
| netCDF4 Python | MIT; https://github.com/Unidata/netcdf4-python |
| rasterio | BSD-3-Clause; https://github.com/rasterio/rasterio/blob/main/LICENSE.txt |
| packaging | Apache-2.0 OR BSD-2-Clause; https://github.com/pypa/packaging/blob/main/LICENSE |
| QGIS/PyQGIS and PyQt | Supplied and licensed by the QGIS distribution; not redistributed here |

The software citation names contributors generically until the user supplies actual authorship/maintainer details. No trademark clearance or public repository registration is claimed.
