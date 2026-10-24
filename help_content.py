"""One maintained source for native Processing Short Help and standalone Help."""
from html import escape
from .brand import DISPLAY_NAME, VERSION
from .core.catalogue import DATASETS, DATASET_DESCRIPTIONS, PRODUCT, PRODUCT_URL, DOI, LICENCE, PUM

def short_help(keys, settings=False):
    rows = "".join("<li><b>" + escape(DATASETS[k][0]) + "</b>: " + escape(DATASET_DESCRIPTIONS[k]) +
                   "<br>Dataset ID: <code>" + escape(DATASETS[k][1]) + "</code></li>" for k in keys)
    intro = ("Choose an action to sign in to Copernicus Marine, check required libraries, or open the full help. "
             "Saved passwords use encrypted QGIS Authentication Manager. No passwords enter Processing parameters or history."
             if settings else
             "Choose an ROI layer, polygon mask or layer extent, and optionally Selected Features only. "
             "Select an output folder and format, then Run. Sign in when asked. "
             "Progress, Cancel and safe error messages use the native Processing dialog. "
             "Transient network errors are retried; a failed run can be run again with a new run folder.")
    return ("<h2>" + DISPLAY_NAME + "</h2>"
        "<p><b>Version " + VERSION + "</b></p>"
        "<p><b>Data source: E.U. Copernicus Marine Service.</b> This independent plugin retrieves existing "
        "Copernicus Marine coastal satellite-derived bathymetry (SDB); it does not generate a new SDB estimate "
        "and is not an official or endorsed Copernicus application.</p>"
        "<h3>Datasets</h3><ul>" + rows + "</ul>"
        "<h3>How to use</h3><p>" + intro + "</p>"
        "<h3>Outputs</h3><p>Only Height layers are added to QGIS. Quality_indicator, SDB_type when supplied, "
        "NetCDF/GeoTIFF files, metadata/provenance and a safe JSONL log remain in the output folder. "
        "Folders and layers use Optical RTE, Wave Kinematics and Intertidal names. "
        "Polygon holes and nodata are preserved; values, signs and vertical datum are not changed.</p>"
        "<h3>Limitations</h3><p>Static coastal coverage, nominally about 100 m. Availability varies by method and location. "
        "These data are not for navigation. Image acquisition dates are recorded only if supplied by the source; "
        "a documented image period is not treated as per-pixel acquisition evidence. "
        "The dependency check runs at plugin activation; missing packages show OSGeo4W Shell pip instructions. "
        "Libraries run in the private environment.</p>"
        "<h3>Data citation — applies to every dataset above</h3>"
        "<p>Global coastal satellite derived bathymetry static. E.U. Copernicus Marine Service Information (CMEMS). "
        "Marine Data Store (MDS). DOI: <a href=\"" + DOI + "\">10.48670/mds-00364</a>. "
        "Include the actual access date and dataset ID/version from provenance when citing downloaded data.</p>"
        "<p>The DOI identifies the parent product <code>" + PRODUCT + "</code>; "
        "the three datasets do not have separate Copernicus product DOIs.</p>"
        "<h3>Attribution and licence</h3><p>Generated using E.U. Copernicus Marine Service Information; "
        "<a href=\"" + DOI + "\">" + DOI + "</a>.</p>"
        "<p>Data retain the <a href=\"" + LICENCE + "\">Copernicus Marine licence</a>; "
        "the plugin's Apache-2.0 licence does not replace the data terms. "
        "See the <a href=\"" + PRODUCT_URL + "/services\">official product/access page</a>, "
        "<a href=\"" + PUM + "\">Product User Manual</a>, and "
        "<a href=\"https://help.marine.copernicus.eu/en/articles/4444611-citing-copernicus-marine-products-and-services\">official citation guidance</a>.</p>"
        "<h3>Development & Credits</h3>"
        "<p><b>Developed by:</b> Mohamed Aly Nasef</p>"
        "<p>Documentation and vibe coding by ChatGPT.</p>")
