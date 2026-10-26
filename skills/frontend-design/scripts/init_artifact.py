#!/usr/bin/env python3
"""Create a dependency-free HTML/CSS/JS starter in a new directory.

Creates the starter without installing packages or replacing an existing
project's configuration.
"""

import argparse
from pathlib import Path


def create(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=False)
    (
        path / "index.html"
    ).write_text("""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>Local artifact</title>
<link rel="stylesheet" href="style.css"><main><h1>Local artifact</h1>
<button id="increment">Add one</button><output id="count" aria-live="polite">0</output></main>
<script src="app.js"></script></html>\n""")
    (path / "style.css").write_text(
        "body{font:18px system-ui;margin:3rem;line-height:1.5}button{font:inherit;padding:.5rem}output{margin:1rem}\n"
    )
    (path / "app.js").write_text(
        "let count=0;document.querySelector('#increment').onclick=()=>{document.querySelector('#count').textContent=++count;};\n"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    a = p.parse_args()
    create(a.directory)
