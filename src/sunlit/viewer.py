from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ViewerError(ValueError):
    """Raised when a study viewer cannot be generated."""


RUNS = [
    ("baseline", "Baseline"),
    ("with-scheme", "With Scheme"),
]


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ViewerError(f"Required viewer input does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _english_mode_name(display_name: str) -> str:
    labels = {
        "场地前期评估": "Site Study",
        "方案自评": "Scheme Self-Assessment",
        "方案对周边影响参考": "Neighbor Impact Reference",
    }
    return labels.get(display_name, display_name)


def _run_payload(output_dir: Path, run_name: str, display_name: str) -> dict[str, Any] | None:
    run_dir = output_dir / run_name
    analysis_path = run_dir / "analysis.json"
    heatmap_path = run_dir / "heatmap.png"
    if not analysis_path.exists() or not heatmap_path.exists():
        return None

    analysis = _read_json(analysis_path)
    mode = analysis.get("mode", {})
    stats = analysis.get("statistics", {})
    config = analysis.get("config", {})
    return {
        "id": run_name,
        "label": display_name,
        "heatmap": f"{run_name}/heatmap.png",
        "summary": _read_text(run_dir / "summary.md"),
        "metadata": _read_text(run_dir / "metadata.yaml"),
        "analysis": analysis,
        "mode": _english_mode_name(str(mode.get("display_name", display_name))),
        "config": config,
        "statistics": stats,
    }


def _study_payload(output_dir: Path) -> dict[str, Any]:
    runs = [
        payload
        for run_name, display_name in RUNS
        if (payload := _run_payload(output_dir, run_name, display_name)) is not None
    ]
    if not runs:
        raise ViewerError(f"No analysis runs were found in study output: {output_dir}")
    return {
        "runs": runs,
        "conversionReport": _read_text(output_dir / "conversion_report.md"),
        "integrityNote": (
            "Heatmap pixels are embedded from deterministic output without AI or style edits. "
            "Numeric judgment remains analysis.json + heatmap.png."
        ),
        "disclaimer": (
            "For early design reference only. Not for permitting, legal review, "
            "or full-window sunlight analysis."
        ),
    }


def _html_template(payload: dict[str, Any]) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sunlit Study Viewer</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #e8e4db;
      --paper: #f7f6f1;
      --panel: #ffffff;
      --ink: #111827;
      --muted: #6b7280;
      --line: #d8dee8;
      --soft: #f3f4f6;
      --accent: #f07818;
      --accent-dark: #c65f10;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .shell {{
      width: min(1580px, calc(100vw - 28px));
      min-height: calc(100vh - 28px);
      margin: 14px auto;
      background: var(--paper);
      border: 2px solid #1f2937;
      display: grid;
      grid-template-rows: auto 1fr auto;
      box-shadow: 0 18px 48px rgba(17, 24, 39, 0.18);
    }}
    header {{
      background: #111827;
      color: white;
      padding: 20px 30px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 24px;
      align-items: center;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(24px, 2.6vw, 36px);
      letter-spacing: 0.04em;
      font-weight: 800;
    }}
    .subtitle {{ color: #d1d5db; font-size: 14px; white-space: nowrap; }}
    main {{
      display: grid;
      grid-template-columns: 1fr 320px;
      min-height: 0;
      gap: 24px;
      padding: 24px 30px 18px;
    }}
    .workspace {{
      display: grid;
      grid-template-rows: auto auto 1fr;
      min-width: 0;
      min-height: 0;
      gap: 12px;
    }}
    .toolbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      flex-wrap: wrap;
    }}
    .segmented {{
      display: inline-flex;
      gap: 3px;
      padding: 3px;
      background: #e5e7eb;
      border: 1px solid var(--line);
    }}
    button, .button-link {{
      appearance: none;
      border: 1px solid transparent;
      background: transparent;
      color: var(--ink);
      font: inherit;
      font-size: 13px;
      padding: 7px 12px;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 34px;
    }}
    button.active {{
      background: white;
      border-color: #cfd6df;
      box-shadow: 0 1px 2px rgba(17, 24, 39, 0.08);
      font-weight: 700;
    }}
    .button-link {{
      border-color: var(--line);
      background: white;
    }}
    .view-controls {{
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .tabs {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      border-bottom: 1px solid var(--line);
    }}
    .tabs button {{
      border-bottom: 2px solid transparent;
      padding-inline: 10px;
    }}
    .tabs button.active {{
      box-shadow: none;
      border-color: transparent transparent var(--accent) transparent;
      background: transparent;
      color: var(--accent-dark);
    }}
    .content {{
      min-height: 0;
      background: white;
      border: 1px solid var(--line);
      overflow: hidden;
      display: grid;
    }}
    .map-panel {{
      min-height: 0;
      overflow: auto;
      display: grid;
      place-items: center;
      background: #fafafa;
      padding: 18px;
    }}
    .heatmap {{
      display: block;
      object-fit: contain;
      max-width: 100%;
      max-height: calc(100vh - 260px);
      background: white;
    }}
    .heatmap.zoom-100 {{ max-width: none; max-height: none; width: auto; height: auto; }}
    .heatmap.zoom-150 {{ max-width: none; max-height: none; width: 150%; height: auto; }}
    .text-panel {{
      min-height: 0;
      overflow: auto;
      padding: 24px;
      background: white;
    }}
    .markdown h1, .markdown h2, .markdown h3 {{ margin: 0 0 12px; }}
    .markdown h1 {{ font-size: 24px; }}
    .markdown h2 {{ font-size: 19px; margin-top: 22px; }}
    .markdown p {{ line-height: 1.55; }}
    .markdown ul {{ padding-left: 22px; }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-size: 12px;
      line-height: 1.5;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    }}
    aside {{
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 22px;
      min-width: 0;
      overflow: auto;
    }}
    aside h2 {{
      margin: 0 0 18px;
      font-size: 22px;
      line-height: 1;
    }}
    .kv {{ display: grid; gap: 14px; }}
    .label {{ color: var(--muted); font-size: 12px; margin-bottom: 5px; display: block; }}
    .value {{ font-size: 15px; line-height: 1.3; }}
    .divider {{ height: 1px; background: var(--line); margin: 22px 0; }}
    .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .metric {{
      border: 1px solid #e5e7eb;
      background: #fafafa;
      padding: 12px;
      min-height: 74px;
    }}
    .metric.wide {{ grid-column: 1 / -1; }}
    .metric .value {{ font-size: 18px; font-weight: 750; }}
    footer {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 18px;
      align-items: center;
      padding: 0 30px 24px;
      color: #4b5563;
      font-size: 13px;
    }}
    .integrity {{
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.72);
      padding: 12px 16px;
      color: #374151;
    }}
    .integrity strong {{ color: var(--ink); margin-right: 14px; }}
    .hidden {{ display: none !important; }}
    @media (max-width: 980px) {{
      .shell {{ width: 100vw; min-height: 100vh; margin: 0; border-inline: 0; }}
      header, main, footer {{ padding-inline: 18px; }}
      main {{ grid-template-columns: 1fr; }}
      aside {{ order: -1; }}
      footer {{ grid-template-columns: 1fr; }}
      .heatmap {{ max-height: 70vh; }}
    }}
  </style>
