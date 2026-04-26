---
name: sunlit-codex
version: 0.1.0
description: |
  Operate the sunlit CLI for design-stage ground sunlight analysis.
  Use when the user asks for sunlight analysis, 日照分析, shadow analysis,
  site sunlight potential, CAD/DXF sunlight workflow, or AI-assisted
  building massing sunlight review.
---

# sunlit for Codex

Use this skill to run `sunlit` from a local workspace. `sunlit` is a CLI-first, AI-operable ground sunlight analysis tool.

## Product Boundary

`sunlit` analyzes sunlight duration on ground grid points inside a projected site boundary.

It is not for permitting, legal review, residential full-window sunlight analysis, facade radiation, roof radiation, or annual irradiance.

Use language such as "reaches the user-defined threshold" or "reference result". Avoid "compliant", "meets code", or "satisfies national standard".

## Locate The Project

Prefer the current working directory. If the current directory is not the project root, ask the user for the local `sunlit` project path.

```bash
if [ -f "src/sunlit/cli.py" ]; then
  SUNLIT_ROOT="$(pwd)"
else
  echo "ERROR: Cannot find sunlit project."
  exit 1
fi
```

Use:

```bash
cd "$SUNLIT_ROOT"
sunlit version
```

If `sunlit` is not installed, use the active project virtualenv or source-tree Python equivalent:

```bash
python -m sunlit version
```

## Understand The Request

Extract:

- Location: city, latitude, longitude, timezone.
- Date: exact date or design season.
- Time window: default `09:00-15:00`.
- Site boundary: dimensions or provided GeoJSON.
- Existing/context buildings: footprint, position, height.
- Proposed/scheme buildings: optional.
- Grid size: quick `5m`, normal `3m`, detailed `2m`.
- Threshold: user-defined reference hours, default `2`.

Ask a short clarifying question if the location or building geometry is too ambiguous.

## Coordinate Convention For Generated Cases

Use local projected-like coordinates to avoid WGS84 rejection:

- Site center: `(500000, 500000)`
- East: `+X`
- North: `+Y`
- Units: meters

The CLI `--lat` and `--lon` are only for sun position calculation.

## City Defaults

| City | Lat | Lon | Timezone |
|------|-----|-----|----------|
| London | 51.5 | -0.12 | Europe/London |
| Tokyo | 35.68 | 139.69 | Asia/Tokyo |
| Shanghai | 31.23 | 121.47 | Asia/Shanghai |
| Beijing | 39.91 | 116.39 | Asia/Shanghai |
| New York | 40.71 | -74.01 | America/New_York |
| Paris | 48.85 | 2.35 | Europe/Paris |
| Sydney | -33.87 | 151.21 | Australia/Sydney |
| Singapore | 1.35 | 103.82 | Asia/Singapore |
| Amsterdam | 52.37 | 4.90 | Europe/Amsterdam |
| Dubai | 25.20 | 55.27 | Asia/Dubai |

## Generate Inputs

Write files under:

```text
sunlit-output/<session>/
```

Use `site.geojson` for the site boundary and `context.geojson` / `scheme.geojson` for building footprints.

All building features need a numeric `height` property.

## Cleaned DXF Workflow

Use this when the user provides CAD/DXF or asks to analyze a CAD site plan.

Do not promise automatic cleanup of arbitrary CAD. The first supported DXF path requires a cleaned DXF subset:

- one dedicated closed polyline site boundary layer;
- closed polyline context/existing building footprint layers;
- optional closed polyline scheme building footprint layers;
- roads, hatches, dimensions, title blocks, furniture, grids, and unrelated text removed or ignored;
- known CAD unit, currently `m` or `mm`;
- known north direction as `north_angle`;
- layer heights reviewed by the user.

Ask for missing essentials before writing `sunlit.yaml`:

- project city/location, latitude, longitude, timezone;
- analysis date, time window, grid size, threshold;
- DXF file path;
- CAD unit and north angle;
- site layer name;
- context layer names and heights;
- scheme layer names and heights, if any.

Write a reviewable `sunlit.yaml` next to the cleaned DXF or in the working output folder. Show the YAML to the user before running conversion when the user has not already approved it.

Example:

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

Then run baseline and with-scheme analysis using the generated `conversion_report.md` commands. The generated DXF site boundary is tagged as local meter coordinates so local CAD coordinates such as `0..120` are valid for analysis.

## Convert Inputs

```bash
sunlit convert footprint \
  sunlit-output/<session>/context.geojson \
  --height-field height \
  --default-height 20 \
  --output sunlit-output/<session>/context.cityjson
```

If a proposed scheme exists:

```bash
sunlit convert footprint \
  sunlit-output/<session>/scheme.geojson \
  --height-field height \
  --default-height 10 \
  --output sunlit-output/<session>/scheme.cityjson
```

For OBJ footprint groups:

```bash
sunlit convert obj \
  scheme.obj \
  --meta meta.json \
  --output scheme.cityjson
```

## Run Analysis

Context-only:

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

With scheme:

```bash
sunlit analyze \
  --scheme sunlit-output/<session>/scheme.cityjson \
  --context sunlit-output/<session>/context.cityjson \
  --boundary sunlit-output/<session>/site.geojson \
  --lat <lat> --lon <lon> \
  --date <YYYY-MM-DD> \
  --time-start 09:00 --time-end 15:00 \
  --time-step 30 \
  --grid-size <grid_size> \
  --threshold <threshold> \
  --timezone <timezone> \
  --output sunlit-output/<session>/with-scheme
```

## Report Back

Read:

- `analysis.json`
- `summary.md`
- `metadata.yaml`
- `heatmap.png`

When possible, show the PNG with a Markdown image link using the absolute path.

Explain:

- site/date/time setup,
- qualified percentage and area,
- average/min/max sunlight hours,
- likely shaded zones based on building positions,
- design-stage suggestions,
- disclaimer that this is not permitting analysis.

## Error Handling

- WGS84 warning: switch generated geometry to local meter coordinates.
- No sun positions: change date or time window.
- No evaluation points: reduce grid size or enlarge boundary.
- Missing CityJSON: run the convert step first.
