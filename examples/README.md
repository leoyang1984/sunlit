# Examples

This directory contains small projected-coordinate examples that can be run after installing `sunlit` from the repository.

Generated files are written to `sunlit-output/`, which is ignored by Git.

## London Footprint Workflow

Inputs:

- `london-site.geojson`: site boundary in EPSG:27700-like meter coordinates.
- `london-context.geojson`: surrounding building footprints with `height` properties.
- `london-scheme.geojson`: optional proposed massing footprints with `height` properties.

Convert the context buildings:

```bash
sunlit convert footprint \
  examples/london-context.geojson \
  --height-field height \
  --default-height 20 \
  --output sunlit-output/london/context.cityjson \
  --crs EPSG:27700
```

Run a context-only baseline:

```bash
sunlit analyze \
  --context sunlit-output/london/context.cityjson \
  --boundary examples/london-site.geojson \
  --lat 51.5 --lon -0.12 \
  --date 2026-01-20 \
  --time-start 09:00 --time-end 15:00 \
  --time-step 30 \
  --grid-size 5 \
  --threshold 2 \
  --timezone Europe/London \
  --output sunlit-output/london/baseline
```

Convert the proposed scheme:

```bash
sunlit convert footprint \
  examples/london-scheme.geojson \
  --height-field height \
  --default-height 12 \
  --output sunlit-output/london/scheme.cityjson \
  --crs EPSG:27700
```

Run context plus scheme:

```bash
sunlit analyze \
  --context sunlit-output/london/context.cityjson \
  --scheme sunlit-output/london/scheme.cityjson \
  --boundary examples/london-site.geojson \
  --lat 51.5 --lon -0.12 \
  --date 2026-01-20 \
  --time-start 09:00 --time-end 15:00 \
  --time-step 30 \
  --grid-size 5 \
  --threshold 2 \
  --timezone Europe/London \
  --output sunlit-output/london/with-scheme
```

Each analysis writes:

- `analysis.json`
- `heatmap.png`
- `summary.md`
- `metadata.yaml`

The current heatmap is a point-grid analysis visualization, not a conventional architectural site-plan drawing.

## OBJ Footprint Example

`sunlit convert obj` supports OBJ files where each `o` or `g` group contains one footprint face.

```bash
sunlit convert obj \
  examples/simple-scheme.obj \
  --meta examples/meta-example.json \
  --output sunlit-output/obj/scheme.cityjson
```

## DXF Clean Input Spike

`examples/dxf/` is an early spike for the future DXF workflow. `sunlit convert dxf` is not implemented yet.

It verifies the planned first-version product principle:

```text
User cleans CAD geometry.
AI writes a readable sunlit.yaml.
User reviews the YAML.
sunlit runs deterministic conversion and analysis.
```

See [examples/dxf/README.md](dxf/README.md).
