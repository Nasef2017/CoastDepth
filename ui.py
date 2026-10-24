import json
from pathlib import Path
import shutil
import sys
import uuid
from qgis.PyQt.QtCore import QProcess, QProcessEnvironment, QSettings, QStandardPaths, QTimer, QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QComboBox, QFileDialog, QMessageBox, QProgressBar,
    QPlainTextEdit, QSpinBox, QGroupBox)
from qgis.core import QgsApplication, QgsProject, QgsRasterLayer
from qgis.gui import QgsMapLayerComboBox
from .auth import load_credentials, save_credentials, forget_credentials
from .core.catalogue import DATASETS, DATASET_DESCRIPTIONS, dataset_display_name
from .core.events import RunLog, event
from .dependencies import environment_python
from .roi import snapshot
from .qt_compat import APP_LOCAL_DATA, FAILED_TO_START, CRASH_EXIT, PASSWORD, ACCEPTED, exec_dialog

HERE = Path(__file__).resolve().parent

def default_python():
    candidates = [Path(sys.prefix) / "python.exe", Path(sys.prefix) / "bin/python3"]
    if Path(sys.executable).name.lower().startswith("python"):
        candidates.insert(0, Path(sys.executable))
    # OSGeo4W commonly uses <root>/apps/Python3xx/python.exe.
    prefix = Path(QgsApplication.prefixPath())
    for parent in [prefix] + list(prefix.parents)[:3]:
        candidates.extend(parent.glob("Python3*/python.exe"))
        candidates.extend(parent.glob("apps/Python3*/python.exe"))
        candidates.extend(parent.glob("bin/python3.exe"))
        candidates.extend(parent.glob("bin/python.exe"))
    return next((str(p) for p in candidates if p.is_file()), "")

def env_root():
    root = Path(QStandardPaths.writableLocation(APP_LOCAL_DATA))
    return root / "coastdepth" / "worker-v1"

def worker_python():
    return str(environment_python(env_root()))

def clean_environment():
    environment = QProcessEnvironment.systemEnvironment()
    for name in ("PYTHONHOME", "PYTHONPATH", "GDAL_DATA", "PROJ_LIB", "PROJ_DATA"):
        environment.remove(name)
    environment.insert("PYTHONNOUSERSITE", "1")
    environment.insert("COPERNICUSMARINE_DISABLE_SSL_CONTEXT", "False")
    return environment

def start_worker(parent, request):
    proc = QProcess(parent)
    proc.setProcessEnvironment(clean_environment())
    proc.setProgram(worker_python())
    proc.setArguments([str(HERE / "worker.py")])
    # Passwords are never arguments, environment variables or files.
    payload = json.dumps(request).encode("utf-8") + b"\n"
    def send():
        proc.write(payload)
        proc.closeWriteChannel()
        try:
            proc.started.disconnect(send)
        except TypeError:
            pass
    proc.started.connect(send)
    return proc

