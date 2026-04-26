# DXF Clean Input Example

This example demonstrates the first cleaned-DXF workflow.

The workflow keeps CAD cleanup explicit and reviewable:

```text
User cleans CAD geometry.
AI writes sunlit.yaml.
User reviews sunlit.yaml.
sunlit converts the cleaned DXF and runs analysis.
```

Generate the example DXF:

```bash
python scripts/generate_dxf_example.py
```

Inspect the DXF and YAML:

```bash
python scripts/spike_dxf_clean_input.py \
  --config examples/dxf/sunlit.yaml \
  --output examples/dxf/conversion_report.md
```

Convert the cleaned DXF into analysis inputs:

```bash
sunlit convert dxf \
  --config examples/dxf/sunlit.yaml \
  --output sunlit-output/dxf-example
```

Or run conversion and analysis together:

```bash
sunlit study examples/dxf/sunlit.yaml \
  --output sunlit-output/dxf-example
```

The one-command study also writes:

```text
sunlit-output/dxf-example/presentation.html
```

Open it locally to switch between baseline and with-scheme results and review the heatmap, summary, metadata, JSON, and conversion report.

Run a context-only baseline analysis:

```bash
sunlit analyze \
  --context sunlit-output/dxf-example/context.cityjson \
  --boundary sunlit-output/dxf-example/site.geojson \
  --lat 31.23 --lon 121.47 \
  --date 2026-01-20 \
  --time-start 09:00 --time-end 15:00 \
  --time-step 30 \
  --grid-size 3 \
  --threshold 2 \
  --timezone Asia/Shanghai \
  --output sunlit-output/dxf-example/baseline
```

Run the analysis with the proposed scheme:

```bash
sunlit analyze \
  --context sunlit-output/dxf-example/context.cityjson \
  --scheme sunlit-output/dxf-example/scheme.cityjson \
  --boundary sunlit-output/dxf-example/site.geojson \
  --lat 31.23 --lon 121.47 \
  --date 2026-01-20 \
  --time-start 09:00 --time-end 15:00 \
  --time-step 30 \
  --grid-size 3 \
  --threshold 2 \
  --timezone Asia/Shanghai \
  --output sunlit-output/dxf-example/with-scheme
```

Expected result:

- the configured Chinese layer names are found;
- site/context/scheme layers contain closed polylines;
- unrelated road entities are ignored;
- `site.geojson`, `context.cityjson`, `scheme.cityjson`, and `conversion_report.md` are written.
- each analysis output directory contains `analysis.json`, `heatmap.png`, `summary.md`, and `metadata.yaml`.
