# Getting Started

This guide runs the current MVP sample from CityJSON to a report bundle.

## 1. Check The CLI

```bash
sunlit version
```

Expected:

```text
sunlit 0.1.0
```

## 2. Inspect The Sample CityJSON

```bash
sunlit inspect-cityjson sample.cityjson
```

Expected:

```text
Loaded 5 buildings
Combined mesh: 4718 vertices, 5299 faces
CRS: https://www.opengis.net/def/crs/EPSG/0/31467
```

## 3. Run Analysis

```bash
sunlit analyze \
  --context sample.cityjson \
  --boundary tests/fixtures/sample-site.geojson \
  --lat 52.0 --lon 4.36 \
  --date 2026-01-20 \
  --time-start 09:00 --time-end 15:00 \
  --time-step 30 \
  --grid-size 10 \
  --threshold 2 \
  --timezone Europe/Amsterdam \
  --output sunlit-output/getting-started
```

## 4. Read Outputs

```text
sunlit-output/getting-started/
├── analysis.json
├── heatmap.png
├── metadata.yaml
└── summary.md
```

`summary.md` contains a non-AI statistical report. AI summary generation is intentionally not wired in yet.
