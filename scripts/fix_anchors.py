#!/usr/bin/env python3
"""Keep heading anchors stable across the English and Chinese pages.

VitePress derives a heading id from the heading text, which differs from the
mdBook ids the upstream pages link to (`ternon` vs `tern-on`), and Chinese
headings would produce Chinese ids that no existing link points at.

This script fixes both directions:

1. when a link points at an anchor that the heading does not produce, the
   English heading gets an explicit `{#anchor}` id;
2. every Chinese heading gets the *same* explicit id as the English heading in
   the same position, so `page.md#anchor` links work in both locales.

It is idempotent: existing `{#id}` suffixes are refreshed, never duplicated.

Usage: python3 scripts/fix_anchors.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

R_CONTROL = re.compile(r"[\u0000-\u001f]")
R_SPECIAL = re.compile(r"[\s~`!@#$%^&*()\-_+=\[\]{}|\\;:\"'\u201c\u201d\u2018\u2019<>,.?/]+")
R_COMBINING = re.compile(r"[\u0300-\u036F]")
ANCHOR_SUFFIX = re.compile(r"\s*\{#[^}]+\}\s*$")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
LINK = re.compile(r"\]\(([^)\s]+)\)")


def slugify(text: str) -> str:
    """VitePress heading id (mirrors @mdit-vue/shared slugify)."""
    text = unicodedata.normalize("NFKD", text)
    text = R_COMBINING.sub("", text)
    text = R_CONTROL.sub("", text)
    text = R_SPECIAL.sub("-", text)
    text = re.sub(r"-{2,}", "-", text)
    text = text.strip("-")
    text = re.sub(r"^(\d)", r"_\1", text)
    return text.lower()


def compact(text: str) -> str:
    """mdBook-style id: alphanumerics only, lowercased."""
    return re.sub(r"[^a-z0-9_]+", "", text.lower())


def unique(ids: list[str]) -> list[str]:
    """Make ids unique per page: repeated titles get -1, -2 suffixes."""
    seen: dict[str, int] = {}
    result: list[str] = []
    for anchor in ids:
        if anchor not in seen:
            seen[anchor] = 0
            result.append(anchor)
        else:
            seen[anchor] += 1
            result.append(f"{anchor}-{seen[anchor]}")
    return result


def scan(path: str) -> list[dict]:
    """Heading lines of a file, outside fenced code blocks."""
    lines = open(path, encoding="utf-8").read().split("\n")
    headings: list[dict] = []
    fence = False
    for index, line in enumerate(lines):
        if line.startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        match = HEADING.match(line)
        if match:
            explicit = re.search(r"\{#([^}]+)\}\s*$", match.group(2))
            title = ANCHOR_SUFFIX.sub("", match.group(2)).strip()
            headings.append(
                {
                    "line": index,
                    "level": len(match.group(1)),
                    "title": title,
                    "explicit": explicit.group(1) if explicit else None,
                }
            )
    return headings


def internal_anchor_refs(page: str, text: str, known: set[str]) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for link in LINK.findall(text):
        if link.startswith("http"):
            continue
        if link.startswith("#"):
            target, anchor = page, link[1:]
        else:
            path, _, anchor = link.partition("#")
            if not anchor:
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(page), path))
        if anchor and target in known:
            refs.append((target, unquote(anchor)))
    return refs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    site_map = json.load(open(os.path.join(ROOT, "site-map.json"), encoding="utf-8"))
    pages = [page["path"] for page in site_map["pages"]]
    known = set(pages)

    en_headings = {page: scan(os.path.join(ROOT, "docs", page)) for page in pages}
    refs: list[tuple[str, str]] = []
    for page in pages:
        text = open(os.path.join(ROOT, "docs", page), encoding="utf-8").read()
        refs.extend(internal_anchor_refs(page, text, known))

    # 1. explicit ids on English headings whose generated id does not match a link
    injected: dict[tuple[str, int], str] = {}
    unresolved: list[str] = []
    for target, anchor in refs:
        headings = en_headings[target]
        current = [h["explicit"] or slugify(h["title"]) for h in headings]
        if anchor in current:
            continue
        match = next(
            (
                index
                for index, heading in enumerate(headings)
                if not heading["explicit"] and compact(heading["title"]) == compact(anchor)
            ),
            None,
        )
        if match is None:
            unresolved.append(f"{target}#{anchor}")
            continue
        injected[(target, match)] = anchor

    updated_files = 0
    for page in pages:
        path = os.path.join(ROOT, "docs", page)
        lines = open(path, encoding="utf-8").read().split("\n")
        changed = False
        for (target, index), anchor in injected.items():
            if target != page:
                continue
            heading = en_headings[page][index]
            line = lines[heading["line"]]
            if not ANCHOR_SUFFIX.search(line):
                lines[heading["line"]] = f"{line.rstrip()} {{#{anchor}}}"
                changed = True
                heading["explicit"] = anchor
        if changed:
            updated_files += 1
            print(f"en {page}: explicit anchor(s) added")
            if not args.dry_run:
                open(path, "w", encoding="utf-8").write("\n".join(lines))

    # 2. mirror the English ids onto the Chinese headings
    zh_updated = 0
    for page in pages:
        en_path = os.path.join(ROOT, "docs", page)
        zh_path = os.path.join(ROOT, "docs", "zh", page)
        if not os.path.exists(zh_path):
            continue
        en = scan(en_path)
        zh = scan(zh_path)
        if [h["level"] for h in en] != [h["level"] for h in zh]:
            print(f"skip {page}: heading structure differs between locales")
            continue
        ids = unique([h["explicit"] or slugify(h["title"]) for h in en])
        zh_lines = open(zh_path, encoding="utf-8").read().split("\n")
        changed = False
        for heading, anchor in zip(zh, ids):
            line = zh_lines[heading["line"]]
            title = ANCHOR_SUFFIX.sub("", line).rstrip()
            new_line = f"{title} {{#{anchor}}}"
            if new_line != line:
                zh_lines[heading["line"]] = new_line
                changed = True
        if changed:
            zh_updated += 1
            if not args.dry_run:
                open(zh_path, "w", encoding="utf-8").write("\n".join(zh_lines))

    if unresolved:
        print(f"{len(unresolved)} anchor reference(s) have no matching heading:")
        for item in unresolved[:15]:
            print(f"  - {item}")

    print(f"English files updated: {updated_files}, Chinese files updated: {zh_updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())