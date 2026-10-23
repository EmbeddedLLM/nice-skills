#!/usr/bin/env python3
"""Measure how much published skill content still overlaps a reference corpus.

Motivation: issue #6. An external audit found dozens of supporting files under
``skills/`` carried over from the original snapshot essentially verbatim,
even though every ``SKILL.md`` entry point was rewritten. Carried files that
were merely reworded or renamed slip past naive comparison tools, so this
script runs three complementary, ungated passes for every local file:

1. Byte identity -- SHA-256 of the file against every corpus file.
2. Ungated ``difflib`` ratio -- computed against every corpus file that shares
   the local file's basename. Cheap ``real_quick_ratio``/``quick_ratio`` upper
   bounds skip provably-low pairs before the quadratic comparison runs; very
   large pairs fall back to line-level ratios.
3. Word-shingle containment -- the fraction of the local file's 6-gram word
   shingles present in a single corpus file, searched across the whole corpus
   through an inverted index. This catches renamed and reworded carry-over
   that name- and line-oriented passes miss. The best candidate is then
   confirmed with a full ``difflib`` ratio.

A file is reported when it is byte-identical, or when either text metric
reaches its threshold (``--min-difflib``, ``--min-shingle``). Expected
boilerplate is excluded from all passes by default because matches there are
not actionable carry-over: generated manifests/lockfiles (``package.json``,
``package-lock.json``, ``.package-lock.json``) and license/notice files
(basenames starting with ``LICENSE`` or ``NOTICE`` -- retained third-party
notices are *supposed* to stay identical). Pass ``--include-noise`` to
report them anyway.

Usage (from the repository root):

    python3 tools/measure_similarity.py --corpus /path/to/reference-corpus
    python3 tools/measure_similarity.py --corpus /path/to/reference-corpus --by-skill
    python3 tools/measure_similarity.py --corpus /path/to/reference-corpus --corpus /path/to/other-ref
    python3 tools/measure_similarity.py --corpus /path/to/reference-corpus --fail-above 0.30
    python3 tools/measure_similarity.py --corpus /path/to/reference-corpus --json > report.json
    python3 -m unittest discover -s tools -p 'test_*.py'    # self-tests

Exit codes: 0 = report produced; 1 = ``--fail-above`` violations found;
2 = usage error (missing root, invalid threshold).
"""

from __future__ import annotations

import argparse
import collections
import difflib
import hashlib
import json
import pathlib
import re
import sys

TEXT_EXTENSIONS = {
    ".css",
    ".cjs",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".xml",
    ".xsd",
    ".yaml",
    ".yml",
}
SKIPPED_DIRECTORY_PARTS = frozenset({".git", "__pycache__", "node_modules"})
GENERATED_BASENAMES = frozenset({".package-lock.json", "package-lock.json", "package.json"})
BOILERPLATE_PREFIXES = ("LICENSE", "NOTICE")


def is_boilerplate(name: str) -> bool:
    """True for generated manifests and license/notice files.

    These are excluded from reporting by default: manifest similarity is
    coincidental, and retained license notices are expected to be identical.
    """
    return name in GENERATED_BASENAMES or name.upper().startswith(BOILERPLATE_PREFIXES)

SHINGLE_SIZE = 6
MIN_SHINGLE_COUNT = 10
LARGE_TEXT_CHARS = 300_000

FileEntry = collections.namedtuple("FileEntry", "path name digest size text shingles")

ScanResult = collections.namedtuple(
    "ScanResult",
    "entry identical difflib difflib_source shingle shingle_source",
)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def _shingles(text: str, k: int = SHINGLE_SIZE) -> frozenset[tuple[str, ...]]:
    words = _tokenize(text)
    if len(words) < k:
        return frozenset()
    return frozenset(tuple(words[i : i + k]) for i in range(len(words) - k + 1))


def collect_files(root: pathlib.Path) -> list[FileEntry]:
    """Read every regular file under ``root`` into comparable entries."""
    entries: list[FileEntry] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or SKIPPED_DIRECTORY_PARTS.intersection(path.parts):
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        text = data.decode("utf-8", "replace") if path.suffix.lower() in TEXT_EXTENSIONS else None
        entries.append(
            FileEntry(
                path=path,
                name=path.name,
                digest=hashlib.sha256(data).hexdigest(),
                size=len(data),
                text=text,
                shingles=_shingles(text) if text is not None else frozenset(),
            )
        )
    return entries


