import json

import pytest
from typer.testing import CliRunner

from sunlit.cli import app
from sunlit.convert.footprint_to_cityjson import FootprintConversionError, convert_footprint_to_cityjson
from sunlit.geometry import load_cityjson_building_mesh

from .conftest import BUILDING_FOOTPRINTS, WGS84_SITE


runner = CliRunner()


def test_convert_footprint_to_cityjson_writes_lod1_solid(tmp_path):
    output = tmp_path / "buildings.cityjson"

    cityjson = convert_footprint_to_cityjson(
        input_path=BUILDING_FOOTPRINTS,
        output_path=output,
        height_field="height",
        default_height=8.0,
        crs="EPSG:3857",
    )

    assert output.exists()
    assert cityjson["version"] == "1.1"
    assert cityjson["metadata"]["referenceSystem"] == "EPSG:3857"
    assert len(cityjson["CityObjects"]) == 2
    assert cityjson["CityObjects"]["A"]["geometry"][0]["type"] == "Solid"
    assert cityjson["CityObjects"]["A"]["attributes"]["height"] == 12.5
    assert cityjson["CityObjects"]["B"]["attributes"]["height"] == 8.0

    mesh, building_count, reference_system = load_cityjson_building_mesh(output)
    assert building_count == 2
    assert len(mesh.faces) == 24
    assert reference_system == "EPSG:3857"


def test_convert_footprint_rejects_wgs84(tmp_path):
    with pytest.raises(FootprintConversionError, match="WGS84"):
        convert_footprint_to_cityjson(
            input_path=WGS84_SITE,
            output_path=tmp_path / "bad.cityjson",
        )


def test_cli_convert_footprint(tmp_path):
    output = tmp_path / "converted.cityjson"
    result = runner.invoke(
        app,
        [
            "convert",
            "footprint",
            str(BUILDING_FOOTPRINTS),
            "--height-field",
            "height",
            "--default-height",
            "8",
            "--output",
            str(output),
            "--crs",
            "EPSG:3857",
        ],
    )

    assert result.exit_code == 0, result.output
    assert output.exists()
    data = json.loads(output.read_text())
    assert len(data["CityObjects"]) == 2
    assert "Buildings: 2" in result.output

