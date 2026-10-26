#!/usr/bin/env python3
"""Report the section-level page layout of a DOCX.

"Page 3 is landscape and I did not do that" and "the header vanished" are both
section questions. A document may carry several sections, each with its own
orientation, page size, margins, header/footer linkage, first-page and
odd/even settings. This prints one compact block per section so the boundary
that caused the surprise is visible.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from docx import Document

EMU_PER_INCH = 914400


def as_inches(value) -> float:
    """Best-effort conversion of a python-docx length to inches."""
    try:
        return float(value.inches)
    except Exception:
        pass
    try:
        return float(value) / EMU_PER_INCH
    except Exception:
        return math.nan


def enum_name(value, fallback: str = "(unknown)") -> str:
    """Turn a python-docx enum member into its trailing name."""
    if value is None:
        return fallback
    return str(value).split(".")[-1]


def describe_section(index: int, section) -> None:
    header_linked = getattr(section.header, "is_linked_to_previous", None)
    footer_linked = getattr(section.footer, "is_linked_to_previous", None)
    first_page = getattr(section, "different_first_page_header_footer", None)
    odd_even = getattr(section, "odd_and_even_pages_header_footer", None)

    width = as_inches(section.page_width)
    height = as_inches(section.page_height)
    left = as_inches(section.left_margin)
    right = as_inches(section.right_margin)
    top = as_inches(section.top_margin)
    bottom = as_inches(section.bottom_margin)

    print(f"\n[Section {index}] start_type={enum_name(getattr(section, 'start_type', None))} "
          f"orientation={enum_name(section.orientation)}")
    print(f"  page_size(in): {width:.2f} x {height:.2f}")
    print(f"  margins(in): L={left:.2f} R={right:.2f} T={top:.2f} B={bottom:.2f}")
    print(f"  header_linked_to_previous={header_linked} footer_linked_to_previous={footer_linked}")
    print(f"  different_first_page={first_page} odd_even_headers={odd_even}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Audit DOCX sections: orientation, margins, header/footer linkage"
    )
    ap.add_argument("docx", type=Path)
    args = ap.parse_args()

    if not args.docx.exists():
        raise FileNotFoundError(args.docx)

    document = Document(str(args.docx))
    print(f"SECTIONS: {len(document.sections)}")
    for index, section in enumerate(document.sections, start=1):
        describe_section(index, section)

    print("\nREMINDER")
    print("- If you change orientation mid-document, Word typically creates a new section.")
    print("- If headers/footers look wrong, check 'Link to Previous' per section.")


if __name__ == "__main__":
    main()
