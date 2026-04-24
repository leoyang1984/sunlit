import json
from pathlib import Path
from typing import Any, Union

import numpy as np
from shapely.geometry import MultiPolygon, Point, Polygon, shape

from .models import EvaluationPoint


class GridError(ValueError):
    """Raised when a site boundary cannot produce a valid analysis grid."""


BoundaryGeometry = Union[Polygon, MultiPolygon]


def _geometry_from_geojson(data: dict[str, Any]) -> BoundaryGeometry:
    geojson_type = data.get("type")
    if geojson_type == "FeatureCollection":
        polygons = [
            shape(feature["geometry"])
            for feature in data.get("features", [])
            if feature.get("geometry", {}).get("type") in ("Polygon", "MultiPolygon")
        ]
        if not polygons:
            raise GridError("GeoJSON FeatureCollection does not contain Polygon or MultiPolygon features.")
        flattened = []
        for polygon in polygons:
            if isinstance(polygon, MultiPolygon):
                flattened.extend(polygon.geoms)
            else:
                flattened.append(polygon)
        return MultiPolygon(flattened) if len(flattened) > 1 else flattened[0]
    if geojson_type == "Feature":
        return shape(data["geometry"])
    if geojson_type in ("Polygon", "MultiPolygon"):
        return shape(data)
    raise GridError("Boundary GeoJSON must be a Polygon, MultiPolygon, Feature, or FeatureCollection.")


def load_boundary(path: Path) -> BoundaryGeometry:
    if not path.exists():
        raise GridError(f"Boundary file does not exist: {path}")
    with path.open() as file:
        boundary = _geometry_from_geojson(json.load(file))
    if not isinstance(boundary, (Polygon, MultiPolygon)):
        raise GridError("Boundary GeoJSON must resolve to Polygon or MultiPolygon geometry.")
    if boundary.is_empty:
        raise GridError("Boundary geometry is empty.")
    return boundary


def looks_like_wgs84(boundary: BoundaryGeometry) -> bool:
    minx, miny, maxx, maxy = boundary.bounds
    return -180 <= minx <= 180 and -180 <= maxx <= 180 and -90 <= miny <= 90 and -90 <= maxy <= 90


def generate_grid_inside(
    boundary: BoundaryGeometry,
    spacing: float,
    z: float = 0.0,
) -> list[EvaluationPoint]:
    if spacing <= 0:
        raise GridError("Grid size must be greater than 0.")
    if looks_like_wgs84(boundary):
        raise GridError(
            "Boundary coordinates look like WGS84 longitude/latitude. "
            "MVP requires a projected meter-based boundary."
        )

    minx, miny, maxx, maxy = boundary.bounds
    xs = np.arange(minx, maxx + spacing, spacing)
    ys = np.arange(miny, maxy + spacing, spacing)
    points: list[EvaluationPoint] = []
    for x in xs:
        for y in ys:
            if boundary.contains(Point(float(x), float(y))):
                points.append(EvaluationPoint(x=float(x), y=float(y), z=z))
    if not points:
        raise GridError("Boundary and grid size produced no evaluation points.")
    return points


def grid_bounds(points: list[EvaluationPoint]) -> dict[str, float]:
    xs = [point.x for point in points]
    ys = [point.y for point in points]
    return {"xmin": min(xs), "ymin": min(ys), "xmax": max(xs), "ymax": max(ys)}
