# DXF Clean Input Protocol

Status: future development guide. `sunlit convert dxf` is not implemented yet.

This document records the product boundary for future DXF support.

## Product Principle

`sunlit` should not try to understand every messy CAD drawing automatically.

Instead, the first DXF workflow should use this division of labor:

```text
User cleans CAD geometry.
AI writes a readable YAML configuration.
User reviews the YAML.
sunlit runs deterministic conversion and analysis.
```

This is the formal product principle for early DXF support.

The AI should not edit or reorganize the CAD file in the first version. Editing geometry is risky because a wrong layer move, deleted object, or missed footprint can be hard to detect. YAML is safer: it is short, human-readable, and easy for the user to review.

This is intentional:

- CAD files vary too much across teams, regions, and drawing habits.
- Automatically adapting to every layer convention, broken polyline, text style, block attribute, unit, and annotation pattern would create large implementation cost.
- A short user cleanup step is cheaper and more reliable than weeks of fragile CAD inference logic.
- AI-generated YAML is easier to audit than AI-edited CAD geometry.

Product promise:

`sunlit` converts a clean, documented CAD subset into analysis inputs. It does not promise to parse arbitrary production CAD sheets or to automatically clean CAD drawings.

## User Responsibility

The user should create a separate cleaned DXF file, for example:

```text
project_sunlit_clean.dxf
```

The cleaned file should contain only the geometry needed for analysis.

The user may keep their own layer names. English `SUNLIT_*` names are optional, not required.

Typical cleaned layers may look like:

```text
红线
周边建筑_低层
周边建筑_高层
场地内保留建筑
方案塔楼
方案裙房
```

Or:

```text
SUNLIT_SITE
SUNLIT_CONTEXT_LOW
SUNLIT_CONTEXT_HIGH
SUNLIT_EXISTING_ON_SITE
SUNLIT_SCHEME_TOWER
SUNLIT_SCHEME_PODIUM
```

## Required Cleanup

Before running `sunlit`, the user should:

- Put the site boundary on one dedicated layer.
- Put surrounding/context building footprints on clear layers.
- Put existing buildings inside the site on clear layers, if they remain in the baseline.
- Put proposed/scheme building footprints on clear layers, if any.
- Group buildings by approximate height where practical.
- Use closed polylines for site and building footprints.
- Remove or hide roads, landscape, hatches, dimensions, title blocks, grids, furniture, and unrelated text.
- Confirm whether CAD units are meters, millimeters, or another scale.
- Confirm north direction.

The user does not need to provide a real GIS CRS for typical CAD workflows.

## YAML Configuration

The AI agent should turn the user's description into a `sunlit.yaml` file.

The user should be able to review this file before running analysis.

First-version YAML should use one clear idea:

```text
Each configured CAD layer has a role and a height.
```

Example:

```yaml
project:
  location:
    city: Shanghai
    lat: 31.23
    lon: 121.47
    timezone: Asia/Shanghai

cad:
  file: project_sunlit_clean.dxf
  unit: m
  north_angle: 0

layers:
  site: 红线

  context:
    周边建筑_低层:
      height: 12
    周边建筑_高层:
      height: 54
    场地内保留建筑:
      height: 18

  scheme:
    方案塔楼:
      height: 72
    方案裙房:
      height: 8

analysis:
  date: 2026-01-20
  time_start: "09:00"
  time_end: "15:00"
  time_step: 30
  grid_size: 3
  threshold: 2
```

Do not expose multiple height modes in the first user-facing workflow. Internally this is a layer-based configuration, but the user-facing rule is simply: write the layer and its height in YAML.

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
- surrounding/context building layers and their heights;
- existing on-site building layers and their heights, if any;
- scheme building layers and their heights, if any.

AI may infer approximate latitude, longitude, and timezone from a city or address for design-stage analysis. The user should confirm exact coordinates for higher-stakes work.

## Future CLI Shape

First-version command shape:

```bash
sunlit convert dxf --config sunlit.yaml
```

Or, later, a single study command:

```bash
sunlit study sunlit.yaml
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

The agent should not modify the CAD file in the first version.

The agent should guide the user through cleanup, then generate YAML:

- Which layer is the site boundary?
- Which layer contains existing/context buildings?
- Which layer contains proposed/scheme buildings?
- What height should be assigned to each relevant layer?
- What is the CAD unit?
- Is north aligned with +Y?
- What is the project location?

Then the agent should show the generated YAML for user review before calling `sunlit convert dxf` and `sunlit analyze`.

Recommended framing:

Use a few minutes to clean the CAD layers, let the AI generate a reviewable `sunlit.yaml`, then let `sunlit` run repeatable design-stage analysis.

## Non-Goals

First DXF support should not attempt to:

- infer all possible layer naming conventions;
- repair heavily broken CAD drawings;
- edit or reorganize the user's CAD automatically;
- parse arbitrary annotations and title blocks;
- identify building heights from uncontrolled text;
- ask the user to choose between several technical height modes;
- infer true project location from CAD coordinates alone;
- provide permitting or legal sunlight conclusions.

These may be explored later, but they should not be required for the first DXF implementation.

## Later Extensions

Later versions may support more precise height assignment for complex sites:

- building ID text plus CSV/YAML table;
- block attributes;
- nearest-text height matching;
- AI-assisted cleanup suggestions.

These should remain roadmap items until the first layer-based YAML workflow is stable.
