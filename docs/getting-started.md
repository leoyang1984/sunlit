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

`heatmap.png` is a 2D site-plan style image with the site boundary, sampled sunlight duration, colorbar, threshold marker, north arrow, scale bar, and building footprint overlays when scheme/context CityJSON paths are provided.

## Cleaned DXF Example

If you are starting from a cleaned CAD/DXF file, use the DXF example:

```bash
sunlit study examples/dxf/sunlit.yaml \
  --output sunlit-output/dxf-example
```

To inspect the converted inputs before analysis, run the conversion step separately:

```bash
sunlit convert dxf \
  --config examples/dxf/sunlit.yaml \
  --output sunlit-output/dxf-example
```

Then run the baseline command shown in:

```text
sunlit-output/dxf-example/conversion_report.md
```

The same report includes a with-scheme command when the YAML has scheme layers.

`sunlit study` also writes `presentation.html` at the output root. Open it locally to switch between available runs and inspect the heatmap, summary, metadata, JSON, and conversion report.
