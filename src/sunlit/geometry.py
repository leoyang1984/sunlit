from pathlib import Path
from typing import Any, Optional

import numpy as np
import trimesh
from cjio import cityjson

from .constants import SUPPORTED_CITYJSON_SUFFIXES


class GeometryLoadError(ValueError):
    """Raised when a CityJSON file cannot be converted into analysis geometry."""


def validate_cityjson_path(path: Path) -> None:
    suffix = path.name.lower()
    if not suffix.endswith(SUPPORTED_CITYJSON_SUFFIXES):
        allowed = ", ".join(SUPPORTED_CITYJSON_SUFFIXES)
        raise GeometryLoadError(f"Unsupported CityJSON extension. Expected one of: {allowed}")
    if not path.exists():
        raise GeometryLoadError(f"CityJSON file does not exist: {path}")


def load_cityjson(path: Path) -> cityjson.CityJSON:
    validate_cityjson_path(path)
    with path.open() as file:
        return cityjson.reader(file)


def transformed_vertices(cj: cityjson.CityJSON) -> np.ndarray:
    vertices = np.array(cj.j["vertices"], dtype=float)
    transform = cj.j.get("transform", {})
    scale = np.array(transform.get("scale", [1, 1, 1]), dtype=float)
    translate = np.array(transform.get("translate", [0, 0, 0]), dtype=float)
    return vertices * scale + translate


def surfaces_for_geometry(geometry: dict[str, Any]) -> list[list[list[int]]]:
    boundaries = geometry.get("boundaries", [])
    geometry_type = geometry.get("type")
    if geometry_type in ("MultiSurface", "CompositeSurface"):
        return boundaries
    if geometry_type == "Solid":
        return [surface for shell in boundaries for surface in shell]
    if geometry_type in ("MultiSolid", "CompositeSolid"):
        return [surface for solid in boundaries for shell in solid for surface in shell]
    return []


def cityjson_buildings_to_mesh(cj: cityjson.CityJSON) -> tuple[trimesh.Trimesh, int]:
    vertices = transformed_vertices(cj)
    faces: list[list[int]] = []
    building_count = 0

    for city_object in cj.j.get("CityObjects", {}).values():
        if city_object.get("type") != "Building":
            continue
        building_count += 1
        for geometry in city_object.get("geometry", []):
            for surface in surfaces_for_geometry(geometry):
                if not surface:
                    continue
                ring = surface[0]
                for index in range(1, len(ring) - 1):
                    faces.append([ring[0], ring[index], ring[index + 1]])

    if not faces:
        raise GeometryLoadError("No Building surfaces could be converted into mesh faces.")

    mesh = trimesh.Trimesh(vertices=vertices, faces=np.array(faces), process=False)
    return mesh, building_count


def load_cityjson_building_mesh(path: Path) -> tuple[trimesh.Trimesh, int, Optional[str]]:
    cj = load_cityjson(path)
    metadata = cj.j.get("metadata", {})
    reference_system = metadata.get("referenceSystem")
    mesh, building_count = cityjson_buildings_to_mesh(cj)
    return mesh, building_count, reference_system
