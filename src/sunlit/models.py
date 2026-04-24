from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class AnalysisConfig(BaseModel):
    latitude: float
    longitude: float
    date: date
    time_start: str = "09:00"
    time_end: str = "15:00"
    time_step_minutes: int = 15
    grid_size_meters: float = 2.0
    threshold_hours: float = 2.0
    language: Literal["zh", "en"] = "zh"
    enable_ai_summary: bool = True


class SunPosition(BaseModel):
    timestamp: str
    azimuth: float
    altitude: float


class EvaluationPoint(BaseModel):
    x: float
    y: float
    z: float = 0.0
    sunlit_minutes: float = 0.0
    sunlit_intervals: list[tuple[str, str]] = Field(default_factory=list)
    meets_threshold: bool = False


class AnalysisMode(BaseModel):
    has_scheme: bool
    has_context: bool
    display_name: str


class Statistics(BaseModel):
    total_points: int
    qualified_points: int
    qualified_pct: float
    qualified_area_sqm: float
    max_hours: float
    min_hours: float
    avg_hours: float


class AnalysisResult(BaseModel):
    version: str
    mode: AnalysisMode
    config: AnalysisConfig
    sun_positions: list[SunPosition]
    evaluation_points: list[EvaluationPoint]
    statistics: Statistics
    grid_bounds: dict[str, float]
    spatial_patterns: dict
    disclaimer: str

