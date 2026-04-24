import json
from pathlib import Path
from typing import Any, Optional

from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.geometry.polygon import orient

from ..grid import looks_like_wgs84


class FootprintConversionError(ValueError):
    """Raised when GeoJSON footprints cannot be converted to CityJSON."""


def _load_features(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FootprintConversionError(f"GeoJSON file does not exist: {path}")
    with path.open() as file:
        data = json.load(file)
    if data.get("type") == "FeatureCollection":
        return data.get("features", [])
    if data.get("type") == "Feature":
        return [data]
    if data.get("type") in ("Polygon", "MultiPolygon"):
        return [{"type": "Feature", "properties": {}, "geometry": data}]
    raise FootprintConversionError("Input must be GeoJSON FeatureCollection, Feature, Polygon, or MultiPolygon.")


def _as_polygons(geometry: dict[str, Any]) -> list[Polygon]:
    shapely_geometry = shape(geometry)
    if isinstance(shapely_geometry, Polygon):
        return [shapely_geometry]
    if isinstance(shapely_geometry, MultiPolygon):
        return list(shapely_geometry.geoms)
    raise FootprintConversionError("Only Polygon and MultiPolygon footprints are supported.")


def _height(properties: dict[str, Any], height_field: str, default_height: float) -> float:
    value = properties.get(height_field, default_height)
    try:
        height = float(value)
    except (TypeError, ValueError) as exc:
        raise FootprintConversionError(f"Height field '{height_field}' must be numeric.") from exc
    if height <= 0:
        raise FootprintConversionError("Building height must be greater than 0.")
    return height


def _append_vertex(vertices: list[list[float]], vertex: tuple[float, float, float]) -> int:
    vertices.append([float(vertex[0]), float(vertex[1]), float(vertex[2])])
    return len(vertices) - 1


def _solid_boundaries(vertices: list[list[float]], polygon: Polygon, height: float) -> list[list[list[int]]]:
    polygon = orient(polygon, sign=1.0)
    coords = list(polygon.exterior.coords)[:-1]
    if len(coords) < 3:
        raise FootprintConversionError("Footprint polygon must have at least 3 distinct vertices.")

    bottom = [_append_vertex(vertices, (x, y, 0.0)) for x, y in coords]
    top = [_append_vertex(vertices, (x, y, height)) for x, y in coords]
    surfaces: list[list[list[int]]] = []
    surfaces.append([list(reversed(bottom))])
    surfaces.append([top])
    for index in range(len(coords)):
        next_index = (index + 1) % len(coords)
        surfaces.append([[bottom[index], bottom[next_index], top[next_index], top[index]]])
    return [surfaces]


def _compress_vertices(vertices: list[list[float]]) -> tuple[list[list[int]], dict[str, list[float]]]:
    mins = [min(vertex[axis] for vertex in vertices) for axis in range(3)]
    scale = [0.001, 0.001, 0.001]
    compressed = [
        [int(round((vertex[axis] - mins[axis]) / scale[axis])) for axis in range(3)]
        for vertex in vertices
    ]
    return compressed, {"scale": scale, "translate": mins}


def convert_footprint_to_cityjson(
    input_path: Path,
    output_path: Path,
    height_field: str = "height",
    default_height: float = 10.0,
    crs: Optional[str] = None,
) -> dict[str, Any]:
    features = _load_features(input_path)
    vertices: list[list[float]] = []
    city_objects: dict[str, Any] = {}
    building_index = 0

    for feature in features:
        geometry = feature.get("geometry")
        if not geometry:
            continue
        properties = feature.get("properties", {})
        polygons = _as_polygons(geometry)
        height = _height(properties, height_field, default_height)
        for polygon in polygons:
            if polygon.is_empty:
                continue
            if looks_like_wgs84(polygon):
                raise FootprintConversionError(
                    "Footprint coordinates look like WGS84 longitude/latitude. "
                    "MVP requires projected meter-based coordinates."
                )
            building_index += 1
            object_id = str(properties.get("id") or properties.get("name") or f"building-{building_index}")
            boundaries = _solid_boundaries(vertices, polygon, height)
            city_objects[object_id] = {
                "type": "Building",
                "attributes": {
                    "name": properties.get("name", object_id),
                    "height": height,
                },
                "geometry": [
                    {
                        "type": "Solid",
                        "lod": "1.0",
                        "boundaries": boundaries,
                    }
                ],
            }
    if not city_objects:
        raise FootprintConversionError("No valid building footprints were found.")

    compressed_vertices, transform = _compress_vertices(vertices)
    metadata: dict[str, Any] = {}
    if crs:
        metadata["referenceSystem"] = crs

    cityjson: dict[str, Any] = {
        "type": "CityJSON",
        "version": "1.1",
        "transform": transform,
        "CityObjects": city_objects,
        "vertices": compressed_vertices,
    }
    if metadata:
        cityjson["metadata"] = metadata

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(cityjson, ensure_ascii=False, indent=2), encoding="utf-8")
    return cityjson
