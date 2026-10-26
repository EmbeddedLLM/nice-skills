"""Classify slide-part XSD complaints by what PowerPoint actually refuses.

PowerPoint tolerates many schema deviations in slide parts but hard-fails on
a handful.  Matching is done on the literal text lxml puts in its error log;
an unrecognised message is treated as survivable rather than alarming.
"""

from __future__ import annotations

import re

#: Package paths this module's verdicts apply to.
SLIDE_PART_RE = re.compile(
    r"ppt/(?:slides|slideLayouts|slideMasters|notesSlides|notesMasters"
    r"|handoutMasters)/[^/]+\.xml"
)

#: (lxml message fragment, plain-language meaning) for show-stopping defects.
FATAL_SLIDE_PATTERNS: tuple[tuple[str, str], ...] = (
    (
        "}tableStyleId': This element is not expected",
        "duplicate <a:tableStyleId> inside one <a:tblPr> (only one allowed)",
    ),
    (
        "}srgbClr', attribute 'val'",
        "an srgbClr colour value that is not six hex digits",
    ),
    (
        "}txBody': Missing child element",
        "an empty <p:txBody> (it must contain at least a bodyPr, lstStyle, p)",
    ),
    (
        "}miter', attribute 'lim'",
        'a miter line join carrying lim="NaN"',
    ),
    (
        "}uLnTx': This element is not expected",
        "<a:uLnTx> appearing where the schema does not allow it",
    ),
    (
        "}overrideClrMapping': This element is not expected",
        "<p:overrideClrMapping> appearing where the schema does not allow it",
    ),
    (
        "}nvGrpSpPr': Missing child element",
        "an empty <p:nvGrpSpPr> (non-visual group shape properties missing)",
    ),
)


def is_schema_verdict(message: str) -> bool:
    """True when *message* is an XSD verdict, not an I/O or parse failure."""
    return message.startswith("Element ")


def fatal_slide_errors(messages) -> list[str]:
    """Annotated, sorted subset of *messages* PowerPoint would refuse."""
    verdicts = []
    for message in sorted(set(messages)):
        for fragment, meaning in FATAL_SLIDE_PATTERNS:
            if fragment in message:
                verdicts.append(f"{meaning}: {message}")
                break
    return verdicts
