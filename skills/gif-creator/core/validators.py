"""Inspect decoded GIF timing and caller-supplied delivery constraints."""

import argparse
import json
from pathlib import Path
from PIL import Image, ImageSequence


def inspect_gif(path, max_bytes=None, max_duration_ms=None):
    with Image.open(path) as gif:
        if gif.format != "GIF":
            raise ValueError("Expected a GIF file")
        durations = []
        for frame in ImageSequence.Iterator(gif):
            frame.load()
            durations.append(frame.info.get("duration", 0))
        report = {
            "width": gif.width,
            "height": gif.height,
            "frame_count": len(durations),
            "duration_ms": sum(durations),
            "durations_ms": durations,
            "loop": gif.info.get("loop"),
            "size_bytes": Path(path).stat().st_size,
        }
    errors = []
    if max_bytes is not None and report["size_bytes"] > max_bytes:
        errors.append("file size exceeds target")
    if max_duration_ms is not None and report["duration_ms"] > max_duration_ms:
        errors.append("duration exceeds target")
    report["errors"] = errors
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("gif")
    p.add_argument("--max-bytes", type=int)
    p.add_argument("--max-duration-ms", type=int)
    a = p.parse_args()
    report = inspect_gif(a.gif, a.max_bytes, a.max_duration_ms)
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(report["errors"]))