</head>
<body>
  <section class="shell">
    <header>
      <h1>SUNLIT STUDY VIEWER</h1>
      <div class="subtitle">Design-stage reference</div>
    </header>
    <main>
      <section class="workspace">
        <div class="toolbar">
          <div id="runButtons" class="segmented" aria-label="Study runs"></div>
          <div class="view-controls">
            <div id="zoomButtons" class="segmented" aria-label="Map zoom">
              <button type="button" data-zoom="fit" class="active">Fit</button>
              <button type="button" data-zoom="100">100%</button>
              <button type="button" data-zoom="150">150%</button>
            </div>
            <a id="rawHeatmapLink" class="button-link" href="#" target="_blank" rel="noreferrer">Open heatmap</a>
          </div>
        </div>
        <nav id="tabs" class="tabs" aria-label="Viewer tabs">
          <button type="button" data-tab="map" class="active">Map</button>
          <button type="button" data-tab="summary">Summary</button>
          <button type="button" data-tab="metadata">Metadata</button>
          <button type="button" data-tab="json">JSON</button>
          <button type="button" data-tab="conversion">Conversion</button>
        </nav>
        <section class="content">
          <div id="mapPanel" class="map-panel">
            <img id="heatmap" class="heatmap" src="" alt="Sunlight heatmap">
          </div>
          <div id="summaryPanel" class="text-panel markdown hidden"></div>
          <div id="metadataPanel" class="text-panel hidden"><pre></pre></div>
          <div id="jsonPanel" class="text-panel hidden"><pre></pre></div>
          <div id="conversionPanel" class="text-panel markdown hidden"></div>
        </section>
      </section>
      <aside>
        <h2>Study Setup</h2>
        <div id="setup" class="kv"></div>
        <div class="divider"></div>
        <h2>Key Results</h2>
        <div id="metrics" class="metrics"></div>
      </aside>
    </main>
    <footer>
      <div class="integrity"><strong>Integrity note</strong><span id="integrityNote"></span></div>
      <div id="disclaimer"></div>
    </footer>
  </section>
  <script type="application/json" id="sunlit-payload">{payload_json}</script>
  <script>
    const payload = JSON.parse(document.getElementById('sunlit-payload').textContent);
    let currentRun = payload.runs[0]?.id;
    let currentTab = 'map';

    function escapeHtml(value) {{
      return String(value ?? '').replace(/[&<>"']/g, ch => ({{
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
      }}[ch]));
    }}

    function markdownToHtml(markdown) {{
      const lines = String(markdown || '').split(/\\r?\\n/);
      const out = [];
      let inList = false;
      for (const line of lines) {{
        if (line.startsWith('# ')) {{
          if (inList) {{ out.push('</ul>'); inList = false; }}
          out.push(`<h1>${{escapeHtml(line.slice(2))}}</h1>`);
        }} else if (line.startsWith('## ')) {{
          if (inList) {{ out.push('</ul>'); inList = false; }}
          out.push(`<h2>${{escapeHtml(line.slice(3))}}</h2>`);
        }} else if (line.startsWith('- ')) {{
          if (!inList) {{ out.push('<ul>'); inList = true; }}
          out.push(`<li>${{escapeHtml(line.slice(2))}}</li>`);
        }} else if (!line.trim()) {{
          if (inList) {{ out.push('</ul>'); inList = false; }}
        }} else {{
          if (inList) {{ out.push('</ul>'); inList = false; }}
          out.push(`<p>${{escapeHtml(line)}}</p>`);
        }}
      }}
      if (inList) out.push('</ul>');
      return out.join('\\n');
    }}

    function formatNumber(value, digits = 2) {{
      const number = Number(value);
      return Number.isFinite(number) ? number.toFixed(digits) : '';
    }}

    function selectedRun() {{
      return payload.runs.find(run => run.id === currentRun) || payload.runs[0];
    }}

    function renderRunButtons() {{
      const root = document.getElementById('runButtons');
      root.innerHTML = payload.runs.map(run =>
        `<button type="button" data-run="${{escapeHtml(run.id)}}" class="${{run.id === currentRun ? 'active' : ''}}">${{escapeHtml(run.label)}}</button>`
      ).join('');
      root.querySelectorAll('button').forEach(button => {{
        button.addEventListener('click', () => {{
          currentRun = button.dataset.run;
          render();
        }});
      }});
      if (payload.runs.length < 2) root.classList.add('hidden');
    }}

    function renderSetup(run) {{
      const c = run.config || {{}};
      const items = [
        ['Mode', run.mode],
        ['Date', c.date],
        ['Time', `${{c.time_start || ''}} - ${{c.time_end || ''}}`],
        ['Grid', `${{c.grid_size_meters ?? ''}} m`],
        ['Threshold', `${{c.threshold_hours ?? ''}} h`]
      ];
      document.getElementById('setup').innerHTML = items.map(([label, value]) =>
        `<div><span class="label">${{escapeHtml(label)}}</span><span class="value">${{escapeHtml(value)}}</span></div>`
      ).join('');
    }}

    function renderMetrics(run) {{
      const s = run.statistics || {{}};
      const items = [
        ['Qualified', `${{s.qualified_points ?? ''}} / ${{s.total_points ?? ''}}`, 'wide'],
        ['Qualified pct', `${{formatNumber(s.qualified_pct, 1)}}%`, ''],
        ['Qualified area', `${{formatNumber(s.qualified_area_sqm, 0)}} m²`, ''],
        ['Avg sunlight', `${{formatNumber(s.avg_hours)}} h`, ''],
        ['Min / Max', `${{formatNumber(s.min_hours)}} / ${{formatNumber(s.max_hours)}} h`, '']
      ];
      document.getElementById('metrics').innerHTML = items.map(([label, value, klass]) =>
        `<div class="metric ${{klass}}"><div class="label">${{escapeHtml(label)}}</div><div class="value">${{escapeHtml(value)}}</div></div>`
      ).join('');
    }}

    function showTab(tab) {{
      currentTab = tab;
      for (const id of ['map', 'summary', 'metadata', 'json', 'conversion']) {{
        document.getElementById(`${{id}}Panel`).classList.toggle('hidden', id !== tab);
      }}
      document.querySelectorAll('#tabs button').forEach(button => {{
        button.classList.toggle('active', button.dataset.tab === tab);
      }});
      document.querySelector('.view-controls').classList.toggle('hidden', tab !== 'map');
    }}

    function render() {{
      const run = selectedRun();
      renderRunButtons();
      renderSetup(run);
      renderMetrics(run);
      const heatmap = document.getElementById('heatmap');
      heatmap.src = run.heatmap;
      document.getElementById('rawHeatmapLink').href = run.heatmap;
      document.getElementById('summaryPanel').innerHTML = markdownToHtml(run.summary || 'No summary.md was found for this run.');
      document.querySelector('#metadataPanel pre').textContent = run.metadata || 'No metadata.yaml was found for this run.';
      document.querySelector('#jsonPanel pre').textContent = JSON.stringify(run.analysis, null, 2);
      document.getElementById('conversionPanel').innerHTML = markdownToHtml(payload.conversionReport || 'No conversion_report.md was found.');
      document.getElementById('integrityNote').textContent = payload.integrityNote;
      document.getElementById('disclaimer').textContent = payload.disclaimer;
      showTab(currentTab);
    }}

    document.querySelectorAll('#tabs button').forEach(button => {{
      button.addEventListener('click', () => showTab(button.dataset.tab));
    }});
    document.querySelectorAll('#zoomButtons button').forEach(button => {{
      button.addEventListener('click', () => {{
        document.querySelectorAll('#zoomButtons button').forEach(item => item.classList.remove('active'));
        button.classList.add('active');
        const heatmap = document.getElementById('heatmap');
        heatmap.classList.remove('zoom-100', 'zoom-150');
        if (button.dataset.zoom === '100') heatmap.classList.add('zoom-100');
        if (button.dataset.zoom === '150') heatmap.classList.add('zoom-150');
      }});
    }});
    render();
  </script>
</body>
</html>
"""


def render_study_viewer(output_dir: Path) -> Path:
    payload = _study_payload(output_dir)
    viewer_path = output_dir / "presentation.html"
    viewer_path.write_text(_html_template(payload), encoding="utf-8")
    return viewer_path
