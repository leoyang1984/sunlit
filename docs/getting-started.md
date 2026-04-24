# Getting Started

This guide runs the London footprint example from GeoJSON to CityJSON to a report bundle.

## 1. Check The CLI

```bash
sunlit version
```

Expected:

```text
sunlit 0.1.0
```

## 2. Convert Example Footprints

```bash
sunlit convert footprint \
  examples/london-context.geojson \
  --height-field height \
  --default-height 20 \
  --output sunlit-output/london/context.cityjson \
  --crs EPSG:27700
```

## 3. Run Analysis

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

## 4. Read Outputs

```text
sunlit-output/london/baseline/
├── analysis.json
├── heatmap.png
├── metadata.yaml
└── summary.md
```

`summary.md` contains a non-AI statistical report. AI summary generation is intentionally not wired in yet.
