"""Snapshot ROI on GUI thread, transform and serialize before starting worker."""
import json
from qgis.core import (QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsProject, QgsVectorLayer, Qgis)
from .core.models import Bounds

def snapshot(layer, mode, selected=False):
    if layer is None or not layer.isValid() or not layer.crs().isValid():
        raise ValueError("Choose a valid layer with a defined CRS.")
    if selected and not isinstance(layer, QgsVectorLayer):
        raise ValueError("Selected Features requires a vector layer.")
    polygon = mode == "polygon"
    if polygon and (not isinstance(layer, QgsVectorLayer) or
                    layer.geometryType() != Qgis.GeometryType.Polygon):
        raise ValueError("Polygon ROI requires a polygon vector layer.")
    if polygon or selected:
        if selected and layer.selectedFeatureCount() == 0:
            raise ValueError("No selected features. Select features or disable Selected Features.")
        features = layer.getSelectedFeatures() if selected else layer.getFeatures()
        geometries = []
        for feature in features:
            geom = QgsGeometry(feature.geometry())
            if geom.isNull() or geom.isEmpty():
                continue
            if not geom.isGeosValid():
                raise ValueError("ROI contains invalid geometry. Run Fix Geometries first.")
            geometries.append(geom)
        if not geometries:
            raise ValueError("No nonempty features in ROI.")
        geometry = QgsGeometry.unaryUnion(geometries)
        if geometry.isEmpty():
            raise ValueError("Could not combine ROI features.")
        if not polygon:
            geometry = QgsGeometry.fromRect(geometry.boundingBox())
    else:
        geometry = QgsGeometry.fromRect(layer.extent())
    transform = QgsCoordinateTransform(layer.crs(), QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance())
    geometry = geometry.densifyByCount(20)
    if geometry.transform(transform) != Qgis.GeometryOperationResult.Success or geometry.isEmpty() or not geometry.isGeosValid():
        raise ValueError("ROI transform failed. Check layer CRS and geometry.")
    box = geometry.boundingBox()
    bounds = Bounds(box.xMinimum(), box.yMinimum(), box.xMaximum(), box.yMaximum()).validate()
    return bounds, json.loads(geometry.asJson(15)) if polygon else None
