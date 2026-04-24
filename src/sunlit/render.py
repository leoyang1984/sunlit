import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "sunlit-matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import MultiPolygon, Polygon

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


def render_heatmap(
    result: AnalysisResult,
    boundary_path: Path,
    output_path: Path,
    dpi: int = 300,
) -> Path:
    if not result.evaluation_points:
        raise RenderError("Analysis result contains no evaluation points.")

    boundary = load_boundary(boundary_path)
    xs = np.array([point.x for point in result.evaluation_points])
    ys = np.array([point.y for point in result.evaluation_points])
    hours = np.array([point.sunlit_minutes / 60 for point in result.evaluation_points])

    fig, ax = plt.subplots(figsize=(7, 6), constrained_layout=True)
    ax.set_facecolor("#f3f4f6")
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
        linewidths=0,
    )
    _plot_boundary(ax, boundary)

    padding = _axis_padding(result.grid_bounds)
    ax.set_xlim(result.grid_bounds["xmin"] - padding, result.grid_bounds["xmax"] + padding)
    ax.set_ylim(result.grid_bounds["ymin"] - padding, result.grid_bounds["ymax"] + padding)
    ax.set_aspect("equal", adjustable="box")
    mode_name = _english_mode_name(result.mode.display_name)
    ax.set_title(f"{mode_name} | {result.config.date} {result.config.time_start}-{result.config.time_end}", fontsize=10)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(color="white", linewidth=0.5)

    colorbar = fig.colorbar(scatter, ax=ax)
    colorbar.set_label("Sunlight hours")
    colorbar.ax.axhline(
        result.config.threshold_hours,
        color="#E8751A",
        linewidth=1.0,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
    return output_path
