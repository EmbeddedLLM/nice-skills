# Browser recording to compact GIF

Adapted from DeepSeek Harness's record-browser-gif; [SOURCES.md](../SOURCES.md) records the revision and [LICENSE-deepseek.txt](../LICENSE-deepseek.txt) retains the MIT notice.

Record only the authorized browser flow, using synthetic or appropriately redacted data. Keep browser viewport, zoom, crop, and cursor behavior consistent. For discrete states, use ordered equal-sized screenshots; for movement, record the actual interaction and wait for the browser context to finish writing the video before encoding.

```sh
python scripts/encode_gif.py recording.webm demo.gif --start 1 --end 5 --speed 2 --final-hold 1 --max-width 960
python scripts/encode_gif.py frames demo.gif --pattern '*.png' --durations 1,2,1 --max-bytes 500000
```

Requires Python standard library and FFmpeg/ffprobe. Video options and screenshot holds are mutually exclusive. Screenshots sort by filename; use zero-padded names. The encoder caps FPS at 30, does not upscale, uses a shared palette, and verifies decoded dimensions, duration, animation, and byte budget. GIF timing is quantized; review the last-frame hold and actual playback.

The helper writes only the requested GIF and prints JSON. Existing output needs `--force`; invalid input, encoding failure, or an exceeded size budget returns nonzero and preserves prior output. Lower dimensions/colors/FPS or simplify content when oversized. No browser capture, external upload, or credential access happens inside the encoder.
