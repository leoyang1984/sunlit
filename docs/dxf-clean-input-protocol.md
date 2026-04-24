# DXF Clean Input Protocol

Status: future development guide. `sunlit convert dxf` is not implemented yet.

This document records the product boundary for future DXF support.

## Principle

`sunlit` should not try to understand every messy CAD drawing automatically.

Instead, the user should spend a few minutes preparing a clean DXF input. The tool can then provide a stable, predictable conversion path.

This is intentional:

- CAD files vary too much across teams, regions, and drawing habits.
- Automatically adapting to every layer convention, broken polyline, text style, block attribute, unit, and annotation pattern would create large implementation cost.
- A short user cleanup step is cheaper and more reliable than weeks of fragile CAD inference logic.

Product promise:

`sunlit` converts a clean, documented CAD subset into analysis inputs. It does not promise to parse arbitrary production CAD sheets.

## User Responsibility

The user should create a separate cleaned DXF file, for example:

```text
project_sunlit_clean.dxf
```

The cleaned file should contain only the geometry needed for analysis.

Recommended layers:

```text
SUNLIT_SITE
SUNLIT_CONTEXT
SUNLIT_SCHEME
SUNLIT_HEIGHT
SUNLIT_NORTH
```

Minimum layers:

```text
SUNLIT_SITE
SUNLIT_CONTEXT
```

Optional:

```text
SUNLIT_SCHEME
SUNLIT_HEIGHT
SUNLIT_NORTH
```

## Required Cleanup

Before running `sunlit`, the user should:

- Put the site boundary on one dedicated layer.
- Put existing/context building footprints on one dedicated layer.
- Put proposed/scheme building footprints on one dedicated layer, if any.
- Use closed polylines for site and building footprints.
- Remove or hide roads, landscape, hatches, dimensions, title blocks, grids, furniture, and unrelated text.
- Make building heights explicit by layer name, nearby text, or a separate table.
- Confirm whether CAD units are meters, millimeters, or another scale.
- Confirm north direction.

The user does not need to provide a real GIS CRS for typical CAD workflows.

## Coordinate Model

Future DXF support should separate two concepts:

1. CAD geometry coordinates.
2. Project location for sun position.

CAD geometry coordinates are used for:

- distances,
- areas,
- footprint placement,
- shadow obstruction geometry.

They can be local project coordinates. They do not need to be EPSG coordinates.

But the CAD units and north direction must be known.

Project location is used for:

- solar altitude,
- solar azimuth,
- timezone-aware time sampling.

It should come from user-provided location information such as city, address, latitude/longitude, and timezone.

## Required User Inputs

For a reliable DXF workflow, the user or AI agent should collect:

- project location, such as `Shanghai, China`;
- latitude, longitude, and timezone, if known;
- analysis date;
- analysis time window;
- sunlight threshold;
- CAD unit, such as `m` or `mm`;
- north direction, such as `north is +Y` or `north-angle 18`;
- site boundary layer;
- context building layer;
- scheme building layer, if any;
- height source.

AI may infer approximate latitude, longitude, and timezone from a city or address for design-stage analysis. The user should confirm exact coordinates for higher-stakes work.

## Height Modes

Future implementation should start with simple, explicit height modes.

Suggested first version:

```text
layer-name
fixed-default
```

Possible later versions:

```text
nearest-text
block-attribute
csv-table
```

Examples:

- Layer naming: `SUNLIT_CONTEXT_H24`, `SUNLIT_CONTEXT_H36`.
- Nearby text: `H=36`, `36m`, `height 36`.
- Default fallback: `--default-height 20`.

## Future CLI Shape

Layer-name height mode:

```bash
sunlit convert dxf project_sunlit_clean.dxf \
  --site-layer SUNLIT_SITE \
  --context-layer SUNLIT_CONTEXT \
  --scheme-layer SUNLIT_SCHEME \
  --height-mode layer-name \
  --unit m \
  --north-angle 0 \
  --output sunlit-output/my-project
```

Nearest-text height mode:

```bash
sunlit convert dxf project_sunlit_clean.dxf \
  --site-layer SUNLIT_SITE \
  --context-layer SUNLIT_CONTEXT \
  --scheme-layer SUNLIT_SCHEME \
  --height-layer SUNLIT_HEIGHT \
  --height-mode nearest-text \
  --default-height 20 \
  --unit m \
  --north-angle 0 \
  --output sunlit-output/my-project
```

The output should be compatible with existing analysis:

```text
sunlit-output/my-project/site.geojson
sunlit-output/my-project/context.cityjson
sunlit-output/my-project/scheme.cityjson
```

Then:

```bash
sunlit analyze \
  --context sunlit-output/my-project/context.cityjson \
  --scheme sunlit-output/my-project/scheme.cityjson \
  --boundary sunlit-output/my-project/site.geojson \
  --lat <lat> --lon <lon> \
  --timezone <timezone> \
  --date <YYYY-MM-DD> \
  --output sunlit-output/my-project/with-scheme
```

## AI Agent Role

Codex or Claude Code should not claim that arbitrary CAD is automatically supported.

The agent should guide the user through cleanup:

- Which layer is the site boundary?
- Which layer contains existing/context buildings?
- Which layer contains proposed/scheme buildings?
- How are heights encoded?
- What is the CAD unit?
- Is north aligned with +Y?
- What is the project location?

Then the agent can call `sunlit convert dxf` and `sunlit analyze`.

Recommended framing:

Use 10 minutes to clean the CAD layers, then let `sunlit` and the AI agent run repeatable design-stage analysis.

## Non-Goals

First DXF support should not attempt to:

- infer all possible layer naming conventions;
- repair heavily broken CAD drawings;
- parse arbitrary annotations and title blocks;
- identify building heights from uncontrolled text;
- infer true project location from CAD coordinates alone;
- provide permitting or legal sunlight conclusions.

These may be explored later, but they should not be required for the first DXF implementation.
