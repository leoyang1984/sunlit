import json

from typer.testing import CliRunner

from sunlit.cli import app

from .conftest import SAMPLE_CITYJSON, SAMPLE_SITE


runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "sunlit 0.1.0" in result.output


def test_cli_analyze_writes_output_files(tmp_path):
    result = runner.invoke(
        app,
        [
            "analyze",
            "--context",
            str(SAMPLE_CITYJSON),
            "--boundary",
            str(SAMPLE_SITE),
            "--lat",
            "52.0",
            "--lon",
            "4.36",
            "--date",
            "2026-01-20",
            "--time-start",
            "09:00",
            "--time-end",
            "15:00",
            "--time-step",
            "30",
            "--grid-size",
            "10",
            "--threshold",
            "2",
            "--timezone",
            "Europe/Amsterdam",
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    analysis_path = tmp_path / "analysis.json"
    heatmap_path = tmp_path / "heatmap.png"
    summary_path = tmp_path / "summary.md"
    metadata_path = tmp_path / "metadata.yaml"
    assert analysis_path.exists()
    assert heatmap_path.exists()
    assert summary_path.exists()
    assert metadata_path.exists()
    assert heatmap_path.read_bytes().startswith(b"\x89PNG")
    data = json.loads(analysis_path.read_text())
    assert data["statistics"]["total_points"] == 42
    assert data["statistics"]["qualified_points"] == 10
    assert "地面日照分析报告" in summary_path.read_text()
    assert "analysis: analysis.json" in metadata_path.read_text()


def test_cli_points_is_not_implemented():
    result = runner.invoke(
        app,
        [
            "analyze",
            "--points",
            "points.geojson",
            "--context",
            str(SAMPLE_CITYJSON),
            "--boundary",
            str(SAMPLE_SITE),
            "--lat",
            "52.0",
            "--lon",
            "4.36",
        ],
    )

    assert result.exit_code == 2
    assert "Not implemented in MVP" in result.output
