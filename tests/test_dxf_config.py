from pathlib import Path

import pytest

from sunlit.dxf_config import DxfConfigError, load_dxf_study_config


def test_load_dxf_study_config_supports_chinese_layers():
    config = load_dxf_study_config(Path("examples/dxf/sunlit.yaml"))

    assert config.cad.unit == "m"
    assert config.layers.site == "红线"
    assert config.layers.context["周边建筑_高层"].height == 54
    assert config.layers.scheme["方案塔楼"].height == 72


def test_load_dxf_study_config_requires_building_layers(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
project:
  location:
    city: Shanghai
    lat: 31.23
    lon: 121.47
    timezone: Asia/Shanghai
cad:
  file: project_clean.dxf
  unit: m
  north_angle: 0
layers:
  site: 红线
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

    with pytest.raises(DxfConfigError, match="context or scheme"):
        load_dxf_study_config(path)
