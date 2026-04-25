from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .dxf_config import DxfConfigError, DxfStudyConfig, load_dxf_study_config


class DxfInspectionError(ValueError):
    """Raised when a cleaned DXF file cannot be inspected."""


@dataclass(frozen=True)
class LayerInspection:
    layer: str
    role: str
    height: float | None
    closed_polylines: int
    open_polylines: int


@dataclass(frozen=True)
class DxfInspectionReport:
    config_path: Path
    dxf_path: Path
    layers: list[LayerInspection]
    missing_layers: list[str]
    ignored_entities: int

    @property
    def has_errors(self) -> bool:
        return (
            bool(self.missing_layers)
            or any(layer.open_polylines for layer in self.layers)
            or any(layer.closed_polylines == 0 for layer in self.layers)
        )


def _load_ezdxf():
    try:
        import ezdxf
    except ImportError as exc:
        raise DxfInspectionError("ezdxf is required to inspect DXF files. Install sunlit[dxf].") from exc
    return ezdxf


def _is_closed_polyline(entity) -> bool:
    if entity.dxftype() == "LWPOLYLINE":
        return bool(entity.closed)
    if entity.dxftype() == "POLYLINE":
        return bool(entity.is_closed)
    return False


def _configured_layers(config: DxfStudyConfig) -> dict[str, tuple[str, float | None]]:
    layers: dict[str, tuple[str, float | None]] = {config.layers.site: ("site", None)}
    for layer_name, layer_config in config.layers.context.items():
        layers[layer_name] = ("context", layer_config.height)
    for layer_name, layer_config in config.layers.scheme.items():
        layers[layer_name] = ("scheme", layer_config.height)
    return layers


def inspect_dxf_config(config_path: Path) -> DxfInspectionReport:
    try:
        config = load_dxf_study_config(config_path)
    except DxfConfigError as exc:
        raise DxfInspectionError(str(exc)) from exc

    dxf_path = config.cad_path(config_path)
    if not dxf_path.exists():
        raise DxfInspectionError(f"DXF file does not exist: {dxf_path}")

    ezdxf = _load_ezdxf()
    try:
        doc = ezdxf.readfile(dxf_path)
    except Exception as exc:
        raise DxfInspectionError(f"Could not read DXF file: {dxf_path}") from exc

    configured = _configured_layers(config)
    counts = {
        layer: {"closed": 0, "open": 0}
        for layer in configured
    }
    present_layers: set[str] = set()
    ignored_entities = 0

    for entity in doc.modelspace():
        layer_name = entity.dxf.layer
        if layer_name not in configured:
            ignored_entities += 1
            continue
        present_layers.add(layer_name)
        if entity.dxftype() not in {"LWPOLYLINE", "POLYLINE"}:
            ignored_entities += 1
            continue
        if _is_closed_polyline(entity):
            counts[layer_name]["closed"] += 1
        else:
            counts[layer_name]["open"] += 1

    layers = [
        LayerInspection(
            layer=layer_name,
            role=role,
            height=height,
            closed_polylines=counts[layer_name]["closed"],
            open_polylines=counts[layer_name]["open"],
        )
        for layer_name, (role, height) in configured.items()
    ]
    missing_layers = [layer for layer in configured if layer not in present_layers]
    return DxfInspectionReport(
        config_path=config_path,
        dxf_path=dxf_path,
        layers=layers,
        missing_layers=missing_layers,
        ignored_entities=ignored_entities,
    )


def render_inspection_report(report: DxfInspectionReport) -> str:
    lines = [
        "# DXF Clean Input Inspection",
        "",
        f"- Config: `{report.config_path}`",
        f"- DXF: `{report.dxf_path}`",
        f"- Ignored entities: {report.ignored_entities}",
        "",
        "## Configured Layers",
        "",
        "| Layer | Role | Height | Closed polylines | Open polylines |",
        "|---|---:|---:|---:|---:|",
    ]
    for layer in report.layers:
        height = "" if layer.height is None else f"{layer.height:g}"
        lines.append(
            f"| {layer.layer} | {layer.role} | {height} | {layer.closed_polylines} | {layer.open_polylines} |"
        )

    lines.extend(["", "## Findings", ""])
    empty_layers = [
        layer.layer
        for layer in report.layers
        if layer.layer not in report.missing_layers and layer.closed_polylines == 0
    ]
    if not report.missing_layers and not empty_layers and not any(layer.open_polylines for layer in report.layers):
        lines.append("- No blocking layer or closure issues found.")
    for layer in report.missing_layers:
        lines.append(f"- Missing configured layer: `{layer}`.")
    for layer in empty_layers:
        lines.append(f"- Layer `{layer}` contains no closed polylines.")
    for layer in report.layers:
        if layer.open_polylines:
            lines.append(f"- Layer `{layer.layer}` contains {layer.open_polylines} open polyline(s).")
    lines.append("")
    return "\n".join(lines)
