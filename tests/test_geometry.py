from sunlit.geometry import load_cityjson_building_mesh

from .conftest import SAMPLE_CITYJSON


def test_load_cityjson_extension_and_build_mesh():
    mesh, building_count, reference_system = load_cityjson_building_mesh(SAMPLE_CITYJSON)

    assert building_count == 5
    assert len(mesh.vertices) == 4718
    assert len(mesh.faces) == 5299
    assert reference_system == "https://www.opengis.net/def/crs/EPSG/0/31467"

