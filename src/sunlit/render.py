import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "sunlit-matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch, Polygon as MplPolygon
from matplotlib.collections import PatchCollection
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from .geometry import load_cityjson, surfaces_for_geometry, transformed_vertices
from .grid import BoundaryGeometry, load_boundary
from .models import AnalysisResult


class RenderError(ValueError):
    """Raised when an analysis result cannot be rendered."""


def _plot_boundary(ax, boundary: BoundaryGeometry) -> None:
    polygons = boundary.geoms if isinstance(boundary, MultiPolygon) else [boundary]
    for polygon in polygons:
        exterior = np.array(polygon.exterior.coords)
        ax.plot(exterior[:, 0], exterior[:, 1], color="#E8751A", linewidth=1.8)
        for interior in polygon.interiors:
            ring = np.array(interior.coords)
            ax.plot(ring[:, 0], ring[:, 1], color="#E8751A", linewidth=1.0, linestyle="--")


def _surface_polygon(vertices: np.ndarray, surface: list[list[int]]) -> Polygon | None:
    if not surface or len(surface[0]) < 3:
        return None
    ring = surface[0]
    coords = [(float(vertices[index][0]), float(vertices[index][1])) for index in ring]
    polygon = Polygon(coords)
    if polygon.is_empty or polygon.area <= 0:
        return None
    if not polygon.is_valid:
        polygon = polygon.buffer(0)
    if not isinstance(polygon, Polygon) or polygon.is_empty or polygon.area <= 0:
        return None
    return polygon


def _footprint_for_city_object(vertices: np.ndarray, city_object: dict) -> Polygon | None:
    candidates: list[tuple[float, Polygon]] = []
    all_points: list[tuple[float, float]] = []

    for geometry in city_object.get("geometry", []):
        for surface in surfaces_for_geometry(geometry):
            if not surface or len(surface[0]) < 3:
                continue
            ring = surface[0]
            surface_vertices = vertices[ring]
            all_points.extend((float(vertex[0]), float(vertex[1])) for vertex in surface_vertices)
            z_range = float(surface_vertices[:, 2].max() - surface_vertices[:, 2].min())
            if z_range <= 0.05:
                polygon = _surface_polygon(vertices, surface)
                if polygon is not None:
                    candidates.append((float(surface_vertices[:, 2].mean()), polygon))

    if candidates:
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]
    if len(all_points) >= 3:
        hull = MultiPolygon([Polygon(all_points).convex_hull]).geoms[0]
        return hull if isinstance(hull, Polygon) and not hull.is_empty else None
    return None


def load_cityjson_footprints(path: Path) -> list[Polygon]:
    cj = load_cityjson(path)
    vertices = transformed_vertices(cj)
    footprints: list[Polygon] = []
    for city_object in cj.j.get("CityObjects", {}).values():
        if city_object.get("type") != "Building":
            continue
        footprint = _footprint_for_city_object(vertices, city_object)
        if footprint is not None:
            footprints.append(footprint)
    return footprints


def _plot_building_footprints(ax, footprints: list[Polygon], role: str) -> None:
    if not footprints:
        return
    style = {
        "context": {"face": "#6B7280", "edge": "#374151", "alpha": 0.28, "linewidth": 0.9},
        "scheme": {"face": "#2563EB", "edge": "#1D4ED8", "alpha": 0.34, "linewidth": 1.2},
    }[role]
    patches = [
        MplPolygon(np.array(polygon.exterior.coords), closed=True)
        for polygon in footprints
        if not polygon.is_empty and polygon.area > 0
    ]
    if not patches:
        return
    collection = PatchCollection(
        patches,
        facecolor=style["face"],
        edgecolor=style["edge"],
        alpha=style["alpha"],
        linewidth=style["linewidth"],
        zorder=4,
    )
    ax.add_collection(collection)


def _axis_padding(bounds: dict[str, float]) -> float:
    width = bounds["xmax"] - bounds["xmin"]
    height = bounds["ymax"] - bounds["ymin"]
    return max(width, height, 1.0) * 0.08


def _english_mode_name(display_name: str) -> str:
    labels = {
        "场地前期评估": "Site Study",
        "方案自评": "Scheme Self-Assessment",
        "方案对周边影响参考": "Neighbor Impact Reference",
    }
    return labels.get(display_name, display_name)


def _combined_bounds(
    boundary: BoundaryGeometry,
    point_bounds: dict[str, float],
    footprints: list[Polygon],
) -> dict[str, float]:
    geometries = [boundary, *footprints]
    if geometries:
        minx, miny, maxx, maxy = unary_union(geometries).bounds
        return {
            "xmin": min(point_bounds["xmin"], float(minx)),
            "ymin": min(point_bounds["ymin"], float(miny)),
            "xmax": max(point_bounds["xmax"], float(maxx)),
            "ymax": max(point_bounds["ymax"], float(maxy)),
        }
    return point_bounds


def _nice_scale_length(width: float) -> float:
    raw = max(width, 1.0) / 5
    exponent = np.floor(np.log10(raw))
    base = raw / (10**exponent)
    if base >= 5:
        nice = 5
    elif base >= 2:
        nice = 2
    else:
        nice = 1
    return float(nice * (10**exponent))


