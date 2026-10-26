"""Native QGIS Processing algorithms with full product citations in Short Help."""
import json
from pathlib import Path
import uuid
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.core import (Qgis, QgsApplication, QgsProcessingProvider, QgsProcessingAlgorithm,
    QgsProcessingException, QgsProcessingParameterMapLayer, QgsProcessingParameterEnum,
    QgsProcessingParameterBoolean, QgsProcessingParameterFolderDestination,
    QgsProcessingParameterNumber, QgsProcessingOutputFolder, QgsProcessingOutputFile,
    QgsProcessingOutputString, QgsRasterLayer)
from .brand import DISPLAY_NAME
from .core.catalogue import DATASETS
from .core.results import height_sources
from .core.runner import execute_worker, WorkerFailure
from .help_content import short_help
from .roi import snapshot

HERE = Path(__file__).resolve().parent

class RuntimeState:
    def __init__(self, iface=None):
        self.iface = iface
        self.ready = False
        self.credentials = None
        self.dependency_dialog = None

class CoastDepthProvider(QgsProcessingProvider):
    def __init__(self, state):
        super().__init__()
        self.state = state
    def id(self): return "coastdepth"
    def name(self): return DISPLAY_NAME
    def longName(self): return DISPLAY_NAME
    def icon(self): return QIcon(str(HERE / "icon.svg"))
    def loadAlgorithms(self):
        self.addAlgorithm(CoastDepthSetup(self.state))
        for key in DATASETS:
            self.addAlgorithm(CoastDepthDownload((key,), self.state))
        self.addAlgorithm(CoastDepthDownload(tuple(DATASETS), self.state))

class CoastDepthDownload(QgsProcessingAlgorithm):
    def __init__(self, keys=("irte",), state=None):
        super().__init__()
        self.keys = tuple(keys)
        self.state = state or RuntimeState()
        self._credentials = None
        self._completed = None
    def name(self):
        return "download_all" if len(self.keys) > 1 else "download_" + self.keys[0]
    def displayName(self):
        return "Download all three Copernicus SDB datasets" if len(self.keys) > 1 else "Download " + DATASETS[self.keys[0]][0] + " — Copernicus Marine"
    def group(self): return "Copernicus Marine coastal bathymetry"
    def groupId(self): return "copernicus_sdb"
    def tags(self): return ["Copernicus", "Marine", "SDB", "bathymetry", "height", "coastal", "CoastDepth"]
    def shortHelpString(self): return short_help(self.keys)
    def helpUrl(self): return QUrl.fromLocalFile(str(HERE / "docs/HELP.html")).toString()
    def createInstance(self): return CoastDepthDownload(self.keys, self.state)
    def initAlgorithm(self, configuration=None):
        self.addParameter(QgsProcessingParameterMapLayer("ROI_LAYER", "ROI layer"))
        self.addParameter(QgsProcessingParameterEnum("ROI_MODE", "ROI mode",
            ["Polygon mask", "Extent from layer"], defaultValue=0))
        self.addParameter(QgsProcessingParameterBoolean("SELECTED_ONLY", "Selected Features only (vector layer)", defaultValue=False))
        self.addParameter(QgsProcessingParameterEnum("FORMAT", "Saved output format",
            ["NetCDF + GeoTIFF", "GeoTIFF", "NetCDF"], defaultValue=0))
        self.addParameter(QgsProcessingParameterFolderDestination("OUTPUT_FOLDER", "Output parent folder"))
        self.addParameter(QgsProcessingParameterNumber("TIMEOUT", "Time limit (minutes)",
            type=QgsProcessingParameterNumber.Integer, defaultValue=30, minValue=1, maxValue=240))
        self.addParameter(QgsProcessingParameterBoolean("ADD_HEIGHTS", "Add Height layers to QGIS", defaultValue=True))
        self.addOutput(QgsProcessingOutputFolder("RESULT_FOLDER", "Completed run folder"))
        self.addOutput(QgsProcessingOutputFile("LOG", "Safe run log (JSONL)"))
        self.addOutput(QgsProcessingOutputString("HEIGHT_SOURCES", "Height sources (JSON)"))

    def prepareAlgorithm(self, parameters, context, feedback):
        from .auth import load_credentials
        from .ui import LoginDialog, worker_python
        from .qt_compat import exec_dialog, ACCEPTED
        if not self.state.ready or not Path(worker_python()).is_file():
            if self.state.dependency_dialog is not None:
                self.state.dependency_dialog.show()
                self.state.dependency_dialog.scan()
            raise QgsProcessingException("Required libraries are not ready. Use CoastDepth Account and dependencies, then Recheck libraries.")
        layer = self.parameterAsLayer(parameters, "ROI_LAYER", context)
        try:
            bounds, polygon = snapshot(layer, "polygon" if self.parameterAsEnum(parameters, "ROI_MODE", context) == 0 else "extent",
                self.parameterAsBool(parameters, "SELECTED_ONLY", context))
        except ValueError as exc:
            raise QgsProcessingException(str(exc)) from None
        if self.state.iface is None and not self.state.credentials and not QgsApplication.authManager().masterPasswordIsSet():
            raise QgsProcessingException("Unlock a saved Copernicus account in QGIS before a headless Processing run.")
        credentials = self.state.credentials or load_credentials()
        if not credentials:
            if self.state.iface is None:
                raise QgsProcessingException("No saved Copernicus credentials. Sign in using CoastDepth Account and dependencies in QGIS.")
            dialog = LoginDialog(self.state.iface.mainWindow())
            if exec_dialog(dialog) != ACCEPTED or not dialog.credentials:
                raise QgsProcessingException("Copernicus login was cancelled or unsuccessful.")
            credentials = dialog.credentials
            dialog.credentials = None
        self.state.credentials = credentials
        self._credentials = credentials
        formats = (["netcdf", "geotiff"], ["geotiff"], ["netcdf"])[self.parameterAsEnum(parameters, "FORMAT", context)]
        self._request = dict(action="download", bounds=vars(bounds), polygon=polygon,
            datasets=list(self.keys), formats=formats,
            output=self.parameterAsOutputLayer(parameters, "OUTPUT_FOLDER", context), run_id=str(uuid.uuid4()))
        if not self._request["output"]:
            raise QgsProcessingException("Choose an output folder.")
        self._timeout = self.parameterAsInt(parameters, "TIMEOUT", context)
        self._add_heights = self.parameterAsBool(parameters, "ADD_HEIGHTS", context)
        return True

    def processAlgorithm(self, parameters, context, feedback):
        from .ui import worker_python
        try:
            result, log_path = execute_worker(worker_python(), HERE / "worker.py", self._request,
                self._credentials, feedback, self._timeout)
            if result.get("skipped_datasets"):
                from .core.catalogue import dataset_display_name
                skipped_names = [dataset_display_name(k) for k in result["skipped_datasets"]]
                feedback.pushInfo("Notice: Skipped datasets without data in ROI: " + ", ".join(skipped_names))
            sources = height_sources(self._request, result, self._request["run_id"])
            self._completed = (result, sources, log_path)
            return {"OUTPUT_FOLDER": self._request["output"], "RESULT_FOLDER": result["directory"],
                    "LOG": log_path, "HEIGHT_SOURCES": json.dumps([source for source, _ in sources])}
        except WorkerFailure as exc:
            if exc.code == "AUTH":
                self.state.credentials = None
            if exc.log_path:
                feedback.pushInfo("Safe log: " + str(exc.log_path))
            raise QgsProcessingException(str(exc)) from None
        except (ValueError, OSError):
            raise QgsProcessingException("Could not validate results. Check the output folder and safe run log.") from None
        finally:
            self._credentials = None

    def postProcessAlgorithm(self, context, feedback):
        if self._completed and self._add_heights and context.project() is not None:
            for source, label in self._completed[1]:
                layer = QgsRasterLayer(source, label, "gdal")
                if layer.isValid():
                    context.project().addMapLayer(layer)
                else:
                    feedback.reportError("A Height layer could not be loaded. Saved files remain in the run folder.")
        return {}

