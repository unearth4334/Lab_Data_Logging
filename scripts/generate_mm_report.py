"""Generate an HTML report for MM screenshots in output/.

Usage:
    python scripts/generate_mm_report.py

This script scans the output/ directory for images named like:
    B00001_MM_15_CLK_3.png
    B00001_MM_1_DOUT_0.png

It groups images by MM index (0-15) and signal (DOUT/CLK), then
lays them out in 4 columns x 2 rows per MM tile.
"""

from __future__ import annotations

import argparse
import base64
import html
import mimetypes
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "mm_report.html"
METADATA_PATH = OUTPUT_DIR / "metadata.yml"

FILENAME_RE = re.compile(
    r"^(?P<board>[A-Za-z0-9-]+)_MM_(?P<mm>\d{1,2})_(?P<signal>DOUT|CLK)_(?P<index>\d+)\.(?P<ext>png|jpg|jpeg)$",
    re.IGNORECASE,
)


@dataclass
class ScreenshotGroup:
    dout: List[Path] = field(default_factory=list)
    clk: List[Path] = field(default_factory=list)


def _scan_output_images(output_dir: Path) -> Dict[int, ScreenshotGroup]:
    groups: Dict[int, ScreenshotGroup] = {}
    for path in sorted(output_dir.iterdir()):
        if not path.is_file():
            continue
        match = FILENAME_RE.match(path.name)
        if not match:
            continue
        mm = int(match.group("mm"))
        if not 0 <= mm <= 15:
            continue
        signal = match.group("signal").upper()
        index = int(match.group("index"))
        groups.setdefault(mm, ScreenshotGroup())
        if signal == "DOUT":
            groups[mm].dout.append((index, path))
        else:
            groups[mm].clk.append((index, path))

    # sort by numeric index and strip index wrappers
    for mm, group in groups.items():
        group.dout = [p for _, p in sorted(group.dout, key=lambda item: item[0])]
        group.clk = [p for _, p in sorted(group.clk, key=lambda item: item[0])]
    return groups


def _load_metadata(metadata_path: Path) -> Dict[str, str]:
    if not metadata_path.exists():
        return {}
    metadata: Dict[str, str] = {}
    for raw_line in metadata_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata


