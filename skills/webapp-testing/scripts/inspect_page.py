#!/usr/bin/env python3
"""Inspect a local HTML file or URL with Playwright; save screenshot and console.

No hard-coded page controls, output paths, network-idle waits, or submissions.
"""

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit


def inspect(target, output, ready=None, width=1280, height=800):
    from playwright.sync_api import sync_playwright

    if urlsplit(target).scheme not in ("http", "https", "file"):
        target = Path(target).resolve().as_uri()
    output.mkdir(parents=True, exist_ok=False)
    logs = []
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on(
                "console", lambda msg: logs.append({"type": msg.type, "text": msg.text})
            )
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.goto(target, wait_until="domcontentloaded", timeout=30000)
            if ready:
                page.locator(ready).wait_for(state="visible", timeout=30000)
            controls = page.locator(
                "button,a[href],input,textarea,select"
            ).evaluate_all("""els=>els.map(e=>({
                tag:e.tagName.toLowerCase(),text:e.textContent.trim(),id:e.id,
                name:e.getAttribute('name'),type:e.getAttribute('type'),href:e.getAttribute('href'),
                visible:!!(e.getClientRects().length)}))""")
            page.screenshot(path=str(output / "page.png"), full_page=True)
            report = {
                "url": target,
                "controls": controls,
                "console": logs,
                "page_errors": errors,
            }
            (output / "report.json").write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )
            return report
        finally:
            browser.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("target")
    p.add_argument("output", type=Path)
    p.add_argument("--ready", help="Visible selector indicating the desired page state")
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=800)
    a = p.parse_args()
    if a.width <= 0 or a.height <= 0:
        p.error("Viewport dimensions must be positive")
    result = inspect(a.target, a.output, a.ready, a.width, a.height)
    print(a.output / "report.json")
    raise SystemExit(bool(result["page_errors"]))
