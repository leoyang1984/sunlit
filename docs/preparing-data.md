# Preparing Data

`sunlit` currently accepts CityJSON buildings and a projected GeoJSON site boundary.

## Coordinate Rule

MVP analysis requires projected meter-based coordinates for geometry operations.

Do not pass WGS84 longitude/latitude boundaries directly. If a boundary looks like longitude/latitude, `sunlit` stops with a clear error instead of silently producing bad distances and areas.

## Option A: GeoJSON Footprints

Input:

- GeoJSON `Polygon` or `MultiPolygon` building footprints
- A numeric height property, usually `height`
- Projected meter-based coordinates

Command:

```bash
sunlit convert footprint \
  tests/fixtures/building-footprints.geojson \
  --height-field height \
  --default-height 8 \
  --output sunlit-output/footprints.cityjson \
  --crs EPSG:3857
```

If a feature has no `height`, `--default-height` is used.

## Option B: OBJ Footprint Faces

Input:

- OBJ file
- One `o` or `g` group per building
- Each group contains exactly one footprint face
- `meta.json` maps OBJ groups to height/name attributes

Command:

```bash
sunlit convert obj \
  tests/fixtures/simple-scheme.obj \
  --meta tests/fixtures/meta-example.json \
  --output sunlit-output/scheme.cityjson
```

Example `meta.json`:

```json
{
  "crs": "EPSG:3857",
  "origin": {
    "x": 1000.0,
    "y": 2000.0,
    "elevation": 0.0
  },
  "rotation_degrees": 0,
  "buildings": [
    {
      "obj_group": "Building_A",
      "name": "1号楼",
      "height": 12.5,
      "floors": 4
    }
  ]
}
```

`height` is preferred. If `height` is absent, `floors * floor_height` is used.

## Current OBJ Limitation

`sunlit convert obj` currently supports footprint faces and extrudes them to LOD1 solids.

It does not yet support wrapping arbitrary closed OBJ meshes into CityJSON solids.
