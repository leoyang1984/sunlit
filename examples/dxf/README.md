# DXF Clean Input Spike

This example is an early DXF workflow spike.

`sunlit convert dxf` is not implemented yet. This folder verifies the planned first-version workflow:

```text
User cleans CAD geometry.
AI writes sunlit.yaml.
User reviews sunlit.yaml.
sunlit inspects and later converts the cleaned DXF.
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

Expected result:

- the configured Chinese layer names are found;
- site/context/scheme layers contain closed polylines;
- unrelated road entities are ignored;
- `conversion_report.md` records the inspection result.
