# SVG tools

Requires Python 3.12+, lxml, Pillow, and Playwright **1.58.0** with its Chromium build for previews. Install the pinned packages from `requirements.txt` in a project-local environment, then run `python -m playwright install chromium` if its browser is absent. Text outlining additionally uses the pinned fontTools package and a locally available licensed font. Parsing/validation uses lxml. No sibling skill is needed.

From this skill directory, run:

```bash
python3 scripts/route_style.py --list
python3 scripts/route_style.py --show blueprint
python3 scripts/validate_svg.py /absolute/art.svg
python3 scripts/render_svg.py /absolute/art.svg -o /absolute/preview.png -w 1024 --analyze
```

Use only registry IDs returned by `--list`. For variants pass multiple SVG paths and `--sheet /absolute/comparison.png`. Preserve a source copy before in-place optimization or conversions. The Chromium image embedding route does not execute SVG scripts. Preview support is not a guarantee that every target application supports the same filters/fonts; test the requested target when compatibility matters. Full style library and original craft instructions are from the pinned BuildFast source, with MIT notice in this package.
