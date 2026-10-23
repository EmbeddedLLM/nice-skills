#!/usr/bin/env python3
"""Generate an interactive HTML "box picker" for precise PDF-page placement.

Why: for non-fillable forms (no AcroForm fields), text and marks must be
stamped into exact rectangles; drawing them on a rendered page is the fast
route.

What it does:
  1. renders one PDF page to PNG at the requested DPI
  2. emits a self-contained HTML page for drawing rectangles on that image
  3. the page's Export produces a JSON spec with rectangles converted to
     PDF user-space points

Golden path:
  python box_picker_html.py input.pdf --page 1 --dpi 200 --out work/box_picker.html
  # open the HTML in a browser, draw boxes, export JSON

The UI exports:
  {
    "dpi": 200,
    "page": 1,
    "items": [
      {"name": "field_1", "rect": [x0,y0,x1,y1], "kind": "text"}
    ]
  }
with rect in PDF points, origin bottom-left.
"""

from __future__ import annotations

import argparse
import sys
import base64
import subprocess
from pathlib import Path

from pypdf import PdfReader

RENDERER = Path(__file__).resolve().with_name("render_pdf.py")


def render_page_image(pdf: Path, page: int, dpi: int, out_png: Path) -> None:
    out_png.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call([
        sys.executable, str(RENDERER), str(pdf),
        "--out_dir", str(out_png.parent),
        "--pages", str(page),
        "--dpi", str(dpi),
        "--engine", "pdftoppm",
    ])
    produced = out_png.parent / f"page-{page}.png"
    if not produced.exists():
        # Defensive: some renderers number output differently.
        candidates = sorted(out_png.parent.glob("page-*.png"))
        if len(candidates) == 1:
            produced = candidates[0]
    produced.replace(out_png)


PAGE_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>PDF Box Picker</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 20px; }
  main { display: flex; gap: 20px; align-items: flex-start; }
  .stage { position: relative; }
  canvas { border: 1px solid #bbb; max-width: 100%; height: auto; }
  aside { width: 340px; }
  aside textarea { width: 100%; min-height: 240px; font-family: monospace; }
  aside .bar { margin: 10px 0; }
  aside button { padding: 6px 12px; }
  ul { padding-left: 18px; }
  li { cursor: pointer; }
</style>
</head>
<body>
<h2>PDF Box Picker</h2>
<p>PDF: <code>__PDF_NAME__</code> &middot; page <b>__PAGE__</b> &middot; dpi <b>__DPI__</b>
   &middot; page size <b>__W_PT__&times;__H_PT__ pt</b></p>
<main>
  <div class="stage">
    <canvas id="stage"></canvas>
    <p>Drag on the page to draw a rectangle. Click a listed rectangle to rename or delete it.</p>
  </div>
  <aside>
    <div class="bar">
      Default kind:
      <select id="kind">
        <option value="text">text</option>
        <option value="check">checkbox</option>
      </select>
    </div>
    <div class="bar"><button id="export" type="button">Export JSON</button>
    <button id="clear" type="button">Clear</button></div>
    <ul id="list"></ul>
    <textarea id="out" placeholder="JSON output..."></textarea>
    <div class="bar"><small>Coordinates: PDF user space (pt), origin bottom-left.</small></div>
  </aside>
</main>
<script>
const DPI = __DPI__;
const PAGE = __PAGE__;
const boxes = [];  // {name, kind, rect:[x0,y0,x1,y1]} in image pixels

const canvas = document.getElementById("stage");
const ctx = canvas.getContext("2d");
const image = new Image();
image.src = "data:image/png;base64,__PNG_B64__";
image.onload = () => {
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  redraw();
};

function toPdfPoints(rectPx) {
  // Canvas space is pixels, origin top-left.  PDF user space is points
  // (1/72 inch), origin bottom-left — convert in one step.
  const scale = 72.0 / DPI;
  const [x0, y0, x1, y1] = rectPx;
  return [x0 * scale, (canvas.height - y1) * scale, x1 * scale, (canvas.height - y0) * scale];
}

function redraw(pending) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(image, 0, 0);
  for (const box of boxes) drawBox(box.rect, box.name, box.kind, "red", "rgba(255,0,0,0.10)");
  if (pending) drawBox(pending, "", "", "blue", "rgba(0,0,255,0.06)");
  const list = document.getElementById("list");
  list.textContent = "";
  boxes.forEach((box, i) => {
    const li = document.createElement("li");
    li.textContent = `${box.name} (${box.kind})`;
    li.addEventListener("click", () => {
      const renamed = window.prompt("Name (empty deletes the box):", box.name);
      if (renamed === null) return;
      if (renamed === "") boxes.splice(i, 1);
      else box.name = renamed;
      redraw();
    });
    list.appendChild(li);
  });
}

