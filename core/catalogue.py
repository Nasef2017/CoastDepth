"""Identifiers verified against official access page on 2026-10-24."""
PRODUCT = "BATHYMETRY_GLO_PHY_COASTAL_L4_MY_016_001"
DOI = "https://doi.org/10.48670/mds-00364"
PRODUCT_URL = "https://data.marine.copernicus.eu/product/" + PRODUCT
LICENCE = "https://marine.copernicus.eu/user-corner/service-commitments-and-licence"
PUM = "https://documentation.marine.copernicus.eu/PUM/CMEMS-GLO-PUM-SDB-016-001.pdf"
DATASETS = {
    "irte": ("Optical RTE", "cmems_obs-sdb_glo_phy_irte_my_100m-l4-s2_static"),
    "wk": ("Wave Kinematics", "cmems_obs-sdb_glo_phy_wk_my_100m-l4-s2_static"),
    "it": ("Intertidal", "cmems_obs-sdb_glo_phy_it_my_100m-l4-s2_static"),
}
DATASET_FOLDERS = {"irte": "Optical_RTE", "wk": "Wave_Kinematics", "it": "Intertidal"}
DATASET_DESCRIPTIONS = {
    "irte": "Physics-based optical bathymetry from inversion of the Radiative Transfer Equation (RTE).",
    "wk": "Bathymetry derived from wave kinematics.",
    "it": "Bathymetry of intertidal areas between tidal levels.",
}

def dataset_display_name(key_or_folder):
    for key, folder in DATASET_FOLDERS.items():
        if key_or_folder in (key, folder):
            return DATASETS[key][0]
    return str(key_or_folder)

VARIABLES = ("height", "Quality_indicator")

def select_variables(names):
    """Live height versus manual example elevation; never silently rename science."""
    candidates = [v for v in ("height", "elevation") if v in names]
    if len(candidates) != 1 or "Quality_indicator" not in names:
        raise ValueError("Unknown bathymetry/quality schema")
    return candidates + ["Quality_indicator"] + (["SDB_type"] if "SDB_type" in names else [])

def citation(access_date):
    return ("Global coastal satellite derived bathymetry static. E.U. Copernicus Marine "
            "Service Information (CMEMS). Marine Data Store (MDS). " + DOI +
            " (Accessed on " + access_date + ").")
