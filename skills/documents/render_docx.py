#!/usr/bin/env python3
"""Render a DOCX (or DOC-compatible file) to one PNG per page.

The route is deliberately indirect: headless LibreOffice converts the document
to PDF, then Poppler rasterizes that PDF. Pagination is therefore decided once,
by the engine that produces the pages a reader will see, and the images are
stable enough to diff between runs.

What this adds over a bare `soffice --convert-to`:

* **A private, writable LibreOffice profile per run.** Containers often have a
  read-only or shared `HOME`; LibreOffice then hangs or aborts trying to lock a
  profile. Each invocation gets its own profile directory, with `HOME` and the
  XDG directories pointed inside it.
* **DPI derived from the document.** Page geometry comes from the OOXML section
  properties (twips) when available and from the intermediate PDF otherwise, so
  pages fit inside `--width` × `--height` without guesswork.
* **Conversion fallbacks.** A direct DOC(X) → PDF attempt, then any PDF the
  converter actually emitted, then DOC(X) → ODT → PDF. Success is judged by the
  output file, because LibreOffice prints alarming stderr on good conversions.

Images are named `page-<N>.png` from 1. The intermediate PDF is deleted unless
`--emit_pdf` is passed, so it cannot be confused with a deliverable.

    python render_docx.py work/report.docx --output_dir work/pages
    python render_docx.py work/report.docx --output_dir work/pages --verbose
"""

import argparse
import glob
import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from os import makedirs, replace
from os.path import abspath, basename, exists, expanduser, join, splitext
from typing import NamedTuple, Sequence, cast
from zipfile import ZipFile

from pdf2image import convert_from_path, pdfinfo_from_path

TWIPS_PER_INCH: int = 1440
POINTS_PER_INCH: float = 72.0
WORD_CONTAINERS = (".docx", ".docm", ".dotx", ".dotm")
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
SECTION_NAMESPACES = {"w": W_NS}

SOFFICE_COMMAND = "soffice"
PROFILE_PREFIX = "soffice_profile_"
CONVERT_PREFIX = "soffice_convert_"
RASTER_THREADS = 8
PAGE_SIZE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*pts")
MIXED_SECTIONS_NOTE = (
    "[render_docx] NOTE: multiple section page sizes/orientations detected; "
    "DPI is computed from the first section only. Consider --dpi to override."
)
LIBREOFFICE_MODE_FLAGS = ("--invisible", "--headless", "--norestore")


# ------------------------------------------------------------------------ DPI


def fitted_dpi(width_inches: float, height_inches: float,
               max_width_px: int, max_height_px: int) -> int:
    """Largest isotropic DPI that keeps the page inside the pixel budget."""
    return round(min(max_width_px / width_inches, max_height_px / height_inches))


def page_size_attribute(element, local: str) -> str | None:
    return element.get(f"{{{W_NS}}}{local}") or element.get(local)


def warn_about_mixed_sections(root) -> None:
    """More than one page geometry means the first section's DPI is a compromise."""
    try:
        geometries = set()
        for section in root.findall(".//w:sectPr", SECTION_NAMESPACES):
            size = section.find("w:pgSz", SECTION_NAMESPACES)
            if size is None:
                continue
            width = page_size_attribute(size, "w")
            height = page_size_attribute(size, "h")
            if width and height:
                geometries.add((width, height))
        if len(geometries) > 1:
            print(MIXED_SECTIONS_NOTE)
    except Exception:
        pass


def dpi_from_ooxml_page_size(input_path: str, max_width_px: int, max_height_px: int) -> int:
    """DPI derived from `w:pgSz`, which stores page dimensions in twips."""
    with ZipFile(input_path, "r") as archive:
        root = ET.fromstring(archive.read("word/document.xml"))

    section = root.find(".//w:sectPr", SECTION_NAMESPACES)
    if section is None:
        raise RuntimeError("Section properties not found in document.xml")
    page_size = section.find("w:pgSz", SECTION_NAMESPACES)
    if page_size is None:
        raise RuntimeError("Page size not found in section properties")

    width_twips = page_size_attribute(page_size, "w")
    height_twips = page_size_attribute(page_size, "h")
    if not width_twips or not height_twips:
        raise RuntimeError("Page size attributes missing in pgSz")

    width_inches = int(width_twips) / TWIPS_PER_INCH
    height_inches = int(height_twips) / TWIPS_PER_INCH
    if width_inches <= 0 or height_inches <= 0:
        raise RuntimeError("Invalid page size values in document.xml")

    warn_about_mixed_sections(root)
    return fitted_dpi(width_inches, height_inches, max_width_px, max_height_px)


# --------------------------------------------------------------- conversion


class Conversion(NamedTuple):
    """Result of a LibreOffice run: the PDF it produced (if any) plus logs."""

    pdf_path: str
    log: str


