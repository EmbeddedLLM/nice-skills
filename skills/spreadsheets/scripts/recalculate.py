#!/usr/bin/env python3
"""Recalculate a plain XLSX copy with LibreOffice, or inspect existing caches.

Recalculation runs headless LibreOffice on a temporary copy, so the input is
never modified and no global macro or sandbox shim is involved.
"""

import argparse
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import zipfile
from xml.etree import ElementTree

from openpyxl import load_workbook


def inspect(path):
    """Inspect typed errors and formula caches without saving either load."""
    formulas = load_workbook(path, data_only=False, read_only=True)
    try:
        cached = load_workbook(path, data_only=True, read_only=True)
        try:
            errors, missing, locations = [], [], []
            for ws in formulas.worksheets:
                values = cached[ws.title]
                for row, cached_row in zip(ws.iter_rows(), values.iter_rows()):
                    for cell, value in zip(row, cached_row):
                        address = f"{ws.title}!{cell.coordinate}" if cell.value is not None else None
                        if cell.data_type == "f":
                            locations.append(address)
                            # An empty cached string is a legitimate blank result.
                            if value.value is None and value.data_type != "str":
                                missing.append(address)
                        if value.data_type == "e":
                            errors.append({"cell": address or f"{ws.title}!{value.coordinate}",
                                           "error": value.value})
            status = "errors_found" if errors else "unverified" if missing else "success"
            return {"status": status, "total_formulas": len(locations),
                    "total_errors": len(errors), "errors": errors[:100],
                    "errors_truncated": max(0, len(errors) - 100),
                    "missing_cache_count": len(missing), "missing_caches": missing[:100],
                    "missing_caches_truncated": max(0, len(missing) - 100)}, set(locations)
        finally:
            cached.close()
    finally:
        formulas.close()


def check_package(path):
    if path.suffix.lower() != ".xlsx":
        raise ValueError("Only self-contained .xlsx files are supported by this helper")
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            lower = name.lower()
            if lower.startswith("xl/externallinks/") or "vbaproject" in lower:
                raise ValueError("External workbook links or macros require a preservation-aware workflow")
            if lower.endswith(".rels"):
                root = ElementTree.fromstring(archive.read(name))
                for rel in root:
                    if rel.attrib.get("Type", "").endswith("/externalLink"):
                        raise ValueError("External workbook links are not supported")


def recalculate(source, output, timeout):
    if output.suffix.lower() != ".xlsx":
        raise ValueError("Output must have an .xlsx extension")
    if output.exists() or output.is_symlink() or source.resolve() == output.resolve():
        raise ValueError("Choose a new output path; the input and existing outputs are never overwritten")
    check_package(source)
    executable = shutil.which("soffice")
    if not executable:
        raise RuntimeError("LibreOffice (soffice) is required for recalculation; --check-only inspects caches")
    _, before = inspect(source)
    with tempfile.TemporaryDirectory(prefix="xlsx-recalc-") as directory:
        work = Path(directory)
        staged = work / "input.xlsx"
        shutil.copyfile(source, staged)
        converted = work / "converted"
        converted.mkdir()
        command = [executable, f"-env:UserInstallation={(work / 'profile').as_uri()}",
                   "--headless", "--norestore", "--convert-to", "xlsx:Calc MS Excel 2007 XML",
                   "--outdir", str(converted), str(staged)]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, start_new_session=(os.name == "posix"))
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            if os.name == "posix":
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                proc.kill()
            proc.communicate()
            raise RuntimeError("LibreOffice did not complete; input preserved and no output published")
        result = converted / staged.name
        if proc.returncode != 0 or not result.is_file():
            raise RuntimeError(f"LibreOffice conversion failed: {(stderr or stdout).strip()}")
        report, after = inspect(result)
        if before != after:
            raise RuntimeError("Formula locations changed during conversion; output not published")
        # Exclusive creation also closes the race between the preflight and save.
        with output.open("xb") as target, result.open("rb") as stream:
            shutil.copyfileobj(stream, target)
        report.update({"output": str(output), "recalculated": True})
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    if args.check_only and args.output:
        parser.error("--output cannot be used with --check-only")
    if not args.check_only and not args.output:
        parser.error("Recalculation requires --output with a new file path")
    try:
        if args.check_only:
            report, _ = inspect(args.input)
            report.update({"recalculated": False, "cache_freshness": "not_verified"})
        else:
            report = recalculate(args.input, args.output, args.timeout)
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "success" else 2
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc), "recalculated": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
