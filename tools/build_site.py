#!/usr/bin/env python3
"""Build the repository homepage from the published catalog and theme guide."""
import argparse
import html
import importlib.util
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/EmbeddedLLM/nice-skills"
GROUPS = {
    "Research & writing": "deep-research doc-coauthoring resolve-recipients",
    "Documents & data": "documents pdf slides spreadsheets",
    "Design & web": "frontend-design design-taste webapp-testing canvas-design algorithmic-art vector-art theme-factory design-research",
    "Motion & sound": "gif-creator create-motion-videos explainer-video presenter-video sound-design",
    "Engineering": "mcp-builder review-agent security-audit software-workflow procedural-3d game-development skill-creator",
}


def catalog(source=None):
    """Read the public catalog, preserving its descriptions and requirements."""
    source = ROOT if source is None else source
    entries = []
    for line in (source / "skills/README.md").read_text().splitlines():
        match = re.fullmatch(r"\| \[([^]]+)\]\(([^)]+)\) \| (.+?) \| (.+?) \|", line)
        if not match:
            continue
        name, path, description, requirements = match.groups()
        if not (source / "skills" / path).is_file():
            raise ValueError(f"Missing catalog entry: {path}")
        group = next((label for label, names in GROUPS.items() if name in names.split()), "Other")
        entries.append(dict(name=name, path=path, description=description, requirements=requirements, group=group))
    published = {path.parent.name for path in (source / "skills").glob("*/SKILL.md")}
    if {entry["name"] for entry in entries} != published or len(entries) != len(published):
        raise ValueError("The catalog must list every published skill exactly once")
    return entries


def render_skill(markdown, name, source_url):
    """Render a skill as inert Markdown, preserving source-relative links and local headings."""
    # Only builds need this dependency; the preview-comment command stays standard-library only.
    from markdown_it import MarkdownIt

    metadata = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", markdown, re.S)
    body = markdown[metadata.end():] if metadata else markdown
    renderer = MarkdownIt("js-default")  # Raw HTML is displayed as text, never executed.
    tokens = renderer.parse(body)
    prefix = f"skill-{name}-"
    headings = {}
    for index, token in enumerate(tokens):
        if token.type == "heading_open":
            label = "".join(child.content for child in tokens[index + 1].children
                            if child.type in {"text", "code_inline"})
            slug = re.sub(r"[^\w\s-]", "", label.lower()).replace(" ", "-")
            count = headings.get(slug, 0)
            headings[slug] = count + 1
            token.attrSet("id", prefix + slug + (f"-{count}" if count else ""))
        for child in token.children or []:
            if child.type == "link_open":
                href = child.attrGet("href")
                child.attrSet("href", "#" + prefix + href[1:] if href.startswith("#") else urljoin(source_url, href))
            elif child.type == "image":
                raw_url = source_url.replace("https://github.com/", "https://raw.githubusercontent.com/", 1).replace("/blob/", "/", 1)
                child.attrSet("src", urljoin(raw_url, child.attrGet("src")))
    rendered = renderer.renderer.render(tokens, renderer.options, {})
    if metadata:
        rendered += ('<details class="skill-metadata"><summary>Skill metadata</summary><pre><code>' +
                     html.escape(metadata[1]) + '</code></pre></details>')
    return rendered


def build(output, source=None, source_ref="main"):
    source = ROOT if source is None else source
    entries = catalog(source)
    # Snapshot inputs are data. Always execute theme helpers from the trusted checkout.
    spec = importlib.util.spec_from_file_location("site_themes", ROOT / "skills/theme-factory/scripts/themes.py")
    theme_tools = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(theme_tools)
    theme_tools.GUIDE = source / "skills/theme-factory/assets/theme-guide.html"
    data, custom, themes = theme_tools.load()
    theme_tools.verify(data, custom, themes)
    escape = html.escape
    cards = []
    readers = []
    for entry in sorted(entries, key=lambda entry: entry["name"]):
        source_url = f"{REPOSITORY}/blob/{source_ref}/skills/{entry['path']}"
        document = render_skill((source / "skills" / entry["path"]).read_text(), entry["name"], source_url)
        readers.append(f'<template id="skill-doc-{escape(entry["name"])}">{document}</template>')
        cards.append(f'''<article class="skill" data-group="{escape(entry['group'])}">
  <span class="skill-group">{escape(entry['group'])}</span>
  <h3><a data-skill="{escape(entry['name'])}" aria-haspopup="dialog" href="{escape(source_url)}">{escape(entry['name'])}<span aria-hidden="true">→</span></a></h3>
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
    page = (source / "site/index.html").read_text()
    replacements = {
        "{{SKILLS}}": "\n".join(cards), "{{SKILL_READERS}}": "\n".join(readers), "{{COUNT}}": str(len(entries)),
        "{{THEME_COUNT}}": str(len(themes)), "{{THEME_OPTIONS}}": "".join(options),
        "{{GROUP_OPTIONS}}": "".join(f'<option>{escape(group)}</option>' for group in dict.fromkeys(entry["group"] for entry in entries)),
        "{{THEME_DATA}}": json.dumps(theme_data).replace("<", "\\u003c"),
    }
    # Substitute only the page template; skill examples may contain the same placeholder syntax.
    page = re.sub("|".join(re.escape(key) for key in replacements), lambda match: replacements[match[0]], page)
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(page)
    (output / "themes.css").write_text("\n".join(theme_tools.css(theme, custom) +
        f'\n[data-palette="{theme["slug"]}"] {{ color-scheme: {theme["web"]["mode"]}; }}\n' for theme in themes))
    for name in ("styles.css", "app.js", "favicon.svg"):
        shutil.copyfile(source / "site" / name, output / name)
    (output / ".nojekyll").touch()
    print(f"Built {len(entries)} skills and {len(themes)} themes in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--source", type=Path, default=ROOT,
                        help="Read homepage, catalog, and theme data here; helpers still run from this checkout")
    parser.add_argument("--source-ref", default="main", help="Git ref used by skill source links")
    args = parser.parse_args()
    build(args.output, args.source, args.source_ref)
