#!/usr/bin/env python3
"""Fetch the upstream Tern Plugin SDK documentation (mdBook) into this repository.

Source: https://docs.stencil.so/tern/
Every page of the mdBook has a plain-text twin at the same path with a `.md`
suffix (e.g. `concepts/architecture.html` -> `concepts/architecture.md`), which
this script downloads verbatim, keeping the upstream directory structure.

Outputs:
  docs/<path>.md      English source pages (VitePress root locale)
  site-map.json       machine readable table of contents (sections + titles)

The script never touches `docs/zh/` (translated pages) or `docs/.vitepress/`
(site configuration), so it is safe to re-run to sync upstream changes.

Usage:
  python3 scripts/fetch_docs.py [--base URL] [--out DIR] [--delay SECONDS]

Exit codes:
  0  all pages fetched
  1  one or more pages failed (partial output is still written)
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = "https://docs.stencil.so/tern/"
USER_AGENT = "tern-docs-fetch/1.0 (+https://github.com/hu-qi/tern-docs)"


def fetch(url: str, attempts: int = 3, timeout: int = 45) -> str:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError) as error:  # pragma: no cover - network
            last_error = error
            if attempt < attempts:
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def parse_toc(toc_html: str) -> list[dict]:
    """Turn the mdBook `toc.html` into an ordered list of items.

    Each item is either a section title (`part-title`) or a page reference with
    the upstream title used for the sidebar.
    """
    items: list[dict] = []
    pattern = re.compile(
        r'<li class="part-title">(?P<part>.*?)</li>'
        r'|<a href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.S,
    )
    for match in pattern.finditer(toc_html):
        if match.group("part") is not None:
            items.append({"kind": "section", "title": clean(match.group("part"))})
            continue
        href = match.group("href")
        if not href.endswith(".html") or href.startswith("http"):
            continue
        items.append(
            {
                "kind": "page",
                "path": href[: -len(".html")] + ".md",
                "title": clean(match.group("title")),
            }
        )
    return items


def clean(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def build_site_map(items: list[dict]) -> dict:
    sections: list[dict] = [{"title": "Overview", "pages": []}]
    for item in items:
        if item["kind"] == "section":
            sections.append({"title": item["title"], "pages": []})
        else:
            sections[-1]["pages"].append({"path": item["path"], "title": item["title"]})
    sections = [section for section in sections if section["pages"]]
    pages = [page for section in sections for page in section["pages"]]
    return {"source": DEFAULT_BASE, "sections": sections, "pages": pages}


ASSET_ATTR = re.compile(r'(?:src|href)="([^"]+)"')
SRCSET_ATTR = re.compile(r'srcset="([^"]+)"')


def safe_join(root: str, relative: str) -> str | None:
    """Join `relative` onto `root`, rejecting absolute paths and `..` escapes.

    Returns the real (symlink-resolved) destination path, or ``None`` when the
    result would fall outside `root`. Used so a compromised upstream table of
    contents or page cannot write anywhere else on disk.
    """
    if not relative or os.path.isabs(relative):
        return None
    root_real = os.path.realpath(root)
    target = os.path.realpath(os.path.join(root_real, relative))
    if target != root_real and not target.startswith(root_real + os.sep):
        return None
    return target


def collect_assets(text: str, page_path: str) -> list[str]:
    """Relative image/asset paths referenced by a page, in page-relative form."""
    targets: list[str] = []
    for match in ASSET_ATTR.finditer(text):
        targets.append(match.group(1))
    for match in SRCSET_ATTR.finditer(text):
        for candidate in match.group(1).split(","):
            targets.append(candidate.strip().split(" ")[0])
    page_dir = os.path.dirname(page_path)
    assets: list[str] = []
    for target in targets:
        if not target or target.startswith(("http://", "https://", "data:", "#", "mailto:")):
            continue
        if target.endswith(".md") or target.endswith(".html"):
            continue
        if " " in target:
            continue
        if os.path.isabs(target):
            continue
        relative = os.path.normpath(os.path.join(page_dir, target))
        if relative == ".." or relative.startswith(".." + os.sep) or os.path.isabs(relative):
            continue
        if relative not in assets:
            assets.append(relative)
    return assets


def fetch_binary(url: str, attempts: int = 3, timeout: int = 60) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as error:  # pragma: no cover - network
            last_error = error
            if attempt < attempts:
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--out", default="docs")
    parser.add_argument("--delay", type=float, default=0.2, help="pause between requests (seconds)")
    parser.add_argument("--map", default="site-map.json")
    args = parser.parse_args()

    base = args.base if args.base.endswith("/") else args.base + "/"
    os.makedirs(args.out, exist_ok=True)

    toc_html = fetch(base + "toc.html")
    items = parse_toc(toc_html)
    site_map = build_site_map(items)
    pages = site_map["pages"]
    if not pages:
        print("error: no pages found in upstream table of contents", file=sys.stderr)
        return 1

    unsafe_pages = [page["path"] for page in pages if safe_join(args.out, page["path"]) is None]
    if unsafe_pages:
        print("error: upstream table of contents escapes the output directory:", file=sys.stderr)
        for path in unsafe_pages[:20]:
            print(f"  - {path}", file=sys.stderr)
        return 1

    failures: list[str] = []
    assets: list[str] = []
    for page in pages:
        url = base + page["path"]
        destination = safe_join(args.out, page["path"])
        try:
            text = fetch(url)
        except Exception as error:
            print(f"FAIL {page['path']}: {error}", file=sys.stderr)
            failures.append(page["path"])
            continue
        os.makedirs(os.path.dirname(destination) or args.out, exist_ok=True)
        with open(destination, "w", encoding="utf-8") as handle:
            handle.write(text)
        assets.extend(collect_assets(text, page["path"]))
        print(f"ok   {page['path']} ({len(text.encode('utf-8'))} bytes)")
        time.sleep(args.delay)

    asset_failures: list[str] = []
    for relative in sorted(set(assets)):
        if "\u2026" in relative:  # placeholder path from a truncated code sample
            continue
        destination = safe_join(args.out, relative)
        if destination is None:
            print(f"SKIP {relative}: path escapes the output directory", file=sys.stderr)
            asset_failures.append(relative)
            continue
        url = base + urllib.parse.quote(relative.replace(os.sep, "/"))
        try:
            payload = fetch_binary(url)
        except Exception as error:
            print(f"FAIL {relative}: {error}", file=sys.stderr)
            asset_failures.append(relative)
            continue
        os.makedirs(os.path.dirname(destination) or args.out, exist_ok=True)
        with open(destination, "wb") as handle:
            handle.write(payload)
        print(f"ok   {relative} ({len(payload)} bytes)")
        time.sleep(args.delay)

    with open(args.map, "w", encoding="utf-8") as handle:
        json.dump(site_map, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"\n{len(pages) - len(failures)}/{len(pages)} pages written to {args.out}/")
    print(f"{len(set(assets)) - len(asset_failures)}/{len(set(assets))} assets written to {args.out}/")
    if failures or asset_failures:
        for item in failures + asset_failures:
            print(f"failed: {item}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())