#!/usr/bin/env python3
"""Check every internal link and anchor of the built site.

Runs against the VitePress output (`docs/.vitepress/dist`), so it validates what
readers actually get:

- every internal `<a href>` resolves to a built page
- every `#fragment` resolves to an element id on that page
- both locales are covered, including the language switcher links between them

Usage: python3 scripts/check_links.py [--dist DIR]

Exit code 0 = all internal links resolve, 1 = broken links were found.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIST = ROOT / "docs" / ".vitepress" / "dist"
BASE = "/tern-docs/"

ANCHOR_TAG = re.compile(r"<a\b[^>]*?href=\"([^\"]+)\"", re.I)
ID = re.compile(r'id="([^"]+)"')
SKIP_PREFIXES = ("http://", "https://", "mailto:", "tel:", "javascript:", "data:")
SKIP_PATHS = ("/404.html", "404.html")


def normalize(href: str) -> tuple[str, str]:
    """Return (site-relative path, fragment) for an internal href."""
    path, _, fragment = href.partition("#")
    if path.startswith(BASE):
        path = path[len(BASE) :]
    elif path.startswith("/"):
        path = path[1:]
    return path.strip("/"), fragment


def find_page(dist: Path, page: Path, path: str) -> Path | None:
    if not path:
        return page
    candidates = []
    if not path.startswith("/") and not page.parent == dist:
        candidates.append(page.parent / path)
    candidates.append(dist / path)
    for candidate in candidates:
        candidate = candidate.resolve()
        for suffix in ("", ".html", "/index.html"):
            probe = Path(str(candidate) + suffix)
            if suffix == "" and probe.suffix in (".css", ".js", ".svg", ".png", ".ico", ".map"):
                continue
            if probe.is_file() and probe.suffix == ".html":
                return probe
    return None


def page_ids(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {html.unescape(value) for value in ID.findall(text)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", default=str(DEFAULT_DIST))
    args = parser.parse_args()

    dist = Path(args.dist).resolve()
    if not dist.exists():
        print(f"dist not found: {dist} (run npm run docs:build first)", file=sys.stderr)
        return 1

    files = sorted(dist.rglob("*.html"))
    ids_cache: dict[Path, set[str]] = {}
    broken: list[str] = []
    checked = 0

    for file in files:
        text = file.read_text(encoding="utf-8", errors="replace")
        for raw in ANCHOR_TAG.findall(text):
            href = html.unescape(raw)
            if href.startswith(SKIP_PREFIXES):
                continue
            path, fragment = normalize(href)
            if not path and not fragment:
                continue
            if "/" + path in SKIP_PATHS or path in SKIP_PATHS:
                continue
            checked += 1
            target = find_page(dist, file, path)
            if target is None:
                if path.endswith((".css", ".js", ".svg", ".png", ".ico")):
                    continue  # asset link, not a page
                broken.append(f"{file.relative_to(dist)}: missing page for {href}")
                continue
            if fragment:
                if target not in ids_cache:
                    ids_cache[target] = page_ids(target)
                if fragment not in ids_cache[target]:
                    broken.append(
                        f"{file.relative_to(dist)}: missing anchor #{fragment} in {target.relative_to(dist)}"
                    )

    if broken:
        print(f"link check FAILED: {len(broken)} broken link(s) of {checked} checked")
        for item in broken[:40]:
            print(f"  - {item}")
        if len(broken) > 40:
            print(f"  ... and {len(broken) - 40} more")
        return 1

    print(f"link check passed: {checked} internal links and anchors resolve across {len(files)} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())