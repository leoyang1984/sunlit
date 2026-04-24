from datetime import date

from sunlit.sun_position import compute_sun_positions


def test_compute_sun_positions_filters_to_daylight_slots():
    positions = compute_sun_positions(
        latitude=52.0,
        longitude=4.36,
        analysis_date=date(2026, 1, 20),
        time_start="09:00",
        time_end="15:00",
        time_step_minutes=30,
        timezone="Europe/Amsterdam",
    )

    assert len(positions) == 13
    assert all(position.altitude > 0 for position in positions)
    assert positions[0].timestamp.startswith("2026-01-20T09:00:00")