from .dependency_ui import DependencyDialog

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CoastDepth — Copernicus Marine login")
        self.credentials = None
        self.proc = None
        self.valid = False
        self.aborted = False
        self.buffer = b""
        layout = QFormLayout(self)
        self.username, self.password = QLineEdit(), QLineEdit()
        self.password.setEchoMode(PASSWORD)
        layout.addRow("Username / email", self.username)
        layout.addRow("Password", self.password)
        self.remember = QCheckBox("Save in encrypted QGIS Authentication Manager")
        layout.addRow(self.remember)
        self.status = QLabel("A free Copernicus Marine account is required.")
        self.status.setWordWrap(True)
        layout.addRow(self.status)
        self.button = QPushButton("Verify and use")
        self.button.clicked.connect(self.verify)
        layout.addRow(self.button)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.cancel)

    def verify(self):
        if not self.username.text().strip() or not self.password.text():
            self.status.setText("Enter username and password.")
            return
        if not Path(worker_python()).is_file():
            self.status.setText("Open Dependencies and install the worker first.")
            return
        self.button.setEnabled(False)
        self.valid = False
        self.aborted = False
        self.buffer = b""
        self.proc = start_worker(self, {"action": "login", "username": self.username.text().strip(), "password": self.password.text()})
        self.proc.readyReadStandardOutput.connect(self.read)
        self.proc.finished.connect(self.finished)
        self.proc.errorOccurred.connect(self.error)
        self.status.setText("Verifying with Copernicus Marine…")
        self.timer.start(120000)
        self.proc.start()

    def error(self, error):
        if error == FAILED_TO_START:
            self.timer.stop()
            self.status.setText("Worker could not start. Open Dependencies.")
            self.button.setEnabled(True)
            self.proc.deleteLater()
            self.proc = None

    def read(self):
        self.buffer += bytes(self.proc.readAllStandardOutput())
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            try:
                value = json.loads(line)
                self.valid = self.valid or value.get("code") == "authenticated"
                self.status.setText(event(value.get("code", "FAILED"))["message"])
            except ValueError:
                pass

    def finished(self, code, status):
        if self.proc is None:
            return
        self.read()
        self.timer.stop()
        self.proc.readAllStandardError()
        self.proc.deleteLater()
        self.proc = None
        self.button.setEnabled(True)
        if code == 0 and self.valid and not self.aborted:
            self.credentials = (self.username.text().strip(), self.password.text())
            if self.remember.isChecked() and not save_credentials(*self.credentials):
                QMessageBox.warning(self, "Credentials not saved", "QGIS authentication storage could not be unlocked. Credentials will be used only for this session.")
            self.password.clear()
            self.accept()
        else:
            self.valid = False
            self.status.setText("Verification failed or timed out. Check credentials, dependencies and connection.")

    def cancel(self):
        self.aborted = True
        if self.proc is not None:
            self.valid = False
            self.proc.kill()

    def reject(self):
        self.cancel()
        self.password.clear()
        super().reject()

