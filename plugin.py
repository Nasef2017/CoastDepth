"""Processing-only registration: no top toolbar or Plugins-menu action."""
import importlib.util
from pathlib import Path
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QMessageBox
from .processing_provider import CoastDepthProvider, RuntimeState
from .qt_compat import exec_dialog

class CoastDepthPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.state = RuntimeState(iface)
        self.dependency_dialog = None
        self.dependencies_met = True

    def check_dependencies(self):
        from .ui import worker_python
        required_modules = {
            'copernicusmarine': 'copernicusmarine==2.4.0',
            'rasterio': 'rasterio',
            'netCDF4': 'netCDF4',
            'xarray': 'xarray',
            'numpy': 'numpy',
            'packaging': 'packaging'
        }
        worker_exe = worker_python()
        worker_site_packages = None
        if Path(worker_exe).is_file():
            candidate = Path(worker_exe).resolve().parent.parent / "Lib" / "site-packages"
            if candidate.is_dir():
                worker_site_packages = candidate

        missing = []
        for mod, pip_name in required_modules.items():
            if importlib.util.find_spec(mod) is not None:
                continue
            if worker_site_packages is not None and any(worker_site_packages.glob(f"{mod}*")):
                continue
            missing.append(pip_name)
        return missing

    def initGui(self):
        missing = self.check_dependencies()
        if missing:
            self.dependencies_met = False
            self.state.ready = False
            parent = self.iface.mainWindow() if self.iface else None
            msg = QMessageBox(parent)
            try:
                msg.setIcon(QMessageBox.Icon.Critical)
            except AttributeError:
                msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Missing Dependencies")
            text = "<b>CoastDepth requires additional Python libraries.</b><br><br>"
            text += "Please open the <b>OSGeo4W Shell</b> as Administrator and run the following command:<br><br>"
            text += f"<code>pip install {' '.join(missing)}</code><br><br>"
            text += "After installation, please restart QGIS."
            msg.setText(text)
            exec_dialog(msg)
            return

        self.dependencies_met = True
        self.state.ready = True
        self.provider = CoastDepthProvider(self.state)
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        self.state.ready = False
        self.state.credentials = None
        if self.dependency_dialog is not None:
            self.dependency_dialog.shutdown()
            self.dependency_dialog.deleteLater()
            self.dependency_dialog = None
            self.state.dependency_dialog = None
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None