def _add_scale_bar(ax, bounds: dict[str, float]) -> None:
    width = bounds["xmax"] - bounds["xmin"]
    height = bounds["ymax"] - bounds["ymin"]
    length = _nice_scale_length(width)
    x0 = bounds["xmin"] + width * 0.06
    y0 = bounds["ymin"] + height * 0.06
    ax.plot([x0, x0 + length], [y0, y0], color="#111827", linewidth=2.0, solid_capstyle="butt", zorder=7)
    ax.text(x0 + length / 2, y0 + height * 0.015, f"{length:g} m", ha="center", va="bottom", fontsize=7)


def _add_north_arrow(ax, bounds: dict[str, float]) -> None:
    width = bounds["xmax"] - bounds["xmin"]
    height = bounds["ymax"] - bounds["ymin"]
    x = bounds["xmax"] - width * 0.08
    y = bounds["ymax"] - height * 0.08
    arrow_length = height * 0.11
    ax.annotate(
        "",
        xy=(x, y),
        xytext=(x, y - arrow_length),
        arrowprops={"arrowstyle": "-|>", "color": "#111827", "lw": 1.4},
        zorder=8,
    )
    ax.text(x, y + height * 0.015, "N", ha="center", va="bottom", fontsize=8, fontweight="bold")


def render_heatmap(
    result: AnalysisResult,
    boundary_path: Path,
    output_path: Path,
    scheme_path: Path | None = None,
    context_path: Path | None = None,
    dpi: int = 300,
) -> Path:
    if not result.evaluation_points:
        raise RenderError("Analysis result contains no evaluation points.")

    boundary = load_boundary(boundary_path)
    context_footprints = load_cityjson_footprints(context_path) if context_path else []
    scheme_footprints = load_cityjson_footprints(scheme_path) if scheme_path else []
    all_footprints = [*context_footprints, *scheme_footprints]
    xs = np.array([point.x for point in result.evaluation_points])
    ys = np.array([point.y for point in result.evaluation_points])
    hours = np.array([point.sunlit_minutes / 60 for point in result.evaluation_points])

    fig, ax = plt.subplots(figsize=(7.5, 6.4), constrained_layout=True)
    ax.set_facecolor("#F3F4F1")
    size = max(18, min(120, 90 * (2.0 / max(result.config.grid_size_meters, 0.1))))
    scatter = ax.scatter(
        xs,
        ys,
        c=hours,
        s=size,
        cmap="viridis",
        vmin=0,
        vmax=max(result.config.threshold_hours, float(hours.max()), 0.1),
        marker="s",
        alpha=0.88,
        linewidths=0,
        zorder=3,
    )
    _plot_building_footprints(ax, context_footprints, "context")
    _plot_building_footprints(ax, scheme_footprints, "scheme")
    _plot_boundary(ax, boundary)

    render_bounds = _combined_bounds(boundary, result.grid_bounds, all_footprints)
    padding = _axis_padding(render_bounds)
    view_bounds = {
        "xmin": render_bounds["xmin"] - padding,
        "ymin": render_bounds["ymin"] - padding,
        "xmax": render_bounds["xmax"] + padding,
        "ymax": render_bounds["ymax"] + padding,
    }
    ax.set_xlim(view_bounds["xmin"], view_bounds["xmax"])
    ax.set_ylim(view_bounds["ymin"], view_bounds["ymax"])
    ax.set_aspect("equal", adjustable="box")
    mode_name = _english_mode_name(result.mode.display_name)
    ax.set_title(
        (
            f"{mode_name} | {result.config.date} {result.config.time_start}-{result.config.time_end} | "
            f"threshold {result.config.threshold_hours:g}h"
        ),
        fontsize=10,
    )
    ax.set_xlabel("Local X (m)")
    ax.set_ylabel("Local Y (m)")
    ax.grid(color="white", linewidth=0.6)

    if len(np.unique(hours)) > 1 and float(hours.min()) < result.config.threshold_hours < float(hours.max()):
        try:
            ax.tricontour(
                xs,
                ys,
                hours,
                levels=[result.config.threshold_hours],
                colors=["#111827"],
                linewidths=0.9,
                linestyles="--",
                zorder=5,
            )
        except Exception:
            pass
    _add_scale_bar(ax, view_bounds)
    _add_north_arrow(ax, view_bounds)

    colorbar = fig.colorbar(scatter, ax=ax)
    colorbar.set_label("Sunlight hours")
    colorbar.ax.axhline(
        result.config.threshold_hours,
        color="#E8751A",
        linewidth=1.0,
    )
    colorbar.ax.text(1.8, result.config.threshold_hours, "threshold", va="center", fontsize=7, color="#E8751A")
    handles = []
    if context_footprints:
        handles.append(Patch(facecolor="#6B7280", edgecolor="#374151", alpha=0.28, label="Context"))
    if scheme_footprints:
        handles.append(Patch(facecolor="#2563EB", edgecolor="#1D4ED8", alpha=0.34, label="Scheme"))
    if handles:
        ax.legend(handles=handles, loc="lower right", frameon=True, framealpha=0.9, fontsize=8)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    return output_path
