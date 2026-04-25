# sunlit AI Skills

This directory contains AI agent adapters for `sunlit`.

`sunlit` itself is a Python CLI in `src/sunlit`. These skills do not reimplement the analysis. They teach an AI agent how to:

- understand a sunlight-analysis request,
- prepare projected GeoJSON, OBJ, or cleaned DXF inputs,
- call the `sunlit` CLI,
- inspect `analysis.json`, `heatmap.png`, `summary.md`, and `metadata.yaml`,
- explain results in design-stage language.

## Available Skills

- `codex/SKILL.md`: optimized for Codex-style coding agents working in a local workspace.
- `claude-code/SKILL.md`: optimized for Claude Code-style natural-language task execution.

## Product Boundary

All skills must preserve the same product boundary:

`sunlit` is a design-stage ground sunlight reference tool. It is not a permitting tool and does not perform full-window sunlight analysis.