def _encode_image_data(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(path.name)
    if not mime_type:
        mime_type = "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{data}"


def _make_tile(mm: int, group: ScreenshotGroup, output_dir: Path) -> str:
    def _image_cells(paths: List[Path]) -> str:
        cells = []
        for path in paths[:4]:
            data_uri = _encode_image_data(path)
            cells.append(
                f"<figure class=\"shot\">"
                f"<button class=\"shot-button\" type=\"button\" data-full=\"{data_uri}\" aria-label=\"Open screenshot\">"
                f"<div class=\"frame\" data-crop-x=\"16\" data-crop-y=\"92\" "
                f"data-crop-w=\"636\" data-crop-h=\"479\">"
                f"<img src=\"{data_uri}\" alt=\"Screenshot\">"
                f"</div>"
                f"</button>"
                f"</figure>"
            )
        # pad to 4 columns
        for _ in range(4 - len(cells)):
            cells.append("<div class=\"shot placeholder\">No Image</div>")
        return "\n".join(cells)

    dout_row = _image_cells(group.dout)
    clk_row = _image_cells(group.clk)
    col_headers = "\n".join(
        [
            f"<div class=\"tile-title\">MM {mm:02d}</div>",
            "<div class=\"column-label\">CH_0</div>",
            "<div class=\"column-label\">CH_1</div>",
            "<div class=\"column-label\">CH_2</div>",
            "<div class=\"column-label\">CH_3</div>",
        ]
    )

    return f"""
    <section class=\"tile\" id=\"mm-{mm}\">
      <div class=\"grid\">
        {col_headers}
        <div class=\"row-label\">DOUT</div>
        {dout_row}
        <div class=\"row-label\">CLK</div>
        {clk_row}
      </div>
    </section>
    """


def _build_report(
    groups: Dict[int, ScreenshotGroup],
    output_dir: Path,
    metadata: Dict[str, str],
) -> str:
    tiles = []
    for mm in range(16):
        tiles.append(_make_tile(mm, groups.get(mm, ScreenshotGroup()), output_dir))

    tiles_html = "\n".join(tiles)
    meta_title = html.escape(metadata.get("title", "Measurement Report"))
    meta_subtitle = html.escape(metadata.get("subtitle", ""))
    meta_date = html.escape(metadata.get("date", ""))
    meta_board = html.escape(metadata.get("board", ""))
    meta_operator = html.escape(metadata.get("operator", ""))
    meta_notes = html.escape(metadata.get("notes", ""))

    template = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>Measurement Report - MM Summary</title>
  <style>
    :root {
      --bg: #f6f8fb;
      --ink: #0f172a;
      --muted: #475569;
      --border: #e2e8f0;
      --accent: #1d4ed8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      color: var(--ink);
      background: var(--bg);
    }
    header.report-header {
      padding: 32px 48px 20px;
      border-bottom: 1px solid var(--border);
      background: white;
    }
    .titleblock {
      display: grid;
      grid-template-columns: minmax(200px, 2fr) minmax(200px, 1fr);
      gap: 16px 32px;
      align-items: start;
    }
    .titleblock h1 {
      margin: 0;
      font-size: 28px;
      font-weight: 600;
      letter-spacing: 0.02em;
    }
    .titleblock .subtitle {
      margin-top: 6px;
      color: var(--muted);
      font-size: 13px;
    }
    .titleblock .meta-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(120px, 1fr));
      gap: 8px 16px;
      font-size: 12px;
      color: var(--muted);
    }
    .titleblock .meta-grid strong {
      color: var(--ink);
    }
    .titleblock .notes {
      grid-column: 1 / -1;
      padding: 10px 12px;
      border: 1px dashed var(--border);
      border-radius: 8px;
      background: #f8fafc;
      font-size: 12px;
      color: var(--muted);
    }
    main {
      padding: 24px 48px 48px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(520px, 1fr));
      gap: 24px;
    }
    .tile {
      background: white;
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
      padding: 20px 20px 24px;
    }
    .tile-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--accent);
      display: flex;
      align-items: center;
      justify-content: flex-start;
      padding-left: 6px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .grid {
      display: grid;
      grid-template-columns: 80px repeat(4, minmax(0, 1fr));
      grid-template-rows: auto repeat(2, auto);
      gap: 12px;
      align-items: stretch;
    }
    .row-label {
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: 0.08em;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f8fafc;
      border: 1px dashed var(--border);
      border-radius: 8px;
    }
    .column-label {
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
      font-size: 10px;
      letter-spacing: 0.06em;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f8fafc;
      border: 1px dashed var(--border);
      border-radius: 8px;
      padding: 0 3px;
      line-height: 1;
      min-height: 18px;
    }
    .shot {
      margin: 0;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: #fdfdfd;
      padding: 4px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      align-items: center;
      justify-content: center;
    }
    .frame {
      width: 100%;
      aspect-ratio: 636 / 479;
      border-radius: 6px;
      overflow: hidden;
      background: #ffffff;
      position: relative;
    }
    .frame img {
      position: absolute;
      top: 0;
      left: 0;
      transform-origin: top left;
    }
    .shot-button {
      border: none;
      background: none;
      padding: 0;
      margin: 0;
      width: 100%;
      cursor: pointer;
    }
    .shot-button:focus-visible {
      outline: 2px solid var(--accent);
      outline-offset: 2px;
      border-radius: 8px;
    }
    .popover {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.65);
      display: none;
      align-items: center;
      justify-content: center;
      padding: 32px;
      z-index: 999;
    }
    .popover.open {
      display: flex;
    }
    .popover-content {
      background: white;
      border-radius: 12px;
      padding: 16px;
      max-width: 92vw;
      max-height: 92vh;
      box-shadow: 0 24px 60px rgba(15, 23, 42, 0.35);
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .popover-content img {
      max-width: 88vw;
      max-height: 80vh;
      object-fit: contain;
      border-radius: 8px;
    }
    .popover-close {
      align-self: flex-end;
      border: none;
      background: #e2e8f0;
      color: var(--ink);
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 12px;
      cursor: pointer;
    }
    .shot.placeholder {
      border: 1px dashed var(--border);
      color: #94a3b8;
      font-size: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    footer {
      padding: 16px 48px 32px;
      color: var(--muted);
      font-size: 12px;
    }
  </style>
</head>
<body>
  <header class="report-header">
    <div class="titleblock">
      <div>
        <h1>__META_TITLE__</h1>
        <div class="subtitle">__META_SUBTITLE__</div>
      </div>
      <div class="meta-grid">
        <div><strong>Date:</strong> __META_DATE__</div>
        <div><strong>Board:</strong> __META_BOARD__</div>
        <div><strong>Operator:</strong> __META_OPERATOR__</div>
      </div>
      <div class="notes"><strong>Notes:</strong> __META_NOTES__</div>
    </div>
  </header>
  <main>
    __TILES__
  </main>
  <footer></footer>
  <div class="popover" id="shot-popover" role="dialog" aria-modal="true" aria-hidden="true">
    <div class="popover-content">
      <button class="popover-close" type="button">Close</button>
      <img src="" alt="Full-size screenshot">
    </div>
  </div>
  <script>
    (function () {
      function applyCrop(frame) {
        const img = frame.querySelector("img");
        if (!img) return;
        const cropX = parseFloat(frame.dataset.cropX || "0");
        const cropY = parseFloat(frame.dataset.cropY || "0");
        const cropW = parseFloat(frame.dataset.cropW || "0");
        const cropH = parseFloat(frame.dataset.cropH || "0");

        const resize = () => {
          const frameWidth = frame.clientWidth;
          const scale = frameWidth / cropW;
          img.style.width = (img.naturalWidth * scale) + "px";
          img.style.height = (img.naturalHeight * scale) + "px";
          img.style.transform = "translate(" + (-cropX * scale) + "px, " + (-cropY * scale) + "px)";
        };

        if (img.complete) {
          resize();
        } else {
          img.addEventListener("load", resize, { once: true });
        }

        window.addEventListener("resize", resize);
      }

      document.querySelectorAll(".frame").forEach(applyCrop);

      const popover = document.getElementById("shot-popover");
      const popoverImg = popover.querySelector("img");
      const popoverClose = popover.querySelector(".popover-close");

      function openPopover(src) {
        popoverImg.src = src;
        popover.classList.add("open");
        popover.setAttribute("aria-hidden", "false");
      }

      function closePopover() {
        popover.classList.remove("open");
        popover.setAttribute("aria-hidden", "true");
        popoverImg.src = "";
      }

      document.querySelectorAll(".shot-button").forEach((button) => {
        button.addEventListener("click", () => {
          const src = button.getAttribute("data-full");
          if (src) {
            openPopover(src);
          }
        });
      });

      popoverClose.addEventListener("click", closePopover);
      popover.addEventListener("click", (event) => {
        if (event.target === popover) {
          closePopover();
        }
      });

      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
          closePopover();
        }
      });
    })();
  </script>
</body>
</html>
"""

    return (
        template.replace("__TILES__", tiles_html)
        .replace("__OUTPUT_DIR__", html.escape(str(output_dir)))
        .replace("__META_TITLE__", meta_title)
        .replace("__META_SUBTITLE__", meta_subtitle)
        .replace("__META_DATE__", meta_date)
        .replace("__META_BOARD__", meta_board)
        .replace("__META_OPERATOR__", meta_operator)
        .replace("__META_NOTES__", meta_notes)
    )


def generate_report(output_dir: Path, report_path: Path) -> Path:
    groups = _scan_output_images(output_dir)
    metadata = _load_metadata(output_dir / "metadata.yml")
    report_html = _build_report(groups, output_dir, metadata)
    report_path.write_text(report_html, encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate MM HTML report from output images.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory containing output screenshots (default: output/)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=REPORT_PATH,
        help="Output HTML report path (default: output/mm_report.html)",
    )
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    report_path = args.report.resolve()

    if not output_dir.exists():
        raise SystemExit(f"Output directory not found: {output_dir}")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    generate_report(output_dir, report_path)
    print(f"Report written to: {report_path}")


if __name__ == "__main__":
    main()
