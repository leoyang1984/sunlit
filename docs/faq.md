# FAQ

## Is this a permitting tool?

No. `sunlit` is a design-stage reference tool. It does not perform full-window sunlight analysis and is not intended for legal or permitting use.

## What does `sunlit` analyze?

The MVP analyzes sunlight duration on ground grid points inside a site boundary.

It does not analyze window full-sun duration, facade radiation, roof radiation, or annual irradiance.

## Why does my GeoJSON boundary fail with a WGS84 warning?

The current MVP needs projected meter-based coordinates for grid size, area, and ray geometry. Longitude/latitude degrees are not meters.

Reproject your data before running analysis.

## Can I use OBJ files from Rhino or SketchUp?

Yes, if the OBJ contains one `o` or `g` group per building footprint face. Use `sunlit convert obj` with a `meta.json` file.

Arbitrary closed OBJ mesh conversion is not implemented yet.

## Can I use CAD or DXF files?

Yes, if you make a cleaned DXF copy first. Use closed polylines for the site boundary and building footprints, then map layers and heights in `sunlit.yaml`.

`sunlit` does not automatically clean arbitrary CAD drawings, repair broken lines, infer layers, or read heights from uncontrolled annotations.

## Does AI summary generation work?

Not yet. The current `summary.md` is a deterministic statistical report. AI summary integration is a later step.
