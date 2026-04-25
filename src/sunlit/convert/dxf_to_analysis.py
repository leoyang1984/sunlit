from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shapely.geometry import Polygon, mapping

from ..dxf_config import DxfConfigError, DxfStudyConfig, load_dxf_study_config
from .footprint_to_cityjson import _compress_vertices, _solid_boundaries


class DxfConversionError(ValueError):
    """Raised when a cleaned DXF file cannot be converted."""


@dataclass(frozen=True)
class DxfConversionResult:
    output_dir: Path
    site_path: Path
    context_path: Path | None
    scheme_path: Path | None
    report_path: Path
    site_polygon_count: int
    context_building_count: int
    scheme_building_count: int


@dataclass(frozen=True)
class DxfPolyline:
    layer: str
    points: list[tuple[float, float]]


def _load_ezdxf():
    try:
        import ezdxf
    except ImportError as exc:
        raise DxfConversionError("ezdxf is required to convert DXF files. Install sunlit[dxf].") from exc
    return ezdxf


def _unit_scale(config: DxfStudyConfig) -> float:
    if config.cad.unit == "m":
        return 1.0
    if config.cad.unit == "mm":
        return 0.001
    raise DxfConversionError(f"Unsupported CAD unit: {config.cad.unit}")


def _transform_point(x: float, y: float, scale: float, north_angle: float) -> tuple[float, float]:
    scaled_x = x * scale
    scaled_y = y * scale
    radians = math.radians(north_angle)
    rotated_x = scaled_x * math.cos(radians) - scaled_y * math.sin(radians)
    rotated_y = scaled_x * math.sin(radians) + scaled_y * math.cos(radians)
    return rotated_x, rotated_y


def _polyline_points(entity, scale: float, north_angle: float) -> list[tuple[float, float]]:
    if entity.dxftype() == "LWPOLYLINE":
        points = []
        for x, y, _start_width, _end_width, bulge in entity.get_points("xyseb"):
            if bulge:
                raise DxfConversionError(
                    f"Layer '{entity.dxf.layer}' contains a bulged polyline segment. "
                    "MVP convert dxf supports straight closed polylines only."
                )
            points.append(_transform_point(float(x), float(y), scale, north_angle))
        return points

    if entity.dxftype() == "POLYLINE":
        return [
            _transform_point(float(vertex.dxf.location.x), float(vertex.dxf.location.y), scale, north_angle)
            for vertex in entity.vertices
        ]

    raise DxfConversionError(f"Unsupported DXF entity type: {entity.dxftype()}")


def _is_closed_polyline(entity) -> bool:
    if entity.dxftype() == "LWPOLYLINE":
        return bool(entity.closed)
    if entity.dxftype() == "POLYLINE":
        return bool(entity.is_closed)
    return False


def _collect_closed_polylines(config_path: Path, config: DxfStudyConfig) -> list[DxfPolyline]:
    dxf_path = config.cad_path(config_path)
    if not dxf_path.exists():
        raise DxfConversionError(f"DXF file does not exist: {dxf_path}")

    ezdxf = _load_ezdxf()
    try:
        doc = ezdxf.readfile(dxf_path)
    except Exception as exc:
        raise DxfConversionError(f"Could not read DXF file: {dxf_path}") from exc

    configured_layers = {config.layers.site, *config.layers.context.keys(), *config.layers.scheme.keys()}
    scale = _unit_scale(config)
    polylines: list[DxfPolyline] = []
    open_layers: list[str] = []

    for entity in doc.modelspace():
        layer = entity.dxf.layer
        if layer not in configured_layers:
            continue
        if entity.dxftype() not in {"LWPOLYLINE", "POLYLINE"}:
            continue
        if not _is_closed_polyline(entity):
            open_layers.append(layer)
            continue
        points = _polyline_points(entity, scale=scale, north_angle=config.cad.north_angle)
        if len(points) < 3:
            raise DxfConversionError(f"Layer '{layer}' contains a closed polyline with fewer than 3 points.")
        polylines.append(DxfPolyline(layer=layer, points=points))

    if open_layers:
        unique_layers = ", ".join(sorted(set(open_layers)))
        raise DxfConversionError(f"Configured DXF layers contain open polylines: {unique_layers}")
    return polylines


