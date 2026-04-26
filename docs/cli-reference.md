# CLI Reference

## `sunlit version`

Print the current version.

```bash
sunlit version
```

## `sunlit inspect-cityjson`

Check whether a CityJSON file can be loaded as building mesh.

```bash
sunlit inspect-cityjson sample.cityjson
```

## `sunlit study`

Run a reviewed cleaned-DXF `sunlit.yaml` through conversion and analysis.

```bash
sunlit study examples/dxf/sunlit.yaml \
  --output sunlit-output/dxf-example
```

This command currently uses the DXF study YAML schema. It writes `site.geojson`, `context.cityjson`, `scheme.cityjson`, `conversion_report.md`, and analysis bundles such as `baseline/` and `with-scheme/` when the corresponding layers exist.

By default it also writes `presentation.html`, a deterministic offline viewer for switching runs and inspecting the map, summary, metadata, raw JSON, and conversion report. Use `--no-viewer` to skip it.

## `sunlit analyze`

Run ground-grid sunlight analysis.

Required:

- At least one of `--scheme` or `--context`
- `--boundary`
- `--lat`
- `--lon`

Common options:

```text
--scheme PATH
--context PATH
--boundary PATH
--lat FLOAT
--lon FLOAT
--date YYYY-MM-DD
--time-start HH:MM
--time-end HH:MM
--time-step INTEGER
--grid-size FLOAT
--threshold FLOAT
--timezone TEXT
--output PATH
```

Example:

```bash
sunlit analyze \
  --context sunlit-output/london/context.cityjson \
  --boundary examples/london-site.geojson \
  --lat 51.5 --lon -0.12 \
  --timezone Europe/London \
  --output sunlit-output/london/baseline
```

`--points` is reserved and intentionally returns `Not implemented in MVP`.

## `sunlit convert footprint`

Convert projected GeoJSON footprints to CityJSON LOD1.

```bash
sunlit convert footprint examples/london-context.geojson \
  --height-field height \
  --default-height 20 \
  --output sunlit-output/london/context.cityjson \
  --crs EPSG:27700
```

## `sunlit convert obj`

Convert grouped OBJ footprint faces to CityJSON LOD1.

```bash
sunlit convert obj scheme.obj \
  --meta meta.json \
  --output scheme.cityjson
```

## `sunlit convert dxf`

Convert a cleaned DXF plus reviewed `sunlit.yaml` into analysis inputs.

Required:

- `--config PATH`
- `--output PATH`

The cleaned DXF workflow supports closed `LWPOLYLINE` / `POLYLINE` footprints on configured layers. It does not clean arbitrary CAD drawings or infer heights from annotations.

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

The generated `conversion_report.md` includes copyable `sunlit analyze` commands for baseline and with-scheme runs.
