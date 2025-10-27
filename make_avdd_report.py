#!/usr/bin/env python3
"""
Generate a portable HTML report with a static PNG bar chart:
x-axis: MM_#
y-axis: "Average - Full Screen(1)" Mean (V)
vertical error bars: Std Dev (V)
y-axis range fixed to 1.1–1.3 V

Embeds the PNG directly as base64 <img> in the HTML (no external JS or CDN).
"""

import argparse
import os
import re
import base64
import io
from pathlib import Path
from typing import Optional, Tuple, List, Dict

import plotly.graph_objects as go

TARGET_MEAS_LABEL = "Average - Full Screen(1)"
MM_REGEX = re.compile(r"MM_(\d+)", re.IGNORECASE)

def parse_results_txt(txt_path: Path) -> Optional[Tuple[float, float]]:
    """Extract (mean, stddev) for 'Average - Full Screen(1)' from results_*.txt."""
    try:
        with txt_path.open("r", encoding="utf-8", errors="ignore") as f:
            lines = [ln.rstrip("\n") for ln in f]

        idx = None
        for i, ln in enumerate(lines):
            if ln.strip().startswith("Measurement ") and TARGET_MEAS_LABEL in ln:
                idx = i
                break

        if idx is None:
            for ln in lines:
                if ln.startswith("Raw Response:"):
                    parts = [p.strip() for p in ln.split(",")]
                    for j, token in enumerate(parts):
                        if token == TARGET_MEAS_LABEL:
                            try:
                                mean = float(parts[j+4].replace("+", ""))
                                std = float(parts[j+5].replace("+", ""))
                                return (mean, std)
                            except Exception:
                                return None
            return None

        mean_val = None
        std_val = None
        for k in range(idx + 1, min(idx + 12, len(lines))):
            t = lines[k].strip()
            if t.startswith("Mean:"):
                try:
                    mean_val = float(t.split()[-1])
                except Exception:
                    pass
            elif t.startswith("Std Dev:"):
                try:
                    std_val = float(t.split()[-1])
                except Exception:
                    pass
            if mean_val is not None and std_val is not None:
                return (mean_val, std_val)
        return None
    except Exception:
        return None

def find_mm_index(path: Path) -> Optional[int]:
    """Extract MM_# from any folder name in path."""
    for part in path.parts[::-1]:
        m = MM_REGEX.search(part)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None
    return None

def collect_measurements(root: Path) -> List[Dict]:
    """Collect measurement data across results_*.txt files."""
    rows = []
    for dirpath, _, filenames in os.walk(root):
        dpath = Path(dirpath)
        mm = find_mm_index(dpath)
        if mm is None:
            continue
        for fn in filenames:
            if fn.startswith("results_") and fn.endswith(".txt"):
                txt = dpath / fn
                res = parse_results_txt(txt)
                if res is None:
                    continue
                mean, std = res
                rows.append({
                    "mm": mm,
                    "mean": mean,
                    "std": std,
                    "file": str(txt),
                    "folder": str(dpath),
                })

    # Keep only newest file per MM
    best_by_mm: Dict[int, Dict] = {}
    for r in rows:
        mm = r["mm"]
        if mm not in best_by_mm:
            best_by_mm[mm] = r
        else:
            old = best_by_mm[mm]
            if os.path.getmtime(r["file"]) >= os.path.getmtime(old["file"]):
                best_by_mm[mm] = r

    return sorted(best_by_mm.values(), key=lambda x: x["mm"])

def build_png(rows: List[Dict], title: str) -> str:
    """Build bar chart with error bars and return base64 PNG string."""
    x = [r["mm"] for r in rows]
    y = [r["mean"] for r in rows]
    yerr = [r["std"] for r in rows]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x,
        y=y,
        error_y=dict(
            type='data',
            array=yerr,
            visible=True,
            thickness=1.5
        ),
        name=TARGET_MEAS_LABEL
    ))
    fig.update_layout(
        title=title,
        xaxis_title="MM #",
        yaxis_title=f"{TARGET_MEAS_LABEL} (V)",
        template="plotly_white",
        margin=dict(l=60, r=30, t=70, b=60),
    )
    fig.update_yaxes(range=[1.1, 1.3])
    fig.update_xaxes(dtick=1)

    # Export to PNG in-memory
    buf = io.BytesIO()
    fig.write_image(buf, format="png", scale=2)  # requires kaleido
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

def write_report(png_uri: str, rows: List[Dict], out_html: Path, heading: str, root: Path):
    table_rows = "\n".join(
        f"<tr><td>MM_{r['mm']}</td><td>{r['mean']:.9f}</td><td>{r['std']:.9f}</td><td>{os.path.basename(r['folder'])}</td></tr>"
        for r in rows
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{heading}</title>
<style>
  body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 1.5rem; }}
  h1 {{ font-size: 1.25rem; margin: 0 0 1rem 0; }}
  .meta {{ color: #555; margin-bottom: 1rem; word-break: break-all; }}
  table {{ border-collapse: collapse; margin-top: 1rem; width: 100%; max-width: 1100px; }}
  th, td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: left; font-size: 0.9rem; }}
  th {{ background: #f7f7f7; }}
  .note {{ color: #666; font-size: 0.85rem; margin-top: .75rem; }}
  img {{ max-width: 100%; height: auto; }}
</style>
</head>
<body>
  <h1>{heading}</h1>
  <div class="meta">Root: <code>{root}</code></div>
  <img src="{png_uri}" alt="Bar chart"/>
  <table>
    <thead>
      <tr><th>MM_#</th><th>Mean ({TARGET_MEAS_LABEL})</th><th>Std Dev</th><th>Folder</th></tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>
  <div class="note">Bars show mean voltage; error bars show ±1×Std Dev parsed from results files. Report is self-contained and works offline.</div>
</body>
</html>"""
    out_html.write_text(html, encoding="utf-8")

def infer_default_title(root: Path) -> str:
    m = re.search(r"(Board_\d+)", str(root))
    board = m.group(1) if m else root.name
    return f"AVDD Static 1A – {board}"

def main():
    ap = argparse.ArgumentParser(description="Generate portable HTML report with embedded PNG bar chart for AVDD measurements.")
    ap.add_argument("root", type=str, help="Root directory (e.g., .../Measurement data/AVDD/Board_00003)")
    ap.add_argument("--out", type=str, default="", help="Output HTML path (default: <root>/AVDD_report.html)")
    ap.add_argument("--title", type=str, default="", help="Report title")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"Root does not exist: {root}")

    rows = collect_measurements(root)
    if not rows:
        raise SystemExit("No matching results found.")

    title = args.title or infer_default_title(root)
    png_uri = build_png(rows, title)
    out_html = Path(args.out) if args.out else (root / "AVDD_report.html")
    write_report(png_uri, rows, out_html, title, root)
    print(f"Report written: {out_html}")

if __name__ == "__main__":
    main()