def build_shingle_index(entries: list[FileEntry]) -> dict[tuple[str, ...], list[int]]:
    index: dict[tuple[str, ...], list[int]] = collections.defaultdict(list)
    for position, entry in enumerate(entries):
        for shingle in entry.shingles:
            index[shingle].append(position)
    return index


def text_ratio(left: str, right: str, floor: float = 0.0) -> float | None:
    """Return the difflib ratio, or None when it is provably below ``floor``.

    Pairs larger than ``LARGE_TEXT_CHARS`` combined are compared line-wise to
    keep the quadratic character comparison off multi-hundred-kilobyte files.
    """
    matcher = difflib.SequenceMatcher(None, left, right)
    if floor > 0.0 and (matcher.real_quick_ratio() < floor or matcher.quick_ratio() < floor):
        return None
    if len(left) + len(right) > LARGE_TEXT_CHARS:
        return difflib.SequenceMatcher(None, left.splitlines(), right.splitlines()).ratio()
    return matcher.ratio()


def best_shingle_match(
    entry: FileEntry,
    index: dict[tuple[str, ...], list[int]],
    corpus: list[FileEntry],
    skip: frozenset[pathlib.Path],
) -> tuple[float, FileEntry | None]:
    if len(entry.shingles) < MIN_SHINGLE_COUNT:
        return 0.0, None
    hits: collections.Counter[int] = collections.Counter()
    for shingle in entry.shingles:
        for position in index.get(shingle, ()):
            hits[position] += 1
    best: tuple[float, FileEntry | None] = (0.0, None)
    for position, shared in hits.items():
        candidate = corpus[position]
        if candidate.path in skip:
            continue
        containment = shared / len(entry.shingles)
        if containment > best[0]:
            best = (containment, candidate)
    return best


def scan(
    local: list[FileEntry],
    corpus: list[FileEntry],
    *,
    min_difflib: float,
    min_shingle: float,
    candidate_shingle: float,
    include_noise: bool,
    progress: bool = False,
) -> list[ScanResult]:
    """Run all three passes over ``local``; return reported results."""
    skip = frozenset(entry.path for entry in local)
    by_digest: dict[str, FileEntry] = {}
    by_name: dict[str, list[FileEntry]] = collections.defaultdict(list)
    filtered: list[FileEntry] = []
    for entry in corpus:
        if entry.path in skip:
            continue
        filtered.append(entry)
        by_digest.setdefault(entry.digest, entry)
        by_name[entry.name].append(entry)
    index = build_shingle_index(filtered)

    results: list[ScanResult] = []
    for position, entry in enumerate(local, start=1):
        if progress and position % 250 == 0:
            print(f"  ... {position}/{len(local)} files", file=sys.stderr)
        if not include_noise and is_boilerplate(entry.name):
            continue

        identical = by_digest.get(entry.digest)

        best_ratio, best_ratio_source = 0.0, None
        best_containment, best_containment_source = 0.0, None
        if entry.text is not None:
            for candidate in by_name.get(entry.name, ()):
                if candidate.text is None:
                    continue
                ratio = text_ratio(entry.text, candidate.text, floor=min_difflib)
                if ratio is not None and ratio > best_ratio:
                    best_ratio, best_ratio_source = ratio, candidate
            containment, source = best_shingle_match(entry, index, filtered, skip)
            best_containment, best_containment_source = containment, source
            if source is not None and source.text is not None and containment >= candidate_shingle:
                ratio = text_ratio(entry.text, source.text)
                if ratio is not None and ratio > best_ratio:
                    best_ratio, best_ratio_source = ratio, source

        reported = (
            identical is not None
            or (best_ratio_source is not None and best_ratio >= min_difflib)
            or (best_containment_source is not None and best_containment >= min_shingle)
        )
        if reported:
            results.append(
                ScanResult(
                    entry=entry,
                    identical=identical.path if identical is not None else None,
                    difflib=best_ratio,
                    difflib_source=best_ratio_source.path if best_ratio_source is not None else None,
                    shingle=best_containment,
                    shingle_source=best_containment_source.path if best_containment_source is not None else None,
                )
            )
    return results


