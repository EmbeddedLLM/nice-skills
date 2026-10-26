# Local footage workflow

Use this route when the user supplies an existing presenter recording. No remote service is called. Dependencies are Python 3, Bash, FFmpeg/ffprobe, jq, and the standard POSIX commands listed by the finalizer. FFmpeg needs libx264, AAC encoding, loudnorm, and image/tile filters. Initial dependency installation is separate from production and follows the host environment's permissions.

## Inspect and edit

Keep the supplied recording unchanged. Probe its streams and duration, then view/listen to the relevant ranges. A matching transcript helps choose cuts; locally transcribed or estimated word timings still need review. Preserve source audio for ordinary edits. When the user supplies replacement narration, explicitly select that track and mute the replaced source audio to avoid doubled speech.

Create a new project directory with a brief, source/permission notes, a timeline listing source offsets, editable composition, and captions. Copy only the media the project needs. The optional generated-presenter `job.json` schema and its provider states do not apply to this route.

From the project directory, a simple trim with both original streams can use:

```sh
ffprobe -v error -show_streams -show_format -of json input.mp4
ffmpeg -nostdin -n -i input.mp4 -ss 2 -t 12 \
  -map 0:v:0 -map 0:a:0 -c:v libx264 -pix_fmt yuv420p -c:a aac \
  -movflags +faststart edited.mp4
```

The example selects seconds 2–14; choose boundaries from the actual recording and keep the last word intact. Re-encoding supports precise cuts; check the resulting sync rather than assuming keyframe-based stream copying is exact. Missing audio is an error for this example. Use an installed editor or explicit FFmpeg filters for multiple cuts, overlays, captions, and layout; preserve an editable project or repeatable command record.

## Produce delivery files

Run from the skill directory, or use an absolute path to the bundled script:

```sh
bash scripts/finalize_delivery.sh /absolute/project/edited.mp4 \
  /absolute/project/delivery introduction
```

Outputs are `introduction-master.mp4`, `introduction-share.mp4`, `introduction-contact-sheet.png`, and `introduction-delivery-report.json`. The default integrated loudness target is −16 LUFS; `PROGRAM_LUFS` can set another target between −40 and −5 when the destination requires it. The helper measures and verifies both encoded files within 0.5 LU and limits measured true peak to −1 dBTP.

The finalizer refuses existing named outputs and silent or missing audio. It builds and checks temporary files before publishing, creates destination files exclusively, and writes the completion report last. If publication itself fails, some completed files may remain without a completion report; existing destinations are never replaced. On failure, inspect the diagnostic and use a new destination for retries. It preserves the source recording. Do not treat its `status: verified` as a human-review result: it describes the technical delivery checks only. Review intentional still shots when black/freeze events are reported, and listen to the final speech.

The local route does not require the optional generation job's image-review, remote-upload, or cloning flags. Respect the user's existing authority to edit and distribute their material, and ask about uncertain usage rights only when relevant to the actual task.
