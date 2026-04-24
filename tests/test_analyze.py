from datetime import date

from sunlit.analyze import analyze
from sunlit.models import AnalysisConfig

from .conftest import SAMPLE_CITYJSON, SAMPLE_SITE


def test_analyze_generates_m1_result():
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

    assert result.mode.display_name == "场地前期评估"
    assert len(result.sun_positions) == 13
    assert result.statistics.total_points == 42
    assert result.statistics.qualified_points == 10
    assert result.disclaimer

