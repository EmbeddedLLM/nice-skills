"""Build a local GIF with a common palette and timing-preserving deduplication.

Transparent inputs are composited onto the explicit background;
no platform-specific limits.
"""

import math
from pathlib import Path
from PIL import Image, ImageChops
from .validators import inspect_gif


class GIFBuilder:
    def __init__(self, width=480, height=480, fps=15, background="white"):
        if (
            type(width) is not int
            or type(height) is not int
            or width <= 0
            or height <= 0
        ):
            raise ValueError("Dimensions must be positive integers")
        if not math.isfinite(fps) or not 0 < fps <= 100:
            raise ValueError("GIF fps must be finite and between 0 and 100")
        self.width, self.height, self.fps, self.background = (
            width,
            height,
            fps,
            background,
        )
        self.frames = []

    def add_frame(self, frame):
        frame = frame if isinstance(frame, Image.Image) else Image.fromarray(frame)
        if frame.size != (self.width, self.height):
            raise ValueError("Every frame must match the configured dimensions")
        canvas = Image.new("RGBA", frame.size, self.background)
        canvas.alpha_composite(frame.convert("RGBA"))
        self.frames.append(canvas.convert("RGB"))

    def add_frames(self, frames):
        for frame in frames:
            self.add_frame(frame)

    def save(self, output_path, num_colors=128, remove_duplicates=True, loop=0):
        if not self.frames:
            raise ValueError("No frames to save")
        if type(num_colors) is not int or not 2 <= num_colors <= 256:
            raise ValueError("num_colors must be 2..256")
        if type(loop) is not int or loop < 0:
            raise ValueError("loop must be nonnegative")
        # Round cumulative timestamps, not each duration: 15 fps remains 2s/30 frames.
        boundaries = [
            round(i * 100 / self.fps) * 10 for i in range(len(self.frames) + 1)
        ]
        durations = [b - a for a, b in zip(boundaries, boundaries[1:])]
        samples = [
            self.frames[i]
            for i in range(0, len(self.frames), max(1, len(self.frames) // 8))
        ][:8]
        atlas = Image.new("RGB", (128, 128 * len(samples)), self.background)
        for i, frame in enumerate(samples):
            atlas.paste(frame.resize((128, 128)), (0, 128 * i))
        palette = atlas.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
        frames = []
        times = []
        for frame, duration in zip(self.frames, durations):
            quantized = frame.quantize(palette=palette, dither=Image.Dither.NONE)
            if (
                remove_duplicates
                and frames
                and ImageChops.difference(quantized, frames[-1]).getbbox() is None
            ):
                times[-1] += duration
            else:
                frames.append(quantized)
                times.append(duration)
        # Pillow may coalesce identical frames too; explicit durations preserve time.
        with Path(output_path).open("xb") as stream:
            frames[0].save(
                stream,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=times,
                loop=loop,
                optimize=False,
                disposal=1,
            )
        return inspect_gif(output_path)
