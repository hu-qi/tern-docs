#!/usr/bin/env python3
"""Point Chinese pages at the shared figures directory.

Upstream pages reference images as `../figures/<name>.png`, which is correct for
`docs/<section>/<page>.md`. Chinese pages live one level deeper
(`docs/zh/<section>/<page>.md`), so the same relative path would look for
`docs/zh/figures/`. This script rewrites image `src`/`srcset` attributes in
`docs/zh/` so they resolve to the single copy of the figures in `docs/figures/`.

The rewrite is idempotent: running it twice changes nothing. Text, links and
code blocks are left untouched.

Usage: python3 scripts/fix_zh_assets.py [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZH = ROOT / "docs" / "zh"

ATTR = re.compile(r'(src|srcset)="([^"]+)"')


def fix_value(value: str, prefix: str) -> str:
    parts = []
    for candidate in value.split(","):
        url = candidate.strip().split(" ")[0]
        descriptor = candidate.strip()[len(url) :]
        if "figures/" in url and not url.startswith(("/", "http://", "https://", "data:")):
            url = f"{prefix}figures/{url.split('figures/', 1)[1]}"
        parts.append(f"{url}{descriptor}")
    return ", ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    changed = 0
    for file in sorted(ZH.rglob("*.md")):
        relative_dir = file.parent.relative_to(ZH)
        depth = 0 if relative_dir == Path(".") else len(relative_dir.parts)
        prefix = "../" * (depth + 1)

        text = file.read_text(encoding="utf-8")
        updated = ATTR.sub(
            lambda match: f'{match.group(1)}="{fix_value(match.group(2), prefix)}"',
            text,
        )
        if updated == text:
            continue
        changed += 1
        print(f"rewrite {file.relative_to(ROOT)}")
        if not args.dry_run:
            file.write_text(updated, encoding="utf-8")

    print(f"{changed} Chinese page(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())