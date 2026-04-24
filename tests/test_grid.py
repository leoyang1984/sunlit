import pytest

from sunlit.grid import GridError, generate_grid_inside, grid_bounds, load_boundary

from .conftest import SAMPLE_SITE, WGS84_SITE


def test_generate_grid_inside_projected_boundary():
    boundary = load_boundary(SAMPLE_SITE)
    points = generate_grid_inside(boundary, spacing=10)

    assert len(points) == 42
    assert grid_bounds(points) == {
        "xmin": 3499950.0,
        "ymin": 5400005.0,
        "xmax": 3500000.0,
        "ymax": 5400065.0,
    }


def test_generate_grid_rejects_wgs84_boundary():
    boundary = load_boundary(WGS84_SITE)

    with pytest.raises(GridError, match="WGS84"):
        generate_grid_inside(boundary, spacing=2)