def libreoffice_environment(profile_dir: str) -> dict:
    """Environment giving LibreOffice a writable home of its own.

    Configuration and cache writes under a default, non-writable `HOME` or XDG
    directory are the usual cause of a headless conversion that never returns.
    """
    env = os.environ.copy()
    env["HOME"] = profile_dir
    env.setdefault("XDG_CONFIG_HOME", join(profile_dir, "xdg_config"))
    env.setdefault("XDG_CACHE_HOME", join(profile_dir, "xdg_cache"))
    makedirs(env["XDG_CONFIG_HOME"], exist_ok=True)
    makedirs(env["XDG_CACHE_HOME"], exist_ok=True)
    return env


def run_captured(command: list[str], env: dict, verbose: bool) -> subprocess.CompletedProcess:
    """Run a converter command, capturing output so failures are diagnosable."""
    process = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    if verbose:
        print("[render_docx] $ " + " ".join(command))
        if process.stdout:
            print(process.stdout)
        if process.stderr:
            print(process.stderr)

    return process


def has_content(path: str) -> bool:
    try:
        return exists(path) and os.path.getsize(path) > 0
    except OSError:
        return exists(path)


class PdfConverter:
    """Drives one LibreOffice profile through the conversion fallbacks."""

    def __init__(self, profile_dir: str, verbose: bool) -> None:
        self.environment = libreoffice_environment(profile_dir)
        self.profile_argument = "-env:UserInstallation=file://" + profile_dir
        self.verbose = verbose
        self.log_lines: list[str] = []

    def _convert(self, label: str, target: str, out_dir: str, source: str) -> None:
        command = [
            SOFFICE_COMMAND,
            self.profile_argument,
            *LIBREOFFICE_MODE_FLAGS,
            "--convert-to", target,
            "--outdir", out_dir,
            source,
        ]
        process = run_captured(command, env=self.environment, verbose=self.verbose)
        self.log_lines.append(f"--- {label} ---")
        self.log_lines.append("CMD: " + " ".join(command))
        self.log_lines.append(f"EXIT: {process.returncode}")
        if process.stdout:
            self.log_lines.append("STDOUT:\n" + process.stdout.strip())
        if process.stderr:
            self.log_lines.append("STDERR:\n" + process.stderr.strip())

    @staticmethod
    def _emitted_pdf(out_dir: str, expected: str) -> str:
        """The PDF LibreOffice left behind, even if it chose another name."""
        if has_content(expected):
            return expected
        produced = glob.glob(join(out_dir, "*.pdf"))
        if not produced:
            return ""
        candidate = sorted(produced)[0]
        return candidate if has_content(candidate) else ""

    def convert(self, document: str, out_dir: str, stem: str) -> Conversion:
        """DOC(X) → PDF, falling back to DOC(X) → ODT → PDF."""
        expected_pdf = join(out_dir, f"{stem}.pdf")

        self._convert("DOCX->PDF", "pdf", out_dir, document)
        found = self._emitted_pdf(out_dir, expected_pdf)
        if found:
            return Conversion(found, "\n".join(self.log_lines))

        self._convert("DOCX->ODT", "odt", out_dir, document)
        intermediate = join(out_dir, f"{stem}.odt")
        if exists(intermediate):
            self._convert("ODT->PDF", "pdf", out_dir, intermediate)
            found = self._emitted_pdf(out_dir, expected_pdf)
            if found:
                return Conversion(found, "\n".join(self.log_lines))

        return Conversion("", "\n".join(self.log_lines))


def convert_to_pdf(document: str, profile_dir: str, out_dir: str, stem: str,
                   verbose: bool) -> tuple[str, str]:
    """Convert `document` to a PDF; returns (path or "", debug log)."""
    conversion = PdfConverter(profile_dir, verbose).convert(document, out_dir, stem)
    return conversion.pdf_path, conversion.log


def dpi_from_pdf_page_size(input_path: str, max_width_px: int, max_height_px: int,
                           verbose: bool) -> int:
    """Convert to PDF and read the page geometry out of it."""
    with tempfile.TemporaryDirectory(prefix=PROFILE_PREFIX) as profile_dir, \
            tempfile.TemporaryDirectory(prefix=CONVERT_PREFIX) as work_dir:
        stem = splitext(basename(input_path))[0]
        pdf_path, log = convert_to_pdf(input_path, profile_dir, work_dir, stem, verbose=verbose)
        if not (pdf_path and exists(pdf_path)):
            raise RuntimeError(
                "Failed to convert input to PDF for DPI computation.\n" + log
            )

        info = pdfinfo_from_path(pdf_path)
        size_text = info.get("Page size")
        if not size_text:
            for key, value in info.items():
                if isinstance(value, str) and "size" in key.lower() and "pts" in value:
                    size_text = value
                    break
        if not isinstance(size_text, str):
            raise RuntimeError("Failed to read PDF page size for DPI computation.")

        # Shapes seen in the wild: "612 x 792 pts", "612.0 x 792.0 pts (letter)".
        match = PAGE_SIZE_PATTERN.search(size_text)
        if not match:
            raise RuntimeError("Unrecognized PDF page size format.")

        width_inches = float(match.group(1)) / POINTS_PER_INCH
        height_inches = float(match.group(2)) / POINTS_PER_INCH
        if width_inches <= 0 or height_inches <= 0:
            raise RuntimeError("Invalid PDF page size values.")

        return fitted_dpi(width_inches, height_inches, max_width_px, max_height_px)


