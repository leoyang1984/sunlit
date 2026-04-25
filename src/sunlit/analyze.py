import math
from pathlib import Path
from typing import Optional

import numpy as np
import trimesh

from . import __version__
from .constants import DISCLAIMER_TEXT_ZH
from .geometry import load_cityjson_building_mesh
from .grid import boundary_declares_local_meters, generate_grid_inside, grid_bounds, load_boundary
from .models import AnalysisConfig, AnalysisMode, AnalysisResult, EvaluationPoint, Statistics, SunPosition
from .sun_position import compute_sun_positions


class AnalysisError(ValueError):
    """Raised when the analysis cannot be completed."""


def infer_mode(has_scheme: bool, has_context: bool) -> AnalysisMode:
    if has_scheme and has_context:
        display_name = "方案对周边影响参考"
    elif has_scheme:
        display_name = "方案自评"
    else:
        display_name = "场地前期评估"
    return AnalysisMode(has_scheme=has_scheme, has_context=has_context, display_name=display_name)


def sun_vector(azimuth: float, altitude: float) -> np.ndarray:
    azimuth_radians = math.radians(azimuth)
    altitude_radians = math.radians(altitude)
    return np.array(
        [
            math.sin(azimuth_radians) * math.cos(altitude_radians),
            math.cos(azimuth_radians) * math.cos(altitude_radians),
            math.sin(altitude_radians),
        ],
        dtype=float,
    )


def load_obstacle_mesh(paths: list[Path]) -> trimesh.Trimesh:
    meshes = []
    for path in paths:
        mesh, _, _ = load_cityjson_building_mesh(path)
        meshes.append(mesh)
    if not meshes:
        raise AnalysisError("Provide at least one of --scheme or --context.")
    if len(meshes) == 1:
        return meshes[0]
    return trimesh.util.concatenate(meshes)


def evaluate_points(
    points: list[EvaluationPoint],
    sun_positions: list[SunPosition],
    mesh: trimesh.Trimesh,
    time_step_minutes: int,
    threshold_hours: float,
) -> list[EvaluationPoint]:
    if not sun_positions:
        raise AnalysisError("No sun positions are above the horizon in the requested time range.")

    coordinates = np.array([[point.x, point.y, point.z] for point in points], dtype=float)
    sunlit_counts = np.zeros(len(points), dtype=int)
    sunlit_slots: list[list[str]] = [[] for _ in points]

    for sun in sun_positions:
        direction = sun_vector(sun.azimuth, sun.altitude)
        directions = np.repeat(direction.reshape(1, 3), len(coordinates), axis=0)
        shadowed = mesh.ray.intersects_any(coordinates, directions)
        lit = ~shadowed
        sunlit_counts += lit.astype(int)
        for index in np.where(lit)[0]:
            sunlit_slots[index].append(sun.timestamp)

    results: list[EvaluationPoint] = []
    threshold_minutes = threshold_hours * 60
    for point, count, slots in zip(points, sunlit_counts, sunlit_slots):
        minutes = float(count * time_step_minutes)
        results.append(
            EvaluationPoint(
                x=point.x,
                y=point.y,
                z=point.z,
                sunlit_minutes=minutes,
                sunlit_intervals=[(slot, slot) for slot in slots],
                meets_threshold=minutes >= threshold_minutes,
            )
        )
    return results


def compute_statistics(points: list[EvaluationPoint], grid_size_meters: float) -> Statistics:
    total = len(points)
    qualified = sum(1 for point in points if point.meets_threshold)
    hours = [point.sunlit_minutes / 60 for point in points]
    qualified_pct = qualified / total * 100 if total else 0.0
    return Statistics(
        total_points=total,
        qualified_points=qualified,
        qualified_pct=qualified_pct,
        qualified_area_sqm=qualified * grid_size_meters * grid_size_meters,
        max_hours=max(hours) if hours else 0.0,
        min_hours=min(hours) if hours else 0.0,
        avg_hours=sum(hours) / total if total else 0.0,
    )


def analyze(
    scheme_path: Optional[Path],
    context_path: Optional[Path],
    boundary_path: Path,
    config: AnalysisConfig,
    timezone: str,
) -> AnalysisResult:
    paths = [path for path in (scheme_path, context_path) if path is not None]
    mesh = load_obstacle_mesh(paths)
    boundary = load_boundary(boundary_path)
    points = generate_grid_inside(
        boundary,
        spacing=config.grid_size_meters,
        allow_wgs84_like=boundary_declares_local_meters(boundary_path),
    )
    sun_positions = compute_sun_positions(
        latitude=config.latitude,
        longitude=config.longitude,
        analysis_date=config.date,
        time_start=config.time_start,
        time_end=config.time_end,
        time_step_minutes=config.time_step_minutes,
        timezone=timezone,
    )
    evaluated = evaluate_points(
        points=points,
        sun_positions=sun_positions,
        mesh=mesh,
        time_step_minutes=config.time_step_minutes,
        threshold_hours=config.threshold_hours,
    )
    statistics = compute_statistics(evaluated, config.grid_size_meters)
    return AnalysisResult(
        version=__version__,
        mode=infer_mode(scheme_path is not None, context_path is not None),
        config=config,
        sun_positions=sun_positions,
        evaluation_points=evaluated,
        statistics=statistics,
        grid_bounds=grid_bounds(evaluated),
        spatial_patterns={},
        disclaimer=DISCLAIMER_TEXT_ZH,
    )
