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
