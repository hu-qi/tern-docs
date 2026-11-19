#!/usr/bin/env python3
"""Check every internal link and anchor of the built site.

Runs against the VitePress output (`docs/.vitepress/dist`), so it validates what
readers actually get:

- every internal `<a href>` resolves to a built page
- every `#fragment` resolves to an element id on that page
- every `<img src>` / `srcset` target exists in the build output, so a missing
  figure or a Chinese page still pointing at `../figures/` fails the check
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
IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)
SRC_ATTR = re.compile(r"\bsrc=\"([^\"]+)\"", re.I)
SRCSET_ATTR = re.compile(r"\bsrcset=\"([^\"]+)\"", re.I)
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


def normalize_asset(src: str) -> str:
    """Return the site-relative path of an image reference (query and slash stripped)."""
    path = src.partition("#")[0].partition("?")[0]
    if path.startswith(BASE):
        path = path[len(BASE) :]
    elif path.startswith("/"):
        path = path[1:]
    return path.strip("/")


def srcset_urls(value: str) -> list[str]:
    """Split a `srcset` attribute into its candidate URLs."""
    urls = []
    for candidate in value.split(","):
        url = candidate.strip().split(" ")[0]
        if url:
            urls.append(url)
    return urls


def find_asset(dist: Path, page: Path, path: str) -> Path | None:
    """Resolve a referenced asset against the page directory and the site root."""
    if not path:
        return None
    candidates = []
    if not path.startswith("/") and page.parent != dist:
        candidates.append(page.parent / path)
    candidates.append(dist / path)
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate.is_file():
            return candidate
    return None


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


def check_dist(dist: Path) -> tuple[int, int, list[str]]:
    """Return (links checked, images checked, problems) for a build output tree."""
    files = sorted(dist.rglob("*.html"))
    ids_cache: dict[Path, set[str]] = {}
    broken: list[str] = []
    checked = 0
    checked_assets = 0

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
                if path.endswith((".css", ".js", ".svg", ".png", ".ico", ".webp", ".gif")):
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

        seen_assets: set[str] = set()
        for tag in IMG_TAG.findall(text):
            raw_urls = [html.unescape(value) for value in SRC_ATTR.findall(tag)]
            for value in SRCSET_ATTR.findall(tag):
                raw_urls.extend(html.unescape(url) for url in srcset_urls(value))
            for raw_url in raw_urls:
                if not raw_url or raw_url.startswith(SKIP_PREFIXES):
                    continue
                path = normalize_asset(raw_url)
                if not path or path in seen_assets:
                    continue
                seen_assets.add(path)
                checked_assets += 1
                if find_asset(dist, file, path) is None:
                    broken.append(f"{file.relative_to(dist)}: missing image asset for {raw_url}")

    return checked, checked_assets, broken


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", default=str(DEFAULT_DIST))
    args = parser.parse_args()

    dist = Path(args.dist).resolve()
    if not dist.exists():
        print(f"dist not found: {dist} (run npm run docs:build first)", file=sys.stderr)
        return 1

    checked, checked_assets, broken = check_dist(dist)

    if broken:
        print(
            f"link check FAILED: {len(broken)} broken link(s)/asset(s) of "
            f"{checked} links and {checked_assets} images checked"
        )
        for item in broken[:40]:
            print(f"  - {item}")
        if len(broken) > 40:
            print(f"  ... and {len(broken) - 40} more")
        return 1

    print(
        f"link check passed: {checked} internal links and anchors and "
        f"{checked_assets} image references resolve across "
        f"{len(list(dist.rglob('*.html')))} pages"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())