import json

from typer.testing import CliRunner

from sunlit.cli import app
from sunlit.convert.obj_to_cityjson import convert_obj_to_cityjson
from sunlit.geometry import load_cityjson_building_mesh

from .conftest import META_EXAMPLE, SIMPLE_OBJ


runner = CliRunner()


def test_convert_obj_to_cityjson_writes_lod1_solid(tmp_path):
    output = tmp_path / "scheme.cityjson"

    cityjson = convert_obj_to_cityjson(
        obj_path=SIMPLE_OBJ,
        meta_path=META_EXAMPLE,
        output_path=output,
    )

    assert output.exists()
    assert cityjson["metadata"]["referenceSystem"] == "EPSG:3857"
    assert len(cityjson["CityObjects"]) == 2
    assert cityjson["CityObjects"]["Building_A"]["attributes"]["height"] == 12.5
    assert cityjson["CityObjects"]["Building_B"]["attributes"]["height"] == 9.0

    mesh, building_count, reference_system = load_cityjson_building_mesh(output)
    assert building_count == 2
    assert len(mesh.vertices) == 16
    assert len(mesh.faces) == 24
    assert reference_system == "EPSG:3857"


def test_cli_convert_obj(tmp_path):
    output = tmp_path / "scheme.cityjson"
    result = runner.invoke(
        app,
        [
            "convert",
            "obj",
            str(SIMPLE_OBJ),
            "--meta",
            str(META_EXAMPLE),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output.exists()
    data = json.loads(output.read_text())
    assert len(data["CityObjects"]) == 2
    assert "Buildings: 2" in result.output

