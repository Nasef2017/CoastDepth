"""Processing-only registration: no top toolbar or Plugins-menu action."""
from qgis.core import QgsApplication
from .processing_provider import CoastDepthProvider, RuntimeState

class CoastDepthPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.state = RuntimeState(iface)
        self.dependency_dialog = None

    def initGui(self):
        self.provider = CoastDepthProvider(self.state)
        QgsApplication.processingRegistry().addProvider(self.provider)
        from .dependency_ui import DependencyDialog
        self.dependency_dialog = DependencyDialog(self.iface.mainWindow(), startup=True)
        self.state.dependency_dialog = self.dependency_dialog
        self.dependency_dialog.readinessChanged.connect(self.dependencies_checked)

    def dependencies_checked(self, ready):
        self.state.ready = bool(ready)

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
