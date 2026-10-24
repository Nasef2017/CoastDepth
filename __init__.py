"""CoastDepth: standalone QGIS plugin."""

def classFactory(iface):
    from .plugin import CoastDepthPlugin
    return CoastDepthPlugin(iface)