# ------------------------------------------------------------------- raster


def published_page_names(out_dir: str, raster_paths: Sequence[str]) -> list[str]:
    """Rename Poppler's `page0000-01.png` output to `page-<N>.png`, in order."""
    pages: list[tuple[int, str]] = []

    for source in raster_paths:
        number = int(splitext(basename(source))[0].split("-")[-1])
        destination = join(out_dir, f"page-{number}.png")
        replace(source, destination)
        pages.append((number, destination))

    pages.sort(key=lambda entry: entry[0])
    return [path for _, path in pages]


def publish_intermediate_pdf(pdf_path: str, out_dir: str, stem: str) -> None:
    destination = join(out_dir, f"{stem}.pdf")
    staging = destination + ".tmp"
    shutil.copy2(pdf_path, staging)
    replace(staging, destination)


def rasterize(document: str, out_dir: str, dpi: int, verbose: bool,
              emit_pdf: bool) -> Sequence[str]:
    """Render `document` into `out_dir` as `page-<N>.png`; return the paths."""
    makedirs(out_dir, exist_ok=True)
    document = abspath(document)
    stem = splitext(basename(document))[0]

    with tempfile.TemporaryDirectory(prefix=PROFILE_PREFIX) as profile_dir, \
            tempfile.TemporaryDirectory(prefix=CONVERT_PREFIX) as work_dir:
        pdf_path, log = convert_to_pdf(document, profile_dir, work_dir, stem, verbose=verbose)
        if not (pdf_path and exists(pdf_path)):
            raise RuntimeError(
                "Failed to produce PDF for rasterization (direct and ODT fallback).\n" + log
            )

        # Off by default: intermediates should not be confused with deliverables.
        if emit_pdf:
            publish_intermediate_pdf(pdf_path, out_dir, stem)

        raster_paths = cast(
            list[str],
            convert_from_path(
                pdf_path,
                dpi=dpi,
                fmt="png",
                thread_count=RASTER_THREADS,
                output_folder=out_dir,
                paths_only=True,
                output_file="page",
            ),
        )

    return published_page_names(out_dir, raster_paths)


# ---------------------------------------------------------------------- CLI


def resolve_dpi(input_path: str, args: argparse.Namespace) -> int:
    if args.dpi is not None:
        return int(args.dpi)
    try:
        if not input_path.lower().endswith(WORD_CONTAINERS):
            raise RuntimeError("Skip OOXML DPI; not a DOCX container")
        return dpi_from_ooxml_page_size(input_path, args.width, args.height)
    except Exception:
        return dpi_from_pdf_page_size(input_path, args.width, args.height, verbose=args.verbose)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render DOCX-like file to PNG images (internal DOCX -> PDF -> PNG)."
    )
    parser.add_argument("input_path", type=str,
                        help="Path to the input DOCX file (or compatible).")
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="Output directory for the rendered images. Defaults to a folder next to the "
             "input named after the input file (without extension).",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1600,
        help="Approximate maximum width in pixels after isotropic scaling (default 1600). "
             "The actual value may exceed slightly.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=2000,
        help="Approximate maximum height in pixels after isotropic scaling (default 2000). "
             "The actual value may exceed slightly.",
    )
    parser.add_argument("--dpi", type=int, default=None,
                        help="Override computed DPI. If provided, skips DOCX/PDF-based DPI "
                             "calculation.")
    parser.add_argument(
        "--emit_pdf",
        action="store_true",
        help="Also write an intermediate PDF to --output_dir as <input_stem>.pdf. "
             "Default is PNG-only to avoid confusing intermediates with deliverables.",
    )
    parser.add_argument("--verbose", action="store_true",
                        help="Print LibreOffice commands and captured stdout/stderr "
                             "(useful for debugging).")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    input_path = abspath(expanduser(args.input_path))
    out_dir = (
        abspath(expanduser(args.output_dir)) if args.output_dir else splitext(input_path)[0]
    )

    dpi = resolve_dpi(input_path, args)
    rasterize(input_path, out_dir, dpi, verbose=args.verbose, emit_pdf=args.emit_pdf)
    print("Pages rendered to " + out_dir)


if __name__ == "__main__":
    main()