class FetchDialog(QDialog):
    def __init__(self, iface):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.proc = None
        self.credentials = None
        self.needs_login = False
        self.log = RunLog()
        self.request = None
        self.result = None
        self.cancelled = False
        self.buffer = b""
        self.setWindowTitle("CoastDepth")
        self.resize(760, 760)
        layout = QVBoxLayout(self)
        notice = QLabel("Copernicus Marine Coastal SDB • static ~100 m data • not for navigation")
        notice.setWordWrap(True)
        layout.addWidget(notice)
        group = QGroupBox("Datasets")
        row = QHBoxLayout(group)
        self.datasets = {}
        for key, (label, _) in DATASETS.items():
            checkbox = QCheckBox(label)
            checkbox.setToolTip(DATASET_DESCRIPTIONS[key])
            checkbox.setChecked(True)
            self.datasets[key] = checkbox
            row.addWidget(checkbox)
        layout.addWidget(group)
        form = QFormLayout()
        self.layer = QgsMapLayerComboBox()
        form.addRow("ROI layer", self.layer)
        self.mode = QComboBox()
        self.mode.addItem("Polygon mask (all polygon features)", "polygon")
        self.mode.addItem("Extent from layer", "extent")
        form.addRow("ROI mode", self.mode)
        self.selected = QCheckBox("Use only Selected Features (vector layers)")
        form.addRow(self.selected)
        self.formats = QComboBox()
        self.formats.addItem("NetCDF + GeoTIFF", ["netcdf", "geotiff"])
        self.formats.addItem("NetCDF", ["netcdf"])
        self.formats.addItem("GeoTIFF", ["geotiff"])
        form.addRow("Output format", self.formats)
        self.output = QLineEdit(QSettings().value("CoastDepth/output", ""))
        folder = QPushButton("Folder…")
        folder.clicked.connect(self.choose_folder)
        row = QHBoxLayout()
        row.addWidget(self.output)
        row.addWidget(folder)
        form.addRow("Output", row)
        self.timeout = QSpinBox()
        self.timeout.setRange(1, 240)
        self.timeout.setValue(30)
        self.timeout.setSuffix(" minutes")
        form.addRow("Time limit", self.timeout)
        self.add_layers = QCheckBox("Add height layers to QGIS when complete")
        self.add_layers.setChecked(True)
        form.addRow(self.add_layers)
        layout.addLayout(form)
        row = QHBoxLayout()
        login = QPushButton("Login / change account…")
        login.clicked.connect(self.login)
        forget = QPushButton("Forget saved credentials")
        forget.clicked.connect(self.forget)
        dependencies = QPushButton("Dependencies…")
        dependencies.clicked.connect(lambda: exec_dialog(DependencyDialog(self)))
        row.addWidget(login)
        row.addWidget(forget)
        row.addWidget(dependencies)
        layout.addLayout(row)
        self.controls = [group, self.layer, self.mode, self.selected, self.formats, self.output, folder,
                         self.timeout, self.add_layers, login, forget, dependencies]
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)
        row = QHBoxLayout()
        self.fetch = QPushButton("Download")
        self.fetch.clicked.connect(self.download)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel)
        self.retry_button = QPushButton("Retry last request")
        self.retry_button.setEnabled(False)
        self.retry_button.clicked.connect(self.retry_last)
        export = QPushButton("Export log…")
        export.clicked.connect(self.export_log)
        for button in (self.fetch, self.cancel_button, self.retry_button, export):
            row.addWidget(button)
        layout.addLayout(row)
        help_button = QPushButton("Open usage guide")
        help_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(HERE / "docs/USAGE.md"))))
        layout.addWidget(help_button)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.timed_out)

    def choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Output folder", self.output.text())
        if path:
            self.output.setText(path)

    def login(self):
        dialog = LoginDialog(self)
        if exec_dialog(dialog) == ACCEPTED:
            self.credentials = dialog.credentials
            self.needs_login = False
            dialog.credentials = None
            return True
        return False

    def forget(self):
        self.credentials = None
        if not forget_credentials():
            QMessageBox.warning(self, "Not removed", "QGIS could not remove the saved authentication entry. Unlock Authentication Manager and try again.")

    def append(self, record):
        value = self.log.add(record)
        detail = " [" + dataset_display_name(value["dataset"]) + "]" if "dataset" in value else ""
        self.log_view.appendPlainText(value["utc"] + "  " + value["message"] + detail)
        self.progress.setValue(max(self.progress.value(), value["progress"]))

    def download(self):
        if self.proc is not None:
            return
        try:
            bounds, polygon = snapshot(self.layer.currentLayer(), self.mode.currentData(), self.selected.isChecked())
            keys = [key for key, checkbox in self.datasets.items() if checkbox.isChecked()]
            if not keys:
                raise ValueError("Choose at least one dataset.")
            output_text = self.output.text().strip()
            if not output_text:
                raise ValueError("Choose an output folder.")
            output = Path(output_text).resolve()
            output.mkdir(parents=True, exist_ok=True)
            request = dict(action="download", bounds=vars(bounds), polygon=polygon, datasets=keys,
                           formats=self.formats.currentData(), output=str(output))
        except Exception as exc:
            # ROI exceptions contain only our controlled local validation text.
            QMessageBox.warning(self, "Check request", str(exc) if isinstance(exc, ValueError) else "Could not prepare ROI or output folder. Check geometry, CRS and folder permissions.")
            return
        QSettings().setValue("CoastDepth/output", str(output))
        self.request = request
        self.launch()

    def retry_last(self):
        if self.request is not None and self.proc is None:
            self.launch()

    def launch(self):
        if not Path(worker_python()).is_file():
            exec_dialog(DependencyDialog(self))
            if not Path(worker_python()).is_file():
                return
        if self.needs_login:
            self.credentials = None
            if not self.login():
                return
        self.credentials = self.credentials or load_credentials()
        if not self.credentials and not self.login():
            return
        self.run_id = str(uuid.uuid4())
        self.result = None
        self.cancelled = False
        self.buffer = b""
        self.log = RunLog()
        self.log_view.clear()
        self.progress.setValue(0)
        self.append(event("start"))
        payload = dict(self.request, run_id=self.run_id, username=self.credentials[0], password=self.credentials[1])
        self.proc = start_worker(self, payload)
        payload.clear()
        self.proc.readyReadStandardOutput.connect(self.read)
        self.proc.finished.connect(self.finished)
        self.proc.errorOccurred.connect(self.error)
        self.busy(True)
        self.timer.start(self.timeout.value() * 60000)
        self.proc.start()

    def busy(self, value):
        for control in self.controls:
            control.setEnabled(not value)
        self.fetch.setEnabled(not value)
        self.cancel_button.setEnabled(value)
        self.retry_button.setEnabled(not value and self.request is not None)

    def read(self):
        self.buffer += bytes(self.proc.readAllStandardOutput())
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            try:
                value = json.loads(line)
                self.append(value)
                if value.get("code") == "AUTH":
                    self.credentials = None
                    self.needs_login = True
                if value.get("code") == "complete":
                    self.result = value.get("result")
            except (ValueError, TypeError):
                self.append(event("FAILED"))

    def error(self, error):
        if error == FAILED_TO_START and self.proc is not None:
            self.append(event("DEPENDENCY"))
            self.finished(-1, CRASH_EXIT)

    def cancel(self):
        if self.proc is not None:
            self.cancelled = True
            self.proc.kill()

    def timed_out(self):
        self.append(event("timeout"))
        self.cancel()

    def cleanup_partial(self):
        root = Path(self.request["output"]).resolve()
        partial = root / (".coastdepth_partial_" + self.run_id)
        if partial.is_dir() and not partial.is_symlink() and partial.resolve().parent == root:
            shutil.rmtree(partial)

    def finished(self, code, status):
        if self.proc is None:
            return
        self.timer.stop()
        self.read()
        self.proc.readAllStandardError()
        self.proc.deleteLater()
        self.proc = None
        self.busy(False)
        try:
            self.cleanup_partial()
        except OSError:
            self.log_view.appendPlainText("Partial cleanup failed; see troubleshooting for the hidden partial folder.")
        if self.cancelled:
            self.append(event("cancelled"))
        elif code == 0 and self.result:
            if self.add_layers.isChecked():
                self.load_results()
            self.retry_button.setEnabled(False)
        elif not self.log.records or self.log.records[-1]["code"] not in ("AUTH", "NETWORK", "DEPENDENCY", "SCHEMA", "FAILED"):
            self.append(event("FAILED"))
        # Safe, structured log is saved for success, cancellation and failure.
        try:
            self.log.export(Path(self.request["output"]) / ("coastdepth_" + self.run_id + ".jsonl"))
        except OSError:
            self.log_view.appendPlainText("Could not save log automatically. Use Export log.")

    def load_results(self):
        from .core.results import height_sources
        try:
            sources = height_sources(self.request, self.result, self.run_id)
        except ValueError:
            self.append(event("FAILED"))
            return
        for source, label in sources:
            layer = QgsRasterLayer(source, label, "gdal")
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
            else:
                self.log_view.appendPlainText("A result could not be added to QGIS. Files remain available in the output folder.")

    def export_log(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export safe run log", "coastdepth_log.jsonl", "JSON Lines (*.jsonl)")
        if path:
            try:
                self.log.export(path)
            except OSError:
                QMessageBox.warning(self, "Export failed", "Could not write the log. Choose a writable folder.")

    def reject(self):
        if self.proc is not None:
            self.cancel()
        else:
            self.credentials = None
            super().reject()

    def closeEvent(self, close_event):
        if self.proc is not None:
            self.cancel()
            close_event.ignore()
        else:
            self.credentials = None
            close_event.accept()
