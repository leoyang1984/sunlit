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
  --context sample.cityjson \
  --boundary tests/fixtures/sample-site.geojson \
  --lat 52.0 --lon 4.36 \
  --timezone Europe/Amsterdam \
  --output sunlit-output/example
```

`--points` is reserved and intentionally returns `Not implemented in MVP`.

## `sunlit convert footprint`

Convert projected GeoJSON footprints to CityJSON LOD1.

```bash
sunlit convert footprint GEOJSON_PATH \
  --height-field height \
  --default-height 10 \
  --output buildings.cityjson \
  --crs EPSG:3857
```

## `sunlit convert obj`

Convert grouped OBJ footprint faces to CityJSON LOD1.

```bash
sunlit convert obj scheme.obj \
  --meta meta.json \
  --output scheme.cityjson
```
