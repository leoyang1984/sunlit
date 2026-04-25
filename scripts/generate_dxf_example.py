from __future__ import annotations

from pathlib import Path


def _add_closed_lwpolyline(modelspace, layer: str, points: list[tuple[float, float]]) -> None:
    modelspace.add_lwpolyline(points, close=True, dxfattribs={"layer": layer})


def main() -> None:
    try:
        import ezdxf
    except ImportError as exc:
        raise SystemExit("ezdxf is required. Install with: python -m pip install -e '.[dev]'") from exc

    output_dir = Path("examples/dxf")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "project_clean.dxf"

    doc = ezdxf.new("R2010")
    for layer in [
        "红线",
        "周边建筑_低层",
        "周边建筑_高层",
        "场地内保留建筑",
        "方案塔楼",
        "方案裙房",
        "道路_忽略",
    ]:
        doc.layers.add(layer)

    msp = doc.modelspace()
    _add_closed_lwpolyline(msp, "红线", [(0, 0), (120, 0), (120, 80), (0, 80)])
    _add_closed_lwpolyline(msp, "周边建筑_低层", [(-20, -15), (40, -15), (40, -5), (-20, -5)])
    _add_closed_lwpolyline(msp, "周边建筑_高层", [(130, 10), (155, 10), (155, 70), (130, 70)])
    _add_closed_lwpolyline(msp, "场地内保留建筑", [(10, 10), (30, 10), (30, 28), (10, 28)])
    _add_closed_lwpolyline(msp, "方案塔楼", [(70, 25), (92, 25), (92, 52), (70, 52)])
    _add_closed_lwpolyline(msp, "方案裙房", [(52, 18), (105, 18), (105, 60), (52, 60)])

    msp.add_lwpolyline([(0, -30), (120, -30)], dxfattribs={"layer": "道路_忽略"})
    msp.add_text("Ignored road annotation", dxfattribs={"layer": "道路_忽略", "height": 2.5}).set_placement((5, -35))

    doc.saveas(output_path)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
