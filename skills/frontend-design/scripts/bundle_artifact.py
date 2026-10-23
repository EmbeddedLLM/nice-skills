#!/usr/bin/env python3
"""Inline local classic JS, CSS, and image assets into a new HTML file.

This is a static inliner: build framework code first. Modules, srcset, CSS imports, remote
assets, base URLs and deferred scripts are refused rather than silently broken.
Runtime fetches/workers are not statically detectable: test the exported file.
"""

import argparse
import base64
import html
from html.parser import HTMLParser
import mimetypes
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


class Bundler(HTMLParser):
    def __init__(self, entry):
        super().__init__(convert_charrefs=False)
        self.root = entry.parent.resolve()
        self.parts = []
        self.skip_script = False
        self.in_style = False

    def asset(self, url, directory=None):
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc or not parsed.path or parsed.query:
            raise ValueError(f"Expected a local asset without query parameters: {url}")
        path = ((directory or self.root) / unquote(parsed.path)).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            raise ValueError(f"Missing/outside-root asset: {url}")
        return path

    def data_url(self, url, directory=None):
        if url.startswith(("data:", "#")):
            return url
        p = self.asset(url, directory)
        return (
            "data:"
            + (mimetypes.guess_type(p.name)[0] or "application/octet-stream")
            + ";base64,"
            + base64.b64encode(p.read_bytes()).decode()
            + ("#" + urlsplit(url).fragment if urlsplit(url).fragment else "")
        )

    def css(self, text, directory):
        if re.search(r"@import\b", text, re.I):
            raise ValueError("Build CSS @imports before inlining")
        return re.sub(
            r'url\(\s*([\'"]?)(.*?)\1\s*\)',
            lambda m: 'url("' + self.data_url(m[2], directory) + '")',
            text,
            flags=re.I,
        )

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "base" or "srcset" in a:
            raise ValueError("base/srcset requires a project-aware bundler")
        if tag == "script":
            if a.get("type") == "module" or "async" in a or "defer" in a:
                raise ValueError(
                    "Build modules/deferred scripts into a classic bundle first"
                )
            if "src" in a:
                p = self.asset(a["src"])
                text = re.sub(
                    r"</script",
                    lambda m: "<\\/" + m[0][2:],
                    p.read_text(encoding="utf-8"),
                    flags=re.I,
                )
                self.parts.append("<script>" + text + "</script>")
                self.skip_script = True
                return
        if tag == "link" and "stylesheet" in a.get("rel", "").split():
            if a.get("media") not in (None, "", "all"):
                raise ValueError(
                    "Conditional stylesheets require a project-aware bundler"
                )
            p = self.asset(a["href"])
            self.parts.append(
                "<style>"
                + re.sub(
                    r"</style",
                    lambda m: "<\\/" + m[0][2:],
                    self.css(p.read_text(), p.parent),
                    flags=re.I,
                )
                + "</style>"
            )
            return
        if tag == "link" and a.get("rel") in ("modulepreload", "preload"):
            raise ValueError("Remove build preload hints before inlining")
        rewritten = []
        for k, v in attrs:
            if k == "src" and tag in ("img", "audio", "video", "source"):
                v = self.data_url(v)
            if k == "poster":
                v = self.data_url(v)
            if k == "style":
                v = self.css(v, self.root)
            rewritten.append(
                " "
                + k
                + (('="' + html.escape(v, quote=True) + '"') if v is not None else "")
            )
        self.parts.append("<" + tag + "".join(rewritten) + ">")
        if tag == "style":
            self.in_style = True

    def handle_endtag(self, tag):
        if tag == "script" and self.skip_script:
            self.skip_script = False
            return
        if tag == "style":
            self.in_style = False
        self.parts.append("</" + tag + ">")

    def handle_data(self, data):
        if not self.skip_script:
            self.parts.append(self.css(data, self.root) if self.in_style else data)

    def handle_entityref(self, name):
        self.parts.append("&" + name + ";")

    def handle_charref(self, name):
        self.parts.append("&#" + name + ";")

    def handle_comment(self, data):
        self.parts.append("<!--" + data + "-->")

    def handle_decl(self, decl):
        self.parts.append("<!" + decl + ">")


def bundle(entry, output):
    entry = Path(entry)
    parser = Bundler(entry)
    parser.feed(entry.read_text(encoding="utf-8"))
    parser.close()
    with Path(output).open("x", encoding="utf-8") as stream:
        stream.write("".join(parser.parts))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("entry", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    try:
        bundle(a.entry, a.output)
    except (ValueError, OSError) as exc:
        p.exit(1, f"Error: {exc}\n")
