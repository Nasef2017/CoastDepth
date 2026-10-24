"""Only auth configuration ID enters QSettings. Secrets remain in QGIS Auth Manager."""
from qgis.core import QgsApplication, QgsAuthMethodConfig
from qgis.PyQt.QtCore import QSettings

KEY = "CoastDepth/authcfg"

def load_credentials():
    manager = QgsApplication.authManager()
    auth_id = QSettings().value(KEY, "")
    if not auth_id or manager.isDisabled():
        return None
    config = QgsAuthMethodConfig()
    if not manager.loadAuthenticationConfig(auth_id, config, True):
        return None
    username, password = config.config("username"), config.config("password")
    return (username, password) if username and password else None

def save_credentials(username, password):
    manager = QgsApplication.authManager()
    if manager.isDisabled() or not manager.setMasterPassword(True):
        return False
    config = QgsAuthMethodConfig()
    config.setName("CoastDepth — Copernicus Marine")
    config.setMethod("Basic")
    config.setConfig("username", username)
    config.setConfig("password", password)
    previous = QSettings().value(KEY, "")
    if previous:
        config.setId(previous)
        ok = manager.updateAuthenticationConfig(config)
    else:
        ok = manager.storeAuthenticationConfig(config)
    if ok:
        QSettings().setValue(KEY, config.id())
    return ok

def forget_credentials():
    manager = QgsApplication.authManager()
    auth_id = QSettings().value(KEY, "")
    if auth_id and not manager.removeAuthenticationConfig(auth_id):
        return False
    QSettings().remove(KEY)
    return True
