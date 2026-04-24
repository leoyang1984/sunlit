from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SAMPLE_CITYJSON = ROOT / "sample.cityjson"
SAMPLE_SITE = FIXTURES / "sample-site.geojson"
WGS84_SITE = FIXTURES / "wgs84-site.geojson"
BUILDING_FOOTPRINTS = FIXTURES / "building-footprints.geojson"
SIMPLE_OBJ = FIXTURES / "simple-scheme.obj"
META_EXAMPLE = FIXTURES / "meta-example.json"
