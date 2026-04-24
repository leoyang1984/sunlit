# sunlit

`sunlit` is an open-source command-line tool for design-stage ground sunlight analysis based on CityJSON massing models.

It analyzes sunlight duration on ground grid points inside a site boundary and writes a small report bundle:

- `analysis.json`
- `heatmap.png`
- `summary.md`
- `metadata.yaml`

## Positioning

`sunlit` is for early design reference. It is not intended for residential building permitting, legal review, or full-window sunlight analysis.

If you need formal permitting output, use professional sunlight analysis software.

## Install From GitHub

```bash
git clone https://github.com/leoyang1984/sunlit.git
cd sunlit
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/sunlit version
```

## Install For Local Development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

After installation, use the `sunlit` command directly. For source-tree development, `python -m sunlit` is also supported.

## Quick Start

Convert the London context footprints:

```bash
sunlit convert footprint \
  examples/london-context.geojson \
  --height-field height \
  --default-height 20 \
  --output sunlit-output/london/context.cityjson \
  --crs EPSG:27700
```

Run the baseline analysis:

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

Inspect the output:

```bash
ls sunlit-output/london/baseline
```

Expected files:

```text
analysis.json
heatmap.png
metadata.yaml
summary.md
```

## Convert Footprints To CityJSON

For projected GeoJSON footprints with a height property:

```bash
sunlit convert footprint \
  examples/london-context.geojson \
  --height-field height \
  --default-height 20 \
  --output sunlit-output/london/context.cityjson \
  --crs EPSG:27700
```

## Convert OBJ Footprints To CityJSON

For OBJ files where each `o` or `g` group is one building footprint face:

```bash
sunlit convert obj \
  examples/simple-scheme.obj \
  --meta examples/meta-example.json \
  --output sunlit-output/scheme.cityjson
```

## Verify

```bash
.venv/bin/python -m pytest
```

Current baseline:

```text
15 passed
```

## Docs

- [Getting Started](docs/getting-started.md)
- [Preparing Data](docs/preparing-data.md)
- [CLI Reference](docs/cli-reference.md)
- [FAQ](docs/faq.md)
- [Examples](examples/README.md)
- [Document Archive](docs/archive/README.md)

## AI Skills

`sunlit` is designed to be operated by AI agents as well as humans.

Agent-specific adapters live in:

- [skills/codex/SKILL.md](skills/codex/SKILL.md)
- [skills/claude-code/SKILL.md](skills/claude-code/SKILL.md)

The root [SKILL.md](SKILL.md) is only an index.
