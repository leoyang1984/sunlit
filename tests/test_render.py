from datetime import date

from sunlit.analyze import analyze
from sunlit.models import AnalysisConfig
from sunlit.render import load_cityjson_footprints, render_heatmap

from .conftest import SAMPLE_CITYJSON, SAMPLE_SITE


def test_render_heatmap_writes_png(tmp_path):
    result = analyze(
        scheme_path=None,
        context_path=SAMPLE_CITYJSON,
        boundary_path=SAMPLE_SITE,
        config=AnalysisConfig(
            latitude=52.0,
            longitude=4.36,
            date=date(2026, 1, 20),
            time_start="09:00",
            time_end="15:00",
            time_step_minutes=30,
            grid_size_meters=10,
            threshold_hours=2,
        ),
        timezone="Europe/Amsterdam",
    )

    output_path = render_heatmap(result, boundary_path=SAMPLE_SITE, output_path=tmp_path / "heatmap.png")

    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"\x89PNG")
    assert output_path.stat().st_size > 1000


def test_load_cityjson_footprints_extracts_buildings():
    footprints = load_cityjson_footprints(SAMPLE_CITYJSON)

    assert footprints
    assert all(footprint.area > 0 for footprint in footprints)


def test_render_heatmap_with_building_overlays_writes_png(tmp_path):
    result = analyze(
        scheme_path=None,
        context_path=SAMPLE_CITYJSON,
        boundary_path=SAMPLE_SITE,
        config=AnalysisConfig(
            latitude=52.0,
            longitude=4.36,
            date=date(2026, 1, 20),
            time_start="09:00",
            time_end="15:00",
            time_step_minutes=30,
            grid_size_meters=10,
            threshold_hours=2,
        ),
        timezone="Europe/Amsterdam",
    )

    output_path = render_heatmap(
        result,
        boundary_path=SAMPLE_SITE,
        context_path=SAMPLE_CITYJSON,
        output_path=tmp_path / "heatmap-with-buildings.png",
    )

    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"\x89PNG")
    assert output_path.stat().st_size > 1000
