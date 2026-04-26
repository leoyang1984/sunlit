---
name: sunlit-claude-code
version: 0.1.0
description: |
  Run AI-assisted design-stage ground sunlight analysis with the sunlit CLI.
  Converts natural-language site/building descriptions or cleaned CAD/DXF
  workflows into local metric inputs, calls sunlit, and explains outputs in
  architectural language.
---

# sunlit for Claude Code

You are helping the user run `sunlit`, a Python CLI for design-stage ground sunlight analysis.

The CLI is the source of truth. Do not reimplement the calculation in the skill.

## Scope

Use this skill for:

- "日照分析"
- "shadow analysis"
- "how much sun does this site get"
- "test this massing scheme"
- "analyze ground sunlight for a site"

Do not present results as permitting, legal, code-compliance, or full-window sunlight analysis.

## Conversation Pattern

1. Clarify missing essentials: city/location, site size, surrounding buildings, date.
2. Create local projected-like GeoJSON inputs in `sunlit-output/<session>/`.
3. Convert footprints or OBJ to CityJSON with `sunlit convert`.
4. Run `sunlit analyze`.
5. Read `summary.md` and `analysis.json`.
6. Show or reference `heatmap.png`.
7. Explain the result in plain architectural language.

## Required Inputs

Minimum viable request:

- Location or city.
- Site boundary or approximate dimensions.
- At least one context or scheme building.

Defaults if user does not specify:

- Date: `2026-01-20` for winter design check.
- Time: `09:00-15:00`.
- Time step: `30`.
- Grid size: `3m` for normal studies.
- Threshold: `2h` user-defined reference threshold.

Avoid saying the threshold is a code requirement unless the user provides that framing.

## Local Coordinate Method

For natural-language generated cases, create a local meter coordinate system:

- Site center: `(500000, 500000)`
- North: positive Y
- East: positive X

Example:

If the site is `100m x 80m`, the boundary is:

```text
(499950, 499960)
(500050, 499960)
(500050, 500040)
(499950, 500040)
```

A building "20m south of the site" sits below the south edge.

## Cleaned CAD/DXF Workflow

Use this path when the user has a CAD site plan or DXF.

Do not claim that `sunlit` can understand arbitrary production CAD. The supported first-version DXF workflow is:

```text
User cleans CAD geometry.
AI writes a readable sunlit.yaml.
User reviews the YAML.
sunlit converts and analyzes deterministically.
```

Required cleaned DXF shape:

- site boundary is one closed polyline on a known layer;
- context/existing buildings are closed polylines on known layers;
- proposed scheme buildings are optional closed polylines on known layers;
- each building layer has one reviewed height;
- CAD unit is `m` or `mm`;
- north direction is supplied as `north_angle`;
- unrelated CAD geometry is removed or ignored.

Before running commands, collect or confirm:

- city/location, latitude, longitude, timezone;
- date, time window, grid size, threshold;
- DXF file path;
- site layer;
- context and scheme layer heights.

Write `sunlit.yaml` and show it to the user for review unless it already exists and the user asked to run it.

After user review, prefer the one-command study flow:

```bash
sunlit study sunlit.yaml \
  --output sunlit-output/<session>
```

This writes converted inputs plus `baseline/` and `with-scheme/` analysis outputs when the YAML contains matching layers.
It also writes `presentation.html`, an offline deterministic viewer for map, summary, metadata, JSON, and conversion report review.

Use the two-step flow when you need to inspect converted inputs before analysis:

```bash
sunlit convert dxf \
  --config sunlit.yaml \
  --output sunlit-output/<session>
```

Then use `sunlit-output/<session>/conversion_report.md` for ready-to-run baseline and with-scheme analysis commands.

## Commands

Prefer the installed `sunlit` command. If it is not installed, run the equivalent command through the active project Python environment.

Convert footprints:

```bash
sunlit convert footprint \
  sunlit-output/<session>/context.geojson \
  --height-field height \
  --default-height 20 \
  --output sunlit-output/<session>/context.cityjson
```

Run analysis:

```bash
sunlit analyze \
  --context sunlit-output/<session>/context.cityjson \
  --boundary sunlit-output/<session>/site.geojson \
  --lat <lat> --lon <lon> \
  --date <YYYY-MM-DD> \
  --time-start 09:00 --time-end 15:00 \
  --time-step 30 \
  --grid-size <grid_size> \
  --threshold <threshold> \
  --timezone <timezone> \
  --output sunlit-output/<session>/baseline
```

If a scheme exists, include `--scheme`.

## Output Interpretation

Use `analysis.json` for numbers:

- `statistics.total_points`
- `statistics.qualified_points`
- `statistics.qualified_pct`
- `statistics.qualified_area_sqm`
- `statistics.avg_hours`
- `statistics.min_hours`
- `statistics.max_hours`

Use `summary.md` for deterministic report text.

Use `heatmap.png` for visual discussion, but remember that the current MVP heatmap is a point-grid analysis rather than a conventional rendered site plan.

## Response Shape

Keep the final explanation concise:

- What was analyzed.
- What the main numbers say.
- Which areas appear shaded or sunny.
- What the designer could change.
- Design-stage disclaimer.

## Known MVP Limits

- Heatmap is not yet a conventional architectural site-plan drawing.
- Building footprint outlines are not yet overlaid in the final heatmap.
- `convert obj` supports footprint faces, not arbitrary closed OBJ meshes.
- AI summary is not wired into the CLI yet; the agent may write interpretation from deterministic outputs.
