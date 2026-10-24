"""Explicit Qt5/Qt6 API differences used by the plugin."""
from qgis.PyQt.QtCore import QProcess, QStandardPaths
from qgis.PyQt.QtWidgets import QDialog, QLineEdit

def enum_value(owner, scope, name):
    scoped = getattr(owner, scope, None)
    if scoped is not None and hasattr(scoped, name):
        return getattr(scoped, name)
    return getattr(owner, name)

APP_LOCAL_DATA = enum_value(QStandardPaths, "StandardLocation", "AppLocalDataLocation")
FAILED_TO_START = enum_value(QProcess, "ProcessError", "FailedToStart")
CRASH_EXIT = enum_value(QProcess, "ExitStatus", "CrashExit")
PASSWORD = enum_value(QLineEdit, "EchoMode", "Password")
ACCEPTED = enum_value(QDialog, "DialogCode", "Accepted")

def exec_dialog(dialog):
    method = getattr(dialog, "exec", None)
    return method() if method is not None else dialog.exec_()
