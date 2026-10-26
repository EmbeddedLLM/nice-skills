#!/usr/bin/env python3
"""Render timed local stills plus a locked narration to an MP4, without services.

Requires Python 3.10+, FFmpeg with libx264/AAC, and ffprobe. See references/local-production.md.
All inputs are read-only; an existing output is never overwritten. Failed renders
leave no output. Temporary encodes are removed on normal exit or failure.
"""

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile


def probe(path):
    return json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        text=True,
    ))


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be a finite positive number")
    return value


def render(story_path, scenes_path, output):
    story = json.loads(story_path.read_text(encoding="utf-8"))
    config = json.loads(scenes_path.read_text(encoding="utf-8"))
    if story.get("draft"):
        raise ValueError("silent story drafts cannot be delivered as narrated explainers")
    if output.exists() or output.is_symlink():
        raise ValueError("refusing to overwrite existing output")
    width, height, fps = (config.get(key, default) for key, default in
                          (("width", 1920), ("height", 1080), ("fps", 30)))
    for name, value in (("width", width), ("height", height), ("fps", fps)):
        number(value, name)
        if not isinstance(value, int):
            raise ValueError(f"{name} must be an integer")
    if width % 2 or height % 2:
        raise ValueError("width and height must be even for H.264 output")
    scenes = config.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("scenes must be a nonempty list")
    inputs, filters, duration, frames = [], [], 0.0, 0
    for index, scene in enumerate(scenes):
        length = number(scene["duration"], "scene duration")
        duration += length
        boundary = math.ceil(duration * fps - 1e-9)
        if boundary <= frames:
            raise ValueError("each scene must occupy at least one output frame")
        length = (boundary - frames) / fps
        frames = boundary
        image = (scenes_path.parent / scene["image"]).resolve(strict=True)
        if image.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".ppm"}:
            raise ValueError("scene images must be local PNG, JPEG, WebP, or PPM files")
        inputs.extend(["-loop", "1", "-framerate", str(fps), "-t", str(length), "-i", str(image)])
        filters.append(
            f"[{index}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
            f"trim=duration={length},setpts=PTS-STARTPTS[v{index}]"
        )
    expected = number(story["duration"], "story duration")
    if abs(duration - expected) > 1 / fps + 1e-6:
        raise ValueError("scene durations must cover the complete story within one frame")
    narration = (story_path.parent / story["narration"]).resolve(strict=True)
    metadata = probe(narration)
    if not any(stream.get("codec_type") == "audio" for stream in metadata["streams"]):
        raise ValueError("narration must have an audio stream")
    audio_duration = number(float(metadata["format"]["duration"]), "narration duration")
    if frames / fps + 0.001 < audio_duration:
        raise ValueError("scene timeline would truncate narration")
    filters.append("".join(f"[v{i}]" for i in range(len(scenes))) +
                   f"concat=n={len(scenes)}:v=1:a=0,format=yuv420p[video]")
    filters.append(f"[{len(scenes)}:a]apad[audio]")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".explainer-", dir=output.parent) as directory:
        temporary = Path(directory) / "render.mp4"
        subprocess.run([
            "ffmpeg", "-nostdin", "-v", "error", "-xerror", "-filter_complex_threads", "1",
            *inputs, "-i", str(narration), "-filter_complex", ";".join(filters),
            "-map", "[video]", "-map", "[audio]", "-t", str(frames / fps), "-r", str(fps),
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac",
            "-ar", "48000", "-b:a", "192k", "-map_metadata", "-1", "-movflags", "+faststart", str(temporary),
        ], check=True)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(temporary),
                        "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"], check=True)
        # Exclusive publication also protects an output created during the encode.
        os.link(temporary, output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("story", type=Path)
    parser.add_argument("scenes", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        print(render(args.story.resolve(), args.scenes.resolve(), args.output.absolute()))
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"render failed: {error}\n")


if __name__ == "__main__":
    main()
