from datetime import date

import pandas as pd
import pvlib

from .models import SunPosition


def compute_sun_position(
    latitude: float,
    longitude: float,
    analysis_date: date,
    time_text: str,
    timezone: str,
) -> SunPosition:
    timestamp = pd.Timestamp(f"{analysis_date.isoformat()} {time_text}:00", tz=timezone)
    solar = pvlib.solarposition.get_solarposition(timestamp, latitude=latitude, longitude=longitude)
    row = solar.iloc[0]
    return SunPosition(
        timestamp=timestamp.isoformat(),
        azimuth=float(row["azimuth"]),
        altitude=float(row["apparent_elevation"]),
    )


def compute_sun_positions(
    latitude: float,
    longitude: float,
    analysis_date: date,
    time_start: str,
    time_end: str,
    time_step_minutes: int,
    timezone: str,
) -> list[SunPosition]:
    start = pd.Timestamp(f"{analysis_date.isoformat()} {time_start}:00", tz=timezone)
    end = pd.Timestamp(f"{analysis_date.isoformat()} {time_end}:00", tz=timezone)
    timestamps = pd.date_range(start=start, end=end, freq=f"{time_step_minutes}min")
    solar = pvlib.solarposition.get_solarposition(timestamps, latitude=latitude, longitude=longitude)

    positions: list[SunPosition] = []
    for timestamp, row in solar.iterrows():
        altitude = float(row["apparent_elevation"])
        if altitude <= 0:
            continue
        positions.append(
            SunPosition(
                timestamp=timestamp.isoformat(),
                azimuth=float(row["azimuth"]),
                altitude=altitude,
            )
        )
    return positions