def group_of(result: ScanResult, local_root: pathlib.Path) -> str:
    relative = result.entry.path.relative_to(local_root)
    return relative.parts[0] if len(relative.parts) > 1 else relative.name


def summarize_groups(results: list[ScanResult], local: list[FileEntry], local_root: pathlib.Path) -> dict[str, dict]:
    groups: dict[str, dict] = {}
    for entry in local:
        relative = entry.path.relative_to(local_root)
        name = relative.parts[0] if len(relative.parts) > 1 else relative.name
        groups.setdefault(name, {"files": 0, "identical": 0, "similar": 0, "max_difflib": 0.0, "max_shingle": 0.0})
        groups[name]["files"] += 1
    for result in results:
        group = groups[group_of(result, local_root)]
        if result.identical is not None:
            group["identical"] += 1
        else:
            group["similar"] += 1
        group["max_difflib"] = max(group["max_difflib"], result.difflib)
        group["max_shingle"] = max(group["max_shingle"], result.shingle)
    return groups


def print_report(
    results: list[ScanResult],
    groups: dict[str, dict],
    *,
    local_root: pathlib.Path,
    corpora: list[pathlib.Path],
    local_count: int,
    corpus_count: int,
    min_difflib: float,
    min_shingle: float,
    by_skill: bool,
    quiet: bool,
    fail_above: float | None,
) -> int:
    identical = [r for r in results if r.identical is not None]
    similar = sorted((r for r in results if r.identical is None), key=lambda r: -max(r.difflib, r.shingle))

    if not quiet:
        print(f"local: {local_root}  ({local_count} files)")
        print(f"corpora: {', '.join(str(c) for c in corpora)}  ({corpus_count} files)")
    print(f"\nBYTE-IDENTICAL: {len(identical)}")
    print(f"TEXT-SIMILAR (difflib >= {min_difflib:.2f} or shingle >= {min_shingle:.2f}): {len(similar)}")
    if not quiet:
        for result in identical:
            print(f"  {result.entry.path.relative_to(local_root)}  ==  {result.identical}")
        print("  difflib  shingle  file")
        for result in similar:
            relative = result.entry.path.relative_to(local_root)
            print(f"  {result.difflib:.3f}    {result.shingle:.3f}    {relative}")
            if result.difflib_source is not None:
                print(f"      difflib <- {result.difflib_source}")
            if result.shingle_source is not None and result.shingle_source != result.difflib_source:
                print(f"      shingle <- {result.shingle_source}")
    if by_skill:
        print("\nBY GROUP:")
        header = f"  {'group':<26} {'files':>6} {'identical':>10} {'similar':>8} {'max_difflib':>12} {'max_shingle':>12}"
        print(header)
        for name in sorted(groups):
            group = groups[name]
            print(
                f"  {name:<26} {group['files']:>6} {group['identical']:>10} {group['similar']:>8} "
                f"{group['max_difflib']:>12.3f} {group['max_shingle']:>12.3f}"
            )

    if fail_above is None:
        return 0
    violations = [r for r in results if r.identical is not None or r.difflib >= fail_above or r.shingle >= fail_above]
    print(f"\nFAIL-ABOVE {fail_above:.2f}: {len(violations)} violation(s)")
    for result in violations:
        metric = "identical" if result.identical is not None else f"d={result.difflib:.3f} s={result.shingle:.3f}"
        print(f"  {result.entry.path.relative_to(local_root)}  [{metric}]")
    return 1 if violations else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="measure_similarity.py",
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--local", type=pathlib.Path, default=pathlib.Path("skills"), help="tree to audit (default: skills)")
    parser.add_argument(
        "--exclude",
        type=pathlib.Path,
        action="append",
        default=None,
        help="skip local files under this path (relative to --local or absolute), repeatable; "
        "use for intentionally immutable bundles such as the motion asset snapshot",
    )
    parser.add_argument(
        "--corpus",
        type=pathlib.Path,
        action="append",
        required=True,
        help="reference corpus root, repeatable",
    )
    parser.add_argument("--min-difflib", type=float, default=0.35, help="difflib reporting threshold (default: 0.35)")
    parser.add_argument("--min-shingle", type=float, default=0.30, help="shingle reporting threshold (default: 0.30)")
    parser.add_argument(
        "--candidate-shingle",
        type=float,
        default=0.15,
        help="shingle containment that triggers a confirming difflib pass (default: 0.15)",
    )
    parser.add_argument("--by-skill", action="store_true", help="print a per-top-level-directory summary")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit a machine-readable report on stdout")
    parser.add_argument(
        "--fail-above",
        type=float,
        default=None,
        help="exit 1 when any file is identical or reaches this ratio/containment (rewrite gate)",
    )
    parser.add_argument("--include-noise", action="store_true", help="include boilerplate (manifests, license/notice files) in all passes")
    parser.add_argument("-q", "--quiet", action="store_true", help="text mode: print only the summary counts")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    corpora = args.corpus
    for root in [args.local, *corpora]:
        if not root.is_dir():
            parser.error(f"not a directory: {root}")
    # Resolve once so local/corpus path comparisons are consistent even when
    # the same tree is reachable through different spellings.
    args.local = args.local.resolve()
    corpora = [root.resolve() for root in corpora]
    for name, value in [("--min-difflib", args.min_difflib), ("--min-shingle", args.min_shingle), ("--candidate-shingle", args.candidate_shingle), ("--fail-above", args.fail_above)]:
        if value is not None and not 0.0 <= value <= 1.0:
            parser.error(f"{name} must be between 0 and 1")

    local = collect_files(args.local)
    if args.exclude:
        excluded = tuple(
            (args.local / path).resolve() if not path.is_absolute() else path.resolve() for path in args.exclude
        )
        local = [e for e in local if not any(e.path.is_relative_to(root) for root in excluded)]
    corpus: list[FileEntry] = []
    for root in corpora:
        corpus.extend(collect_files(root))
    if not args.as_json:
        print(f"scanning {len(local)} local files against {len(corpus)} corpus files", file=sys.stderr)

    results = scan(
        local,
        corpus,
        min_difflib=args.min_difflib,
        min_shingle=args.min_shingle,
        candidate_shingle=args.candidate_shingle,
        include_noise=args.include_noise,
        progress=not args.as_json and not args.quiet,
    )
    groups = summarize_groups(results, local, args.local)

    if args.as_json:
        json.dump(
            {
                "local": str(args.local),
                "corpora": [str(c) for c in corpora],
                "thresholds": {
                    "min_difflib": args.min_difflib,
                    "min_shingle": args.min_shingle,
                    "candidate_shingle": args.candidate_shingle,
                    "include_noise": args.include_noise,
                },
                "counts": {"local_files": len(local), "corpus_files": len(corpus)},
                "identical": [
                    {"local": str(r.entry.path.relative_to(args.local)), "corpus": str(r.identical)} for r in results if r.identical is not None
                ],
                "similar": [
                    {
                        "local": str(r.entry.path.relative_to(args.local)),
                        "difflib": round(r.difflib, 4),
                        "difflib_source": str(r.difflib_source) if r.difflib_source else None,
                        "shingle": round(r.shingle, 4),
                        "shingle_source": str(r.shingle_source) if r.shingle_source else None,
                    }
                    for r in sorted((r for r in results if r.identical is None), key=lambda r: -max(r.difflib, r.shingle))
                ],
                "groups": groups,
            },
            sys.stdout,
            indent=2,
        )
        print()
        if args.fail_above is not None:
            violations = [r for r in results if r.identical is not None or r.difflib >= args.fail_above or r.shingle >= args.fail_above]
            return 1 if violations else 0
        return 0

    return print_report(
        results,
        groups,
        local_root=args.local,
        corpora=corpora,
        local_count=len(local),
        corpus_count=len(corpus),
        min_difflib=args.min_difflib,
        min_shingle=args.min_shingle,
        by_skill=args.by_skill,
        quiet=args.quiet,
        fail_above=args.fail_above,
    )


if __name__ == "__main__":
    raise SystemExit(main())
