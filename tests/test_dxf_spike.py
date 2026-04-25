from pathlib import Path

from sunlit.dxf_spike import inspect_dxf_config, render_inspection_report


def _write_config(path: Path, dxf_name: str = "test.dxf") -> None:
    path.write_text(
        f"""
project:
  location:
    city: Shanghai
    lat: 31.23
    lon: 121.47
    timezone: Asia/Shanghai
cad:
  file: {dxf_name}
  unit: m
  north_angle: 0
layers:
  site: 红线
  context:
    周边建筑:
      height: 24
analysis:
  date: 2026-01-20
  time_start: "09:00"
  time_end: "15:00"
  time_step: 30
  grid_size: 3
  threshold: 2
""",
        encoding="utf-8",
    )


def _new_doc():
    import ezdxf

    doc = ezdxf.new("R2010")
    doc.layers.add("红线")
    doc.layers.add("周边建筑")
    return doc


def _add_polyline(modelspace, layer: str, points: list[tuple[float, float]], closed: bool) -> None:
    modelspace.add_lwpolyline(points, close=closed, dxfattribs={"layer": layer})


def test_inspect_dxf_config_reads_clean_example():
    report = inspect_dxf_config(Path("examples/dxf/sunlit.yaml"))

    assert not report.has_errors
    assert report.ignored_entities == 2
    assert {layer.layer for layer in report.layers} == {
        "红线",
        "周边建筑_低层",
        "周边建筑_高层",
        "场地内保留建筑",
        "方案塔楼",
        "方案裙房",
    }
    assert sum(layer.closed_polylines for layer in report.layers) == 6


def test_render_inspection_report_mentions_layers():
    report = inspect_dxf_config(Path("examples/dxf/sunlit.yaml"))
    text = render_inspection_report(report)

    assert "# DXF Clean Input Inspection" in text
    assert "周边建筑_高层" in text
    assert "No blocking layer or closure issues found" in text


def test_inspect_dxf_config_reports_missing_site_layer(tmp_path):
    config_path = tmp_path / "sunlit.yaml"
    _write_config(config_path)
    doc = _new_doc()
    msp = doc.modelspace()
    _add_polyline(msp, "周边建筑", [(0, 0), (10, 0), (10, 10), (0, 10)], closed=True)
    doc.saveas(tmp_path / "test.dxf")

    report = inspect_dxf_config(config_path)
    text = render_inspection_report(report)

    assert report.has_errors
    assert "Missing configured layer: `红线`" in text


def test_inspect_dxf_config_reports_open_polyline(tmp_path):
    config_path = tmp_path / "sunlit.yaml"
    _write_config(config_path)
    doc = _new_doc()
    msp = doc.modelspace()
    _add_polyline(msp, "红线", [(0, 0), (20, 0), (20, 20), (0, 20)], closed=True)
    _add_polyline(msp, "周边建筑", [(0, 0), (10, 0), (10, 10), (0, 10)], closed=False)
    doc.saveas(tmp_path / "test.dxf")

    report = inspect_dxf_config(config_path)
    text = render_inspection_report(report)

    assert report.has_errors
    assert "contains no closed polylines" in text
    assert "contains 1 open polyline" in text
