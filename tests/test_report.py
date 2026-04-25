from datetime import date

from sunlit.analyze import analyze
from sunlit.models import AnalysisConfig
from sunlit.report import file_sha256, write_report_files

from .conftest import SAMPLE_CITYJSON, SAMPLE_SITE


def _result():
    return analyze(
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


def test_write_report_files(tmp_path):
    result = _result()

    summary_path, metadata_path = write_report_files(
        result=result,
        output_dir=tmp_path,
        scheme_path=None,
        context_path=SAMPLE_CITYJSON,
        boundary_path=SAMPLE_SITE,
        timezone_name="Europe/Amsterdam",
    )

    summary = summary_path.read_text(encoding="utf-8")
    metadata = metadata_path.read_text(encoding="utf-8")
    assert "# 地面日照分析报告" in summary
    assert "## 统计结果" in summary
    assert result.disclaimer in summary
    assert "context_sha256:" in metadata
    assert file_sha256(SAMPLE_CITYJSON) in metadata
    assert "summary: summary.md" in metadata
