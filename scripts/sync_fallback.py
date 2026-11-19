#!/usr/bin/env python3
"""Copy English pages that have no Chinese counterpart yet into `docs/zh/`.

A missing translation should not break the Chinese site: the page falls back to
the English source, prefixed with a short notice so readers know the page is not
translated yet. Pages created here are marked with `<!-- fallback: english
source -->`, which `scripts/check_parity.py` recognises and exempts from the
translation checks (they are still checked for structure and links).

The script is idempotent: existing Chinese pages are never overwritten, so a
translation is not clobbered on the next build.

Usage: python3 scripts/sync_fallback.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ZH = DOCS / "zh"
MARK = "<!-- fallback: english source -->"
NOTICE = (
    f"{MARK}\n\n"
    "> 本页尚未翻译，以下为英文原文。\n\n"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    site_map = json.loads((ROOT / "site-map.json").read_text(encoding="utf-8"))
    created = 0
    for page in site_map["pages"]:
        source = DOCS / page["path"]
        target = ZH / page["path"]
        if target.exists():
            continue
        print(f"fallback {page['path']}")
        created += 1
        if args.dry_run:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(NOTICE + source.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"{created} page(s) fall back to English")
    return 0


if __name__ == "__main__":
    sys.exit(main())