class CoastDepthSetup(QgsProcessingAlgorithm):
    def __init__(self, state=None):
        super().__init__()
        self.state = state or RuntimeState()
    def name(self): return "account_and_dependencies"
    def displayName(self): return "Account, dependencies and help"
    def group(self): return "Setup and documentation"
    def groupId(self): return "setup"
    def flags(self):
        scope = getattr(Qgis, "ProcessingAlgorithmFlag", None)
        flag = scope.NoThreading if scope is not None else QgsProcessingAlgorithm.FlagNoThreading
        return super().flags() | flag
    def shortHelpString(self): return short_help(tuple(DATASETS), settings=True)
    def helpUrl(self): return QUrl.fromLocalFile(str(HERE / "docs/HELP.html")).toString()
    def createInstance(self): return CoastDepthSetup(self.state)
    def initAlgorithm(self, configuration=None):
        self.addParameter(QgsProcessingParameterEnum("ACTION", "Action", ["Copernicus login / change account",
            "Check required libraries", "Read full help", "Forget saved credentials"], defaultValue=0))
        self.addOutput(QgsProcessingOutputString("STATUS", "Status"))
    def processAlgorithm(self, parameters, context, feedback):
        from .auth import forget_credentials
        from .ui import LoginDialog, DependencyDialog
        from .qt_compat import exec_dialog, ACCEPTED
        if self.state.iface is None:
            raise QgsProcessingException("This setup tool requires the QGIS desktop interface.")
        action = self.parameterAsEnum(parameters, "ACTION", context)
        if action == 0:
            if not self.state.ready:
                raise QgsProcessingException("Check and install required libraries before signing in.")
            dialog = LoginDialog(self.state.iface.mainWindow())
            if exec_dialog(dialog) != ACCEPTED:
                return {"STATUS": "Login cancelled"}
            self.state.credentials = dialog.credentials
            dialog.credentials = None
            return {"STATUS": "Copernicus credentials verified"}
        if action == 1:
            dialog = self.state.dependency_dialog
            if dialog is None:
                dialog = DependencyDialog(self.state.iface.mainWindow())
                self.state.dependency_dialog = dialog
            dialog.show()
            dialog.scan()
            return {"STATUS": "Dependency check opened"}
        if action == 2:
            QDesktopServices.openUrl(QUrl(self.helpUrl()))
            return {"STATUS": "Help opened"}
        self.state.credentials = None
        if not forget_credentials():
            raise QgsProcessingException("QGIS could not remove the saved authentication entry.")
        return {"STATUS": "Saved credentials removed"}
