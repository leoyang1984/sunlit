# Preparing Data

`sunlit` accepts CityJSON buildings and a projected GeoJSON site boundary. It can also convert projected GeoJSON footprints, simple OBJ footprint faces, and cleaned DXF workflows into those analysis inputs.

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
  examples/london-context.geojson \
  --height-field height \
  --default-height 20 \
  --output sunlit-output/london/context.cityjson \
  --crs EPSG:27700
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
  examples/simple-scheme.obj \
  --meta examples/meta-example.json \
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

## Option C: Cleaned DXF + `sunlit.yaml`

Input:

- cleaned DXF file;
- one dedicated closed polyline site boundary layer;
- closed polyline context/existing building layers;
- optional closed polyline proposed scheme layers;
- one reviewed height per building layer;
- CAD unit, currently `m` or `mm`;
- north direction as `north_angle`;
- project location for sun position.

This path does not automatically clean messy CAD drawings. Create a separate cleaned DXF and remove or ignore roads, hatches, dimensions, title blocks, furniture, grids, and unrelated text.

Example `sunlit.yaml`:

```yaml
project:
  location:
    city: Shanghai
    lat: 31.23
    lon: 121.47
    timezone: Asia/Shanghai
cad:
  file: project_clean.dxf
  unit: m
  north_angle: 0
layers:
  site: 红线
  context:
    周边建筑_高层:
      height: 54
  scheme:
    方案塔楼:
      height: 72
analysis:
  date: 2026-01-20
  time_start: "09:00"
  time_end: "15:00"
  time_step: 30
  grid_size: 3
  threshold: 2
```

Convert:

```bash
sunlit convert dxf \
  --config examples/dxf/sunlit.yaml \
  --output sunlit-output/dxf-example
```

Expected files:

```text
site.geojson
context.cityjson
scheme.cityjson
conversion_report.md
```

The generated `site.geojson` is tagged as local meter coordinates, so CAD-local coordinates such as `0..120` are accepted by `sunlit analyze`. Use `conversion_report.md` for the exact baseline and with-scheme analysis commands.
