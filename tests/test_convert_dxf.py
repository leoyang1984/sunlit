import json
from pathlib import Path

from typer.testing import CliRunner

from sunlit.cli import app
from sunlit.convert.dxf_to_analysis import convert_dxf_to_analysis_inputs


runner = CliRunner()


def _write_config(path: Path, dxf_name: str, unit: str = "m") -> None:
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
  unit: {unit}
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


def _add_closed_polyline(modelspace, layer: str, points: list[tuple[float, float]]) -> None:
    modelspace.add_lwpolyline(points, close=True, dxfattribs={"layer": layer})


def test_convert_dxf_example_writes_analysis_inputs(tmp_path):
    result = convert_dxf_to_analysis_inputs(
        config_path=Path("examples/dxf/sunlit.yaml"),
        output_dir=tmp_path,
    )

    assert result.site_path.exists()
    assert result.context_path is not None
    assert result.context_path.exists()
    assert result.scheme_path is not None
    assert result.scheme_path.exists()
    assert result.report_path.exists()
    assert result.context_building_count == 3
    assert result.scheme_building_count == 2

    site = json.loads(result.site_path.read_text(encoding="utf-8"))
    context = json.loads(result.context_path.read_text(encoding="utf-8"))
    scheme = json.loads(result.scheme_path.read_text(encoding="utf-8"))

    assert site["type"] == "FeatureCollection"
    assert site["features"][0]["properties"]["layer"] == "红线"
    assert site["features"][0]["properties"]["coordinate_system"] == "local_meters"
    assert len(context["CityObjects"]) == 3
    assert len(scheme["CityObjects"]) == 2
    report = result.report_path.read_text(encoding="utf-8")
    assert "Suggested Analysis Commands" in report
    assert "Baseline Context" in report
    assert "With Scheme" in report


def test_convert_dxf_scales_millimeter_coordinates(tmp_path):
    config_path = tmp_path / "sunlit.yaml"
    _write_config(config_path, "test.dxf", unit="mm")
    doc = _new_doc()
    modelspace = doc.modelspace()
    _add_closed_polyline(modelspace, "红线", [(0, 0), (20000, 0), (20000, 20000), (0, 20000)])
    _add_closed_polyline(modelspace, "周边建筑", [(1000, 1000), (3000, 1000), (3000, 4000), (1000, 4000)])
    doc.saveas(tmp_path / "test.dxf")

    result = convert_dxf_to_analysis_inputs(config_path=config_path, output_dir=tmp_path / "out")

    site = json.loads(result.site_path.read_text(encoding="utf-8"))
    coordinates = site["features"][0]["geometry"]["coordinates"][0]
    assert coordinates[:4] == [[0.0, 0.0], [20.0, 0.0], [20.0, 20.0], [0.0, 20.0]]


def test_cli_convert_dxf_writes_outputs(tmp_path):
    result = runner.invoke(
        app,
        [
            "convert",
            "dxf",
            "--config",
            "examples/dxf/sunlit.yaml",
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "site.geojson").exists()
    assert (tmp_path / "context.cityjson").exists()
    assert (tmp_path / "scheme.cityjson").exists()
    assert (tmp_path / "conversion_report.md").exists()
    assert "Wrote" in result.output


def test_cli_dxf_workflow_runs_analysis(tmp_path):
    convert_dir = tmp_path / "converted"
    convert_result = runner.invoke(
        app,
        [
            "convert",
            "dxf",
            "--config",
            "examples/dxf/sunlit.yaml",
            "--output",
            str(convert_dir),
        ],
    )

    assert convert_result.exit_code == 0, convert_result.output

    analysis_dir = tmp_path / "with-scheme"
    analyze_result = runner.invoke(
        app,
        [
            "analyze",
            "--context",
            str(convert_dir / "context.cityjson"),
            "--scheme",
            str(convert_dir / "scheme.cityjson"),
            "--boundary",
            str(convert_dir / "site.geojson"),
            "--lat",
            "31.23",
            "--lon",
            "121.47",
            "--date",
            "2026-01-20",
            "--time-start",
            "09:00",
            "--time-end",
            "15:00",
            "--time-step",
            "30",
            "--grid-size",
            "12",
            "--threshold",
            "2",
            "--timezone",
            "Asia/Shanghai",
            "--output",
            str(analysis_dir),
        ],
    )

    assert analyze_result.exit_code == 0, analyze_result.output
    assert (analysis_dir / "analysis.json").exists()
    assert (analysis_dir / "heatmap.png").read_bytes().startswith(b"\x89PNG")
    assert "地面日照分析报告" in (analysis_dir / "summary.md").read_text(encoding="utf-8")


def test_cli_study_runs_convert_and_analysis(tmp_path):
    result = runner.invoke(
        app,
        [
            "study",
            "examples/dxf/sunlit.yaml",
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "site.geojson").exists()
    assert (tmp_path / "context.cityjson").exists()
    assert (tmp_path / "scheme.cityjson").exists()
    assert (tmp_path / "conversion_report.md").exists()
    assert (tmp_path / "baseline" / "analysis.json").exists()
    assert (tmp_path / "baseline" / "heatmap.png").read_bytes().startswith(b"\x89PNG")
    assert (tmp_path / "with-scheme" / "analysis.json").exists()
    assert (tmp_path / "with-scheme" / "heatmap.png").read_bytes().startswith(b"\x89PNG")
    assert "Wrote" in result.output
