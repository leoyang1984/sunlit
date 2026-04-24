import json
import math
from pathlib import Path
from typing import Any, Optional

from shapely.geometry import Polygon

from .footprint_to_cityjson import _compress_vertices, _solid_boundaries


class ObjConversionError(ValueError):
    """Raised when an OBJ file cannot be converted to CityJSON."""


def _load_meta(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ObjConversionError(f"Meta file does not exist: {path}")
    with path.open() as file:
        meta = json.load(file)
    buildings = meta.get("buildings", [])
    if not isinstance(buildings, list) or not buildings:
        raise ObjConversionError("Meta JSON must contain a non-empty 'buildings' list.")
    return meta


def _meta_by_group(meta: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for building in meta.get("buildings", []):
        group = building.get("obj_group")
        if not group:
            raise ObjConversionError("Each building in meta JSON must include 'obj_group'.")
        result[str(group)] = building
    return result


def _parse_obj(path: Path) -> tuple[list[tuple[float, float, float]], dict[str, list[list[int]]]]:
    if not path.exists():
        raise ObjConversionError(f"OBJ file does not exist: {path}")
    vertices: list[tuple[float, float, float]] = []
    groups: dict[str, list[list[int]]] = {}
    current_group = "default"
    groups[current_group] = []

    with path.open() as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if parts[0] == "v":
                if len(parts) < 4:
                    raise ObjConversionError("OBJ vertex line must contain x y z.")
                vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif parts[0] in ("o", "g"):
                current_group = " ".join(parts[1:]) or "default"
                groups.setdefault(current_group, [])
            elif parts[0] == "f":
                if len(parts) < 4:
                    raise ObjConversionError("OBJ face must contain at least 3 vertices.")
                face = []
                for token in parts[1:]:
                    vertex_index = int(token.split("/")[0])
                    if vertex_index < 0:
                        vertex_index = len(vertices) + vertex_index + 1
                    face.append(vertex_index - 1)
                groups.setdefault(current_group, []).append(face)
    return vertices, {group: faces for group, faces in groups.items() if faces}


def _transform_xy(x: float, y: float, meta: dict[str, Any]) -> tuple[float, float]:
    rotation = math.radians(float(meta.get("rotation_degrees", 0.0)))
    rotated_x = x * math.cos(rotation) - y * math.sin(rotation)
    rotated_y = x * math.sin(rotation) + y * math.cos(rotation)
    origin = meta.get("origin", {})
    offset_x = float(origin.get("x", origin.get("lon", 0.0)))
    offset_y = float(origin.get("y", origin.get("lat", 0.0)))
    return rotated_x + offset_x, rotated_y + offset_y


def _footprint_from_group(
    vertices: list[tuple[float, float, float]],
    faces: list[list[int]],
    meta: dict[str, Any],
) -> Polygon:
    if len(faces) != 1:
        raise ObjConversionError("MVP convert obj supports footprint groups with exactly one face.")
    coords = []
    for vertex_index in faces[0]:
        x, y, _ = vertices[vertex_index]
        coords.append(_transform_xy(x, y, meta))
    polygon = Polygon(coords)
    if not polygon.is_valid or polygon.is_empty:
        raise ObjConversionError("OBJ footprint face did not produce a valid polygon.")
    return polygon


def _height(building_meta: dict[str, Any]) -> float:
    if "height" in building_meta:
        height = float(building_meta["height"])
    elif "floors" in building_meta and "floor_height" in building_meta:
        height = float(building_meta["floors"]) * float(building_meta["floor_height"])
    else:
        raise ObjConversionError("Each OBJ building meta entry must include height or floors + floor_height.")
    if height <= 0:
        raise ObjConversionError("Building height must be greater than 0.")
    return height


def convert_obj_to_cityjson(
    obj_path: Path,
    meta_path: Path,
    output_path: Path,
    crs: Optional[str] = None,
) -> dict[str, Any]:
    meta = _load_meta(meta_path)
    vertices, groups = _parse_obj(obj_path)
    buildings = _meta_by_group(meta)
    cityjson_vertices: list[list[float]] = []
    city_objects: dict[str, Any] = {}
    output_crs = crs or meta.get("crs")

    for group_name, building_meta in buildings.items():
        if group_name not in groups:
            raise ObjConversionError(f"OBJ group '{group_name}' was not found.")
        height = _height(building_meta)
        polygon = _footprint_from_group(vertices, groups[group_name], meta)
        boundaries = _solid_boundaries(cityjson_vertices, polygon, height)
        object_id = str(building_meta.get("id") or group_name)
        city_objects[object_id] = {
            "type": "Building",
            "attributes": {
                "name": building_meta.get("name", object_id),
                "height": height,
                "floors": building_meta.get("floors"),
            },
            "geometry": [
                {
                    "type": "Solid",
                    "lod": "1.0",
                    "boundaries": boundaries,
                }
            ],
        }

    compressed_vertices, transform = _compress_vertices(cityjson_vertices)
    cityjson: dict[str, Any] = {
        "type": "CityJSON",
        "version": "1.1",
        "transform": transform,
        "CityObjects": city_objects,
        "vertices": compressed_vertices,
    }
    if output_crs:
        cityjson["metadata"] = {"referenceSystem": output_crs}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(cityjson, ensure_ascii=False, indent=2), encoding="utf-8")
    return cityjson

