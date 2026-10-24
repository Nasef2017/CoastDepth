"""Startup gate and copyable manual installation instructions. No auto-install."""
import json
from pathlib import Path
from qgis.PyQt.QtCore import QProcess, QTimer, pyqtSignal
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout,
    QPushButton, QFileDialog, QPlainTextEdit)
from qgis.core import QgsApplication
from .dependencies import PACKAGES, SPECS, missing_environment_result, shell_commands
from .qt_compat import FAILED_TO_START

class DependencyDialog(QDialog):
    readinessChanged = pyqtSignal(bool)

    def __init__(self, parent=None, startup=False):
        super().__init__(parent)
        # Lazy import prevents a dependency on this module during ui initialization.
        from .ui import default_python
        self.startup = startup
        self.ready = False
        self.proc = None
        self.result = None
        self.setWindowTitle("CoastDepth — Dependency check")
        self.resize(820, 570)
        layout = QVBoxLayout(self)
        self.status_label = QLabel("Checking required libraries…")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        label = QLabel("Open OSGeo4W Shell from the QGIS installation / Start menu, then paste the commands below.\n"
            "They install libraries into this plugin's private Python environment.\n"
            "After installation, return here and click Recheck libraries.")
        label.setWordWrap(True)
        layout.addWidget(label)
        row = QHBoxLayout()
        self.python = QLineEdit(default_python() or "python")
        row.addWidget(self.python)
        browse = QPushButton("Choose QGIS Python…")
        browse.clicked.connect(self.browse)
        row.addWidget(browse)
        layout.addLayout(row)
        self.report = QPlainTextEdit()
        self.report.setReadOnly(True)
        layout.addWidget(self.report)
        self.commands = QPlainTextEdit()
        self.commands.setReadOnly(True)
        self.commands.setPlaceholderText("Installation commands appear after the dependency check.")
        layout.addWidget(self.commands)
        row = QHBoxLayout()
        self.copy = QPushButton("Copy pip install commands")
        self.copy.clicked.connect(self.copy_commands)
        self.check = QPushButton("Recheck libraries")
        self.check.clicked.connect(self.scan)
        help_button = QPushButton("OSGeo4W Shell instructions")
        help_button.clicked.connect(self.help)
        close = QPushButton("Close")
        close.clicked.connect(self.reject)
        for button in (self.copy, self.check, help_button, close):
            row.addWidget(button)
        layout.addLayout(row)
        self.python.textChanged.connect(self.refresh_commands)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.probe_timeout)
        self.initial_check = QTimer(self)
        self.initial_check.setSingleShot(True)
        self.initial_check.timeout.connect(self.scan)
        self.initial_check.start(0)

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select QGIS Python executable")
        if path:
            self.python.setText(path)

    def help(self):
        path = Path(__file__).resolve().parent / "docs/INSTALL.md"
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def copy_commands(self):
        QgsApplication.clipboard().setText(self.commands.toPlainText())

    def refresh_commands(self):
        from .ui import env_root
        if not self.result or self.ready:
            self.commands.clear()
            self.copy.setEnabled(False)
            return
        try:
            value = shell_commands(self.python.text().strip() or "python", env_root(), self.result)
        except ValueError:
            value = "Cannot safely quote this path. Choose a QGIS Python path without %, ! or quotation marks."
            self.copy.setEnabled(False)
        else:
            self.copy.setEnabled(True)
        self.commands.setPlainText(value)

    def scan(self):
        from .ui import worker_python, clean_environment, HERE
        self.initial_check.stop()
        if self.proc is not None:
            return
        self.ready = False
        self.check.setEnabled(False)
        self.status_label.setText("Checking required libraries…")
        executable = worker_python()
        if not Path(executable).is_file():
            self.handle_result(missing_environment_result())
            return
        self.proc = QProcess(self)
        self.proc.setProcessEnvironment(clean_environment())
        self.proc.setProgram(executable)
        self.proc.setArguments([str(HERE / "dependencies.py")])
        self.proc.finished.connect(self.finished)
        self.proc.errorOccurred.connect(self.error)
        self.timer.start(60000)
        self.proc.start()

    def reset(self):
        self.timer.stop()
        if self.proc is not None:
            self.proc.deleteLater()
        self.proc = None
        self.check.setEnabled(True)

    def unavailable(self):
        self.reset()
        self.handle_result({"ready": False, "missing": [], "broken": list(PACKAGES),
            "incompatible": [], "packages": {}, "compatible_python": True, "probe_failed": True})

    def error(self, error):
        if error == FAILED_TO_START:
            self.unavailable()

    def probe_timeout(self):
        if self.proc is not None:
            self.proc.kill()
            # finished() handles process exit and supplies fixed diagnostics.

    def finished(self, code, status):
        if self.proc is None:
            return
        output = bytes(self.proc.readAllStandardOutput())
        self.proc.readAllStandardError()
        try:
            result = json.loads(output.decode("utf-8"))
            if code != 0 or not isinstance(result, dict) or "packages" not in result:
                raise ValueError()
        except (ValueError, UnicodeError):
            self.unavailable()
            return
        self.reset()
        self.handle_result(result)

    def handle_result(self, result):
        self.result = result
        self.ready = bool(result.get("ready"))
        self.check.setEnabled(True)
        lines = []
        labels = (("missing", "MISSING"), ("broken", "IMPORT ERROR"), ("incompatible", "INCOMPATIBLE VERSION"))
        for field, label in labels:
            for name in result.get(field, []):
                if name in PACKAGES:
                    lines.append(label + ": " + PACKAGES[name] + SPECS[name])
        if result.get("environment_missing"):
            lines.insert(0, "The required private environment is not installed. These libraries are required in that environment:")
        if result.get("probe_failed"):
            lines.insert(0, "The worker Python could not be checked. Repair its environment or check the selected QGIS Python path.")
        if not result.get("compatible_python", True):
            lines.insert(0, "Python 3.10 or later is required. Use a recent QGIS installation before installing packages.")
        if self.ready:
            self.setWindowTitle("CoastDepth — Dependencies ready")
            self.status_label.setText("All required libraries are installed and compatible.")
            self.status_label.setStyleSheet("")
            lines = [name + ": " + str(result["packages"].get(name, "checked")) for name in PACKAGES]
        else:
            self.setWindowTitle("Dependency ERROR — CoastDepth")
            self.status_label.setText("ERROR: Required libraries are missing, incompatible or cannot be imported.\n"
                "Open OSGeo4W Shell and run the pip install commands below. Downloads are blocked until Recheck succeeds.")
            self.status_label.setStyleSheet("color: #a51b1b; font-weight: bold;")
        self.report.setPlainText("\n".join(lines))
        self.refresh_commands()
        self.readinessChanged.emit(self.ready)
        if not self.ready:
            self.show()
            self.raise_()
        elif self.startup:
            self.hide()

    def shutdown(self):
        self.initial_check.stop()
        self.timer.stop()
        if self.proc is not None:
            proc = self.proc
            proc.blockSignals(True)
            proc.kill()
            proc.waitForFinished(3000)
            self.reset()
        self.close()

    def reject(self):
        # Checks may finish after the user hides the dialog; unload stops them explicitly.
        super().reject()

    def closeEvent(self, event):
        event.accept()
