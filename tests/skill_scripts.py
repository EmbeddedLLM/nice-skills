"""Shared plumbing for the skill-script contract tests.

Every skill package under ``skills/`` ships executable helpers whose contract
is defined by their ``SKILL.md`` prose, their ``--help`` text and the artifacts
they emit.  The suites that import this module pin that contract: they drive
the real scripts as subprocesses (so argument parsing, exit codes and stdout
shape are all exercised) and, where a script is also a library, they import it
in a child interpreter with the package's own ``PYTHONPATH`` layout.

The helpers deliberately stay small: a temp workspace, a runner that fails
loudly with captured output, and dependency probes that turn a missing
LibreOffice/Poppler/Node module into a skip instead of a red build.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

# Optional third-party modules that individual scripts import at load time.
OPTIONAL_MODULES = {
    "PIL": "Pillow",
    "docx": "python-docx",
    "pptx": "python-pptx",
    "openpyxl": "openpyxl",
    "pypdf": "pypdf",
    "pdfplumber": "pdfplumber",
    "reportlab": "reportlab",
    "fitz": "PyMuPDF",
    "pdf2image": "pdf2image",
    "lxml": "lxml",
    "yaml": "PyYAML",
    "numpy": "numpy",
    "scipy": "scipy",
    "imageio_ffmpeg": "imageio-ffmpeg",
    "playwright": "playwright",
    "fontTools": "fonttools",
    "defusedxml": "defusedxml",
}


def module_available(import_name: str) -> bool:
    """True when ``import_name`` can be imported in the running interpreter."""
    if import_name in sys.modules:
        return True
    try:
        spec = importlib.util.find_spec(import_name)
    except (ImportError, ValueError):
        return False
    return spec is not None


def require_module(import_name: str):
    """Skip decorator naming the pip requirement that is missing."""
    return unittest.skipUnless(
        module_available(import_name),
        f"requires the {OPTIONAL_MODULES.get(import_name, import_name)} package",
    )


def binary(name: str) -> str | None:
    return shutil.which(name)


def require_binary(name: str):
    return unittest.skipUnless(binary(name) is not None, f"requires `{name}` on PATH")


def require_modules(*names):
    missing = [n for n in names if not module_available(n)]
    return unittest.skipUnless(
        not missing,
        "requires " + ", ".join(OPTIONAL_MODULES.get(m, m) for m in missing),
    )


def node_modules_ready(package_dir: Path) -> bool:
    """True when a Node package directory has its dependencies installed."""
    return (package_dir / "node_modules").is_dir()


# The PptxGenJS helpers resolve their peers (skia-canvas, prismjs, mathjax-full,
# linebreak, pptxgenjs) through NODE_PATH.  Tests point NODE_PATH at
# whichever of these locations actually has them, and skip when none does.
NODE_PATH_CANDIDATES = (
    os.environ.get("SKILL_NODE_MODULES"),
    str(SKILLS / "slides" / "pptxgenjs_helpers" / "node_modules"),
    str(SKILLS / "slides" / "node_modules"),
    str(ROOT / "node_modules"),
)

#: Peers that ``slides/pptxgenjs_helpers/index.js`` needs at require time.
SLIDE_HELPER_PEERS = (
    "skia-canvas", "linebreak", "prismjs", "mathjax-full", "pptxgenjs",
)


def slide_helper_node_path() -> str | None:
    """Return a NODE_PATH value holding every helper peer, or ``None``."""
    for candidate in NODE_PATH_CANDIDATES:
        if not candidate:
            continue
        base = Path(candidate)
        if all((base / peer).is_dir() for peer in SLIDE_HELPER_PEERS):
            return str(base)
    return None


def require_slide_helpers():
    return unittest.skipUnless(
        slide_helper_node_path() is not None,
        "requires the PptxGenJS helper peers (" + ", ".join(SLIDE_HELPER_PEERS)
        + "); see tests/README.md",
    )


class Completed:
    """Thin wrapper over ``subprocess.CompletedProcess`` with handy accessors."""

    def __init__(self, proc: subprocess.CompletedProcess):
        self._proc = proc

    def __getattr__(self, item):
        return getattr(self._proc, item)

    @property
    def detail(self) -> str:
        return (
            f"\n--- command ---\n{' '.join(map(str, self._proc.args))}"
            f"\n--- exit {self._proc.returncode} ---"
            f"\n--- stdout ---\n{self._proc.stdout}"
            f"\n--- stderr ---\n{self._proc.stderr}"
        )

    def json(self) -> object:
        return json.loads(self._proc.stdout)


class ScriptCase(unittest.TestCase):
    """Base class providing a scratch workspace and script runners."""

    #: Skills whose scripts this case drives; subclasses may override.
    package_dirs: tuple[str, ...] = ()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="skilltest-")
        self.addCleanup(self._tmp.cleanup)
        self.work = Path(self._tmp.name)

    # -- paths ---------------------------------------------------------
    def script(self, *parts: str) -> Path:
        """Resolve ``skills/<parts...>`` and assert it exists."""
        path = SKILLS.joinpath(*parts)
        self.assertTrue(path.is_file(), f"missing script {path}")
        return path

    # -- running -------------------------------------------------------
    def run_python(self, script: Path, *args, code=0, cwd=None, env=None,
                   input=None, timeout=180, check=True):
        cmd = [sys.executable, str(script), *[str(a) for a in args]]
        return self._run(cmd, code=code, cwd=cwd, env=env, input=input,
                         timeout=timeout, check=check)

    def run_node(self, script, *args, code=0, cwd=None, env=None,
                 input=None, timeout=180, check=True):
        cmd = ["node", str(script), *[str(a) for a in args]]
        return self._run(cmd, code=code, cwd=cwd, env=env, input=input,
                         timeout=timeout, check=check)

    def run_node_source(self, source: str, *args, code=0, cwd=None, env=None,
                        node_path=None, timeout=180, check=True):
        """Run a JavaScript snippet through ``node -e``."""
        child_env = dict(env or {})
        if node_path:
            existing = child_env.get("NODE_PATH")
            child_env["NODE_PATH"] = (
                f"{node_path}{os.pathsep}{existing}" if existing else node_path
            )
        cmd = ["node", "-e", source, *[str(a) for a in args]]
        return self._run(cmd, code=code, cwd=cwd, env=child_env, timeout=timeout,
                         check=check)

    def run_node_json(self, source: str, *args, **kwargs):
        """Run a JS snippet whose last statement is ``emit(<value>)``.

        The snippet is wrapped so that ``emit`` prints exactly one JSON document
        on stdout, which keeps assertions in Python while the logic stays in JS.
        """
        wrapper = (
            "const emit = (value) => process.stdout.write("
            "'\\n@@JSON@@' + JSON.stringify(value));\n" + source
        )
        result = self.run_node_source(wrapper, *args, **kwargs)
        marker = "\n@@JSON@@"
        self.assertIn(marker, result.stdout, result.detail)
        head, _, payload = result.stdout.rpartition(marker)
        return head, json.loads(payload)

    def _run(self, cmd, code=0, cwd=None, env=None, input=None, timeout=180,
             check=True):
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            env={**os.environ, **(env or {})},
            input=input,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        result = Completed(proc)
        if check and code is not None:
            self.assertEqual(proc.returncode, code, result.detail)
        return result

    def run_shell(self, script: Path, *args, code=0, cwd=None, env=None,
                  input=None, timeout=180, check=True):
        cmd = ["bash", str(script), *[str(a) for a in args]]
        return self._run(cmd, code=code, cwd=cwd, env=env, input=input,
                         timeout=timeout, check=check)

    def import_snippet(self, snippet: str, *args, path_entries=(), code=0,
                       cwd=None, env=None, timeout=180):
        """Run ``snippet`` in a child interpreter with extra PYTHONPATH entries."""
        python_path = [str(p) for p in path_entries]
        existing = os.environ.get("PYTHONPATH")
        if existing:
            python_path.append(existing)
        child_env = dict(env or {})
        if python_path:
            child_env["PYTHONPATH"] = os.pathsep.join(python_path)
        cmd = [sys.executable, "-c", snippet, *[str(a) for a in args]]
        return self._run(cmd, code=code, cwd=cwd, env=child_env, timeout=timeout)

    # -- workspace helpers ---------------------------------------------
    def write(self, name: str, text: str) -> Path:
        path = self.work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_bytes(self, name: str, data: bytes) -> Path:
        path = self.work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def write_json(self, name: str, payload) -> Path:
        return self.write(name, json.dumps(payload, indent=2))

    def read_json(self, path: Path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    # -- assertions ------------------------------------------------------
    def assertAllIn(self, needles, haystack: str, msg: str = ""):
        missing = [n for n in needles if n not in haystack]
        self.assertFalse(missing, f"{msg}expected to find {missing} in:\n{haystack}")

    def assertAllInText(self, needles, haystack: str, msg: str = ""):
        """``assertAllIn`` with whitespace collapsed on both sides.

        ``--help`` output is wrapped to the terminal width, so assertions on
        prose must compare normalised text.
        """
        flat = " ".join(haystack.split())
        missing = [n for n in needles if " ".join(n.split()) not in flat]
        self.assertFalse(missing, f"{msg}expected to find {missing} in:\n{haystack}")


def png_bytes(width: int = 8, height: int = 8, color=(200, 30, 30)) -> bytes:
    """A real PNG payload without needing Pillow at import time."""
    from PIL import Image
    import io

    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, format="PNG")
    return buf.getvalue()
