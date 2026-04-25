from __future__ import annotations

import argparse
from pathlib import Path

from sunlit.dxf_spike import inspect_dxf_config, render_inspection_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a cleaned DXF plus sunlit.yaml config.")
    parser.add_argument("--config", type=Path, default=Path("examples/dxf/sunlit.yaml"))
    parser.add_argument("--output", type=Path, default=Path("examples/dxf/conversion_report.md"))
    args = parser.parse_args()

    report = inspect_dxf_config(args.config)
    text = render_inspection_report(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(text)
    if report.has_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
