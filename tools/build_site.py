#!/usr/bin/env python3
"""Build the repository homepage from the published catalog and theme guide."""
import argparse
import html
import json
from pathlib import Path
import re
import runpy
import shutil

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/EmbeddedLLM/nice-skills"
GROUPS = {
    "Research & writing": "deep-research doc-coauthoring resolve-recipients",
    "Documents & data": "documents pdf slides spreadsheets",
    "Design & web": "frontend-design design-taste webapp-testing canvas-design algorithmic-art vector-art theme-factory design-research",
    "Motion & sound": "gif-creator create-motion-videos explainer-video presenter-video sound-design",
    "Engineering": "mcp-builder review-agent security-audit software-workflow procedural-3d game-development skill-creator",
}


def catalog():
    """Read the public catalog, preserving its descriptions and requirements."""
    entries = []
    for line in (ROOT / "skills/README.md").read_text().splitlines():
        match = re.fullmatch(r"\| \[([^]]+)\]\(([^)]+)\) \| (.+?) \| (.+?) \|", line)
        if not match:
            continue
        name, path, description, requirements = match.groups()
        if not (ROOT / "skills" / path).is_file():
            raise ValueError(f"Missing catalog entry: {path}")
        group = next((label for label, names in GROUPS.items() if name in names.split()), "Other")
        entries.append(dict(name=name, path=path, description=description, requirements=requirements, group=group))
    published = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
    if {entry["name"] for entry in entries} != published or len(entries) != len(published):
        raise ValueError("The catalog must list every published skill exactly once")
    return entries


def build(output):
    entries = catalog()
    theme_tools = runpy.run_path(str(ROOT / "skills/theme-factory/scripts/themes.py"))
    data, custom, themes = theme_tools["load"]()
    theme_tools["verify"](data, custom, themes)
    escape = html.escape
    cards = []
    for entry in entries:
        cards.append(f'''<article class="skill" data-group="{escape(entry['group'])}">
  <span class="skill-group">{escape(entry['group'])}</span>
  <h3><a href="{REPOSITORY}/blob/main/skills/{escape(entry['path'])}">{escape(entry['name'])}<span aria-hidden="true">↗</span></a></h3>
  <p>{escape(entry['description'])}</p>
  <details><summary>Local requirements</summary><p>{escape(entry['requirements'])}</p></details>
</article>''')
    options = []
    for mood in data["moods"]:
        members = [theme for theme in themes if theme["mood_id"] == mood["id"]]
        options.append(f'<optgroup label="{escape(mood["name"])}">' + "".join(
            f'<option value="{theme["slug"]}"{ " selected" if theme["slug"] == "lavender" else ""}>{escape(theme["display_name"])}</option>'
            for theme in members) + '</optgroup>')
    theme_data = [dict(slug=t["slug"], colors=t["colors"]) for t in themes]
    page = (ROOT / "site/index.html").read_text()
    replacements = {
        "{{SKILLS}}": "\n".join(cards), "{{COUNT}}": str(len(entries)),
        "{{THEME_COUNT}}": str(len(themes)), "{{THEME_OPTIONS}}": "".join(options),
        "{{GROUP_OPTIONS}}": "".join(f'<option>{escape(group)}</option>' for group in dict.fromkeys(entry["group"] for entry in entries)),
        "{{THEME_DATA}}": json.dumps(theme_data).replace("<", "\\u003c"),
    }
    for key, value in replacements.items():
        page = page.replace(key, value)
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(page)
    (output / "themes.css").write_text("\n".join(theme_tools["css"](theme, custom) +
        f'\n[data-palette="{theme["slug"]}"] {{ color-scheme: {theme["web"]["mode"]}; }}\n' for theme in themes))
    for name in ("styles.css", "app.js", "favicon.svg"):
        shutil.copyfile(ROOT / "site" / name, output / name)
    (output / ".nojekyll").touch()
    print(f"Built {len(entries)} skills and {len(themes)} themes in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    build(parser.parse_args().output)