function drawBox(rect, name, kind, stroke, fill) {
  const [x0, y0, x1, y1] = rect;
  ctx.fillStyle = fill;
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 2;
  ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);
  if (name) {
    ctx.fillStyle = "rgba(255,255,255,0.85)";
    ctx.fillRect(x0, Math.max(0, y0 - 16), Math.min(canvas.width - x0, 160), 16);
    ctx.fillStyle = "black";
    ctx.font = "12px sans-serif";
    ctx.fillText(`${name} (${kind})`, x0 + 3, Math.max(12, y0 - 4));
  }
}

function canvasPoint(event) {
  const bounds = canvas.getBoundingClientRect();
  return [
    (event.clientX - bounds.left) * (canvas.width / bounds.width),
    (event.clientY - bounds.top) * (canvas.height / bounds.height),
  ];
}

let dragStart = null;
canvas.addEventListener("pointerdown", (event) => {
  dragStart = canvasPoint(event);
  canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener("pointermove", (event) => {
  if (!dragStart) return;
  const [x, y] = canvasPoint(event);
  redraw([Math.min(dragStart[0], x), Math.min(dragStart[1], y),
          Math.max(dragStart[0], x), Math.max(dragStart[1], y)]);
});
canvas.addEventListener("pointerup", (event) => {
  if (!dragStart) return;
  const [x, y] = canvasPoint(event);
  const rect = [Math.min(dragStart[0], x), Math.min(dragStart[1], y),
                Math.max(dragStart[0], x), Math.max(dragStart[1], y)];
  dragStart = null;
  if (rect[2] - rect[0] < 3 || rect[3] - rect[1] < 3) { redraw(); return; }
  boxes.push({
    name: `item_${boxes.length + 1}`,
    kind: document.getElementById("kind").value,
    rect,
  });
  redraw();
});

document.getElementById("clear").addEventListener("click", () => {
  boxes.length = 0;
  document.getElementById("out").value = "";
  redraw();
});
document.getElementById("export").addEventListener("click", () => {
  const payload = {
    dpi: DPI,
    page: PAGE,
    items: boxes.map((box) => ({ name: box.name, kind: box.kind, rect: toPdfPoints(box.rect) })),
  };
  document.getElementById("out").value = JSON.stringify(payload, null, 2);
});
</script>
</body>
</html>
"""


def build_html(pdf: Path, page: int, dpi: int, width_pt: float, height_pt: float,
               png_b64: str) -> str:
    replacements = {
        "__PDF_NAME__": pdf.name,
        "__PAGE__": str(page),
        "__DPI__": str(dpi),
        "__W_PT__": f"{width_pt:.2f}",
        "__H_PT__": f"{height_pt:.2f}",
        "__PNG_B64__": png_b64,
    }
    html = PAGE_HTML
    for marker, value in replacements.items():
        html = html.replace(marker, value)
    return html


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_pdf")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--out", required=True, help="Output HTML path")
    parser.add_argument("--tmp_dir", default="work/_box_picker",
                        help="Temp render directory")
    args = parser.parse_args()

    source = Path(args.input_pdf)
    reader = PdfReader(str(source))
    page_count = len(reader.pages)
    if not 1 <= args.page <= page_count:
        raise SystemExit(f"--page must be in [1,{page_count}]")

    page_obj = reader.pages[args.page - 1]
    width_pt = float(page_obj.mediabox.width)
    height_pt = float(page_obj.mediabox.height)

    tmp_dir = Path(args.tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    png_path = tmp_dir / "page.png"
    render_page_image(source, args.page, args.dpi, png_path)

    out_html = Path(args.out)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(
        build_html(source, args.page, args.dpi, width_pt, height_pt,
                   base64.b64encode(png_path.read_bytes()).decode("ascii")),
        encoding="utf-8",
    )
    print(str(out_html))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
