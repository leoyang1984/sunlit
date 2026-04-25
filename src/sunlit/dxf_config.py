from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class DxfConfigError(ValueError):
    """Raised when a DXF study YAML file cannot be loaded or validated."""


class LocationConfig(BaseModel):
    city: str
    lat: float
    lon: float
    timezone: str


class ProjectConfig(BaseModel):
    location: LocationConfig


class CadConfig(BaseModel):
    file: Path
    unit: Literal["m", "mm"]
    north_angle: float = 0.0


class LayerConfig(BaseModel):
    height: float = Field(gt=0)


class DxfLayersConfig(BaseModel):
    site: str
    context: dict[str, LayerConfig] = Field(default_factory=dict)
    scheme: dict[str, LayerConfig] = Field(default_factory=dict)

    @field_validator("site")
    @classmethod
    def site_layer_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Site layer must not be blank.")
        return value

    @model_validator(mode="after")
    def require_building_layers(self) -> "DxfLayersConfig":
        if not self.context and not self.scheme:
            raise ValueError("Configure at least one context or scheme building layer.")
        return self


class DxfAnalysisConfig(BaseModel):
    date: date
    time_start: str
    time_end: str
    time_step: int = Field(gt=0)
    grid_size: float = Field(gt=0)
    threshold: float = Field(ge=0)


class DxfStudyConfig(BaseModel):
    project: ProjectConfig
    cad: CadConfig
    layers: DxfLayersConfig
    analysis: DxfAnalysisConfig

    def cad_path(self, config_path: Path) -> Path:
        if self.cad.file.is_absolute():
            return self.cad.file
        return config_path.parent / self.cad.file


def load_dxf_study_config(path: Path) -> DxfStudyConfig:
    try:
        import yaml
    except ImportError as exc:
        raise DxfConfigError("PyYAML is required to read sunlit.yaml files. Install sunlit[dxf].") from exc

    if not path.exists():
        raise DxfConfigError(f"Config file does not exist: {path}")

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DxfConfigError(f"Could not read YAML config: {path}") from exc

    if not isinstance(data, dict):
        raise DxfConfigError("YAML config must contain a mapping at the top level.")

    try:
        return DxfStudyConfig.model_validate(data)
    except Exception as exc:
        raise DxfConfigError(str(exc)) from exc
