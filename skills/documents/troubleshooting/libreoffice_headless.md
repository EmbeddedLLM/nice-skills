# Troubleshooting: headless LibreOffice

## The usual failure

`soffice --headless` hangs, times out, or exits with a conversion error inside a container. Almost always the cause is the user profile: LibreOffice wants to create and lock a profile directory and to write configuration and cache files, and it does that under `HOME`. In a sandbox `HOME` is often read-only or shared with a previous run that left a stale lock behind.

## Fix one: use the packaged renderer

`render_docx.py` already deals with all of it. Each invocation gets its own profile directory, `HOME` and the XDG directories are pointed at that profile so they are writable, and the converter's stdout/stderr are captured so a failure can be read afterwards.

```bash
python render_docx.py work/draft.docx --output_dir work/pages
# when the conversion itself is the mystery:
python render_docx.py work/draft.docx --output_dir work/pages --verbose
```

## Fix two: profile and HOME by hand

If you need to call `soffice` yourself, give it a private profile and a writable home:

```bash
SRC=work/draft.docx
OUT=work/pages
PROFILE=work/.lo-profile_$(basename "$SRC" .docx)_$$
mkdir -p "$OUT" "$PROFILE"

HOME="$PROFILE" soffice --headless \
  -env:UserInstallation=file://"$PROFILE" \
  --convert-to pdf --outdir "$OUT" "$SRC"
```

`$$` (or a uuid) keeps concurrent runs from sharing one profile, which is the other common way to get a hang.

## Noise on stderr is not a failure

Successful conversions regularly print alarming lines — `error : Unknown IO error` is the classic one. Judge the run by its effects instead:

- the process exited;
- the expected output files exist and their page count and content are right.

Only escalate when those are wrong.

## Still misbehaving

- Make the profile path unique per process; never reuse one across runs.
- Remove leftover profile directories between attempts.
- Work under `work` rather than `/tmp` if the sandbox looks like it is blocking writes in one of them.