def _polygon_from_polyline(polyline: DxfPolyline) -> Polygon:
    polygon = Polygon(polyline.points)
    if polygon.is_empty or not polygon.is_valid:
        raise DxfConversionError(f"Layer '{polyline.layer}' contains an invalid polygon.")
    return polygon


def _write_site_geojson(polylines: list[DxfPolyline], output_path: Path, config: DxfStudyConfig) -> int:
    if len(polylines) != 1:
        raise DxfConversionError(
            f"Site layer '{config.layers.site}' must contain exactly one closed polyline; found {len(polylines)}."
        )
    polygon = _polygon_from_polyline(polylines[0])
    feature = {
        "type": "Feature",
        "properties": {
            "source": "dxf",
            "layer": config.layers.site,
            "coordinate_system": "local_meters",
        },
        "geometry": mapping(polygon),
    }
    geojson = {"type": "FeatureCollection", "features": [feature]}
    output_path.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1


def _cityjson_from_building_polylines(
    polylines: list[DxfPolyline],
    layer_heights: dict[str, float],
    role: str,
) -> dict[str, Any]:
    vertices: list[list[float]] = []
    city_objects: dict[str, Any] = {}

    for index, polyline in enumerate(polylines, start=1):
        polygon = _polygon_from_polyline(polyline)
        height = layer_heights[polyline.layer]
        object_id = f"{role}-{index}"
        boundaries = _solid_boundaries(vertices, polygon, height)
        city_objects[object_id] = {
            "type": "Building",
            "attributes": {
                "name": object_id,
                "source": "dxf",
                "role": role,
                "layer": polyline.layer,
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
        raise DxfConversionError(f"No {role} building polylines were found.")

    compressed_vertices, transform = _compress_vertices(vertices)
    return {
        "type": "CityJSON",
        "version": "1.1",
        "transform": transform,
        "CityObjects": city_objects,
        "vertices": compressed_vertices,
    }


def _write_cityjson(
    polylines: list[DxfPolyline],
    layer_heights: dict[str, float],
    role: str,
    output_path: Path,
) -> int:
    if not layer_heights:
        return 0
    role_polylines = [polyline for polyline in polylines if polyline.layer in layer_heights]
    missing_layers = [layer for layer in layer_heights if not any(polyline.layer == layer for polyline in role_polylines)]
    if missing_layers:
        raise DxfConversionError(f"No closed building polylines found for layer(s): {', '.join(missing_layers)}")
    cityjson = _cityjson_from_building_polylines(role_polylines, layer_heights, role)
    output_path.write_text(json.dumps(cityjson, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(cityjson["CityObjects"])


def _analysis_command(
    config: DxfStudyConfig,
    result: DxfConversionResult,
    output_dir: Path,
    include_context: bool,
    include_scheme: bool,
) -> list[str]:
    lines = ["sunlit analyze \\"]
    if include_context and result.context_path:
        lines.append(f"  --context {result.context_path} \\")
    if include_scheme and result.scheme_path:
        lines.append(f"  --scheme {result.scheme_path} \\")
    lines.extend(
        [
            f"  --boundary {result.site_path} \\",
            f"  --lat {config.project.location.lat:g} --lon {config.project.location.lon:g} \\",
            f"  --date {config.analysis.date.isoformat()} \\",
            f"  --time-start {config.analysis.time_start} --time-end {config.analysis.time_end} \\",
            f"  --time-step {config.analysis.time_step} \\",
            f"  --grid-size {config.analysis.grid_size:g} \\",
            f"  --threshold {config.analysis.threshold:g} \\",
            f"  --timezone {config.project.location.timezone} \\",
            f"  --output {output_dir}",
        ]
    )
    return lines


def _render_conversion_report(
    config_path: Path,
    config: DxfStudyConfig,
    result: DxfConversionResult,
) -> str:
    lines = [
        "# DXF Conversion Report",
        "",
        f"- Config: `{config_path}`",
        f"- DXF: `{config.cad_path(config_path)}`",
        f"- CAD unit: `{config.cad.unit}`",
        f"- North angle: {config.cad.north_angle:g}",
        "",
        "## Outputs",
        "",
        f"- Site boundary: `{result.site_path}`",
    ]
    if result.context_path:
        lines.append(f"- Context CityJSON: `{result.context_path}`")
    if result.scheme_path:
        lines.append(f"- Scheme CityJSON: `{result.scheme_path}`")
    lines.extend(
        [
            "",
            "## Counts",
            "",
            f"- Site boundary polygons: {result.site_polygon_count}",
            f"- Context buildings: {result.context_building_count}",
            f"- Scheme buildings: {result.scheme_building_count}",
            "",
            "## Suggested Analysis Commands",
            "",
        ]
    )

    if result.context_path:
        lines.extend(
            [
                "### Baseline Context",
                "",
                "```bash",
                *_analysis_command(
                    config=config,
                    result=result,
                    output_dir=result.output_dir / "baseline",
                    include_context=True,
                    include_scheme=False,
                ),
                "```",
                "",
            ]
        )

    if result.scheme_path:
        command_title = "### With Scheme" if result.context_path else "### Scheme Only"
        lines.extend(
            [
                command_title,
                "",
                "```bash",
                *_analysis_command(
                    config=config,
                    result=result,
                    output_dir=result.output_dir / "with-scheme",
                    include_context=bool(result.context_path),
                    include_scheme=True,
                ),
                "```",
                "",
            ]
        )

    if not result.context_path and not result.scheme_path:
        lines.extend(
            [
                "No analysis command was generated because no building CityJSON outputs were configured.",
                "",
            ]
        )

    lines.extend(
        [
            "## Full Workflow",
            "",
            "```bash",
            f"sunlit convert dxf --config {config_path} --output {result.output_dir}",
            "",
        ]
    )
    if result.context_path:
        lines.extend(_analysis_command(config, result, result.output_dir / "baseline", True, False))
        lines.append("")
    if result.scheme_path:
        lines.extend(_analysis_command(config, result, result.output_dir / "with-scheme", bool(result.context_path), True))
    lines.extend(["```", ""])
    return "\n".join(lines)


def convert_dxf_to_analysis_inputs(config_path: Path, output_dir: Path) -> DxfConversionResult:
    try:
        config = load_dxf_study_config(config_path)
    except DxfConfigError as exc:
        raise DxfConversionError(str(exc)) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    polylines = _collect_closed_polylines(config_path=config_path, config=config)

    site_path = output_dir / "site.geojson"
    context_path = output_dir / "context.cityjson" if config.layers.context else None
    scheme_path = output_dir / "scheme.cityjson" if config.layers.scheme else None
    report_path = output_dir / "conversion_report.md"

    site_polylines = [polyline for polyline in polylines if polyline.layer == config.layers.site]
    site_polygon_count = _write_site_geojson(site_polylines, site_path, config)

    context_count = 0
    if context_path:
        context_count = _write_cityjson(
            polylines=polylines,
            layer_heights={name: layer.height for name, layer in config.layers.context.items()},
            role="context",
            output_path=context_path,
        )

    scheme_count = 0
    if scheme_path:
        scheme_count = _write_cityjson(
            polylines=polylines,
            layer_heights={name: layer.height for name, layer in config.layers.scheme.items()},
            role="scheme",
            output_path=scheme_path,
        )

    result = DxfConversionResult(
        output_dir=output_dir,
        site_path=site_path,
        context_path=context_path,
        scheme_path=scheme_path,
        report_path=report_path,
        site_polygon_count=site_polygon_count,
        context_building_count=context_count,
        scheme_building_count=scheme_count,
    )
    report_path.write_text(_render_conversion_report(config_path, config, result), encoding="utf-8")
    return result
