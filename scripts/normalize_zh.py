#!/usr/bin/env python3
"""Normalise blank lines around headings and figure blocks in the Chinese pages.

Translations sometimes drop the blank line that upstream has between a block and
the next heading. In Markdown an HTML block (`<figure>…</figure>`) continues
until a blank line, so a missing line there swallows the following heading: the
page still looks right in the editor, but the heading disappears from the built
site (and so does its anchor).

This script inserts the missing blank lines. It only changes whitespace, never
text, and is idempotent.

Usage: python3 scripts/normalize_zh.py [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZH = ROOT / "docs" / "zh"
HEADING = re.compile(r"^#{1,6} ")


def normalize(text: str) -> tuple[str, int]:
    lines = text.split("\n")
    output: list[str] = []
    fence = False
    inserted = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            fence = not fence
        if not fence and output:
            previous = output[-1]
            needs_gap = False
            if HEADING.match(line) and previous.strip() and not HEADING.match(previous):
                needs_gap = True
            if previous.strip().endswith("</figure>") and stripped and not stripped.startswith("<"):
                needs_gap = True
            if stripped.startswith("<figure") and previous.strip() and not previous.strip().startswith("<"):
                needs_gap = True
            if needs_gap:
                output.append("")
                inserted += 1
        output.append(line)
    return "\n".join(output), inserted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    total = 0
    for file in sorted(ZH.rglob("*.md")):
        text = file.read_text(encoding="utf-8")
        updated, inserted = normalize(text)
        if not inserted:
            continue
        total += inserted
        print(f"{file.relative_to(ROOT)}: +{inserted} blank line(s)")
        if not args.dry_run:
            file.write_text(updated, encoding="utf-8")

    print(f"{total} blank line(s) inserted")
    return 0


if __name__ == "__main__":
    sys.exit(main())