#!/usr/bin/env python3
"""Verify that the Simplified Chinese pages mirror the English source pages.

Checks, for every page listed in `site-map.json`:

1. existence      - `docs/zh/<path>` exists for `docs/<path>`
2. headings       - same number of headings, same level sequence, same order,
                    and headings are actually translated
3. code blocks    - fenced code blocks are byte-identical and in the same order
4. inline code    - every code span of the English page appears in the Chinese page
5. link targets   - same link count and same targets (paths are mirrored, so a link
                    that works in English must work in Chinese too)
6. volume         - the Chinese page is neither a stub nor padded far beyond the source

Pages copied verbatim by `scripts/sync_fallback.py` (marked with
`<!-- fallback: english source -->`) are exempt from 2, 4 and 6: they are
intentionally untranslated and fall back to English.

Run with `python3 scripts/check_parity.py` (also wired to `npm run docs:check`,
which the deploy workflow runs before building). Add `--page <path>` (repeatable)
to check a single page.

Exit code 0 = every page is in parity, 1 = at least one problem was found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ZH = DOCS / "zh"
FALLBACK_MARK = "<!-- fallback: english source -->"

HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.M)
FENCE = re.compile(r"^```[^\n]*\n(.*?)^```", re.M | re.S)
INLINE_CODE = re.compile(r"`([^`\n]+)`")
LINK = re.compile(r"\]\(([^)\s]+)\)")
ANCHOR_SUFFIX = re.compile(r"\s*\{#[^}]+\}\s*$")
CJK = re.compile(r"[\u3400-\u9fff]")
TECHNICAL_HEADING = re.compile(r"^`[^`]+`$")
API_HEADING = re.compile(r"^[A-Z][A-Za-z]*( [A-Z][A-Za-z]*)* (API|SDK|UI)$")


def headings(text: str) -> list[tuple[int, str]]:
    result = []
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING.match(line)
        if match:
            title = ANCHOR_SUFFIX.sub("", match.group(2)).strip()
            result.append((len(match.group(1)), title))
    return result


def code_blocks(text: str) -> list[str]:
    return [block.strip("\n") for block in FENCE.findall(text)]


def inline_codes(text: str) -> set[str]:
    """Code spans worth comparing.

    Upstream prose also uses single backticks as quotation marks, which produces
    unbalanced spans such as "` on `" or long fragments of prose; those are not
    code and are skipped so only real identifiers are compared.
    """
    without_fences = FENCE.sub("", text)
    spans = set(INLINE_CODE.findall(without_fences))
    return {
        span
        for span in spans
        if span == span.strip()
        and 0 < len(span) <= 40
        and span[0] not in ",.;:、。"
        and not CJK.search(span)
        and not any(mark in span for mark in "，。；：、（）《》“”")
    }


def looks_technical(title: str) -> bool:
    """Headings that legitimately stay in English: code spans, API names, acronyms."""
    return (
        bool(TECHNICAL_HEADING.match(title))
        or bool(API_HEADING.match(title))
        or title.startswith("@")
        or title.isupper()
    )


def links(text: str) -> list[str]:
    return LINK.findall(text)


def check_page(page: dict) -> list[str]:
    path = page["path"]
    en_file = DOCS / path
    zh_file = ZH / path
    problems: list[str] = []

    if not zh_file.exists():
        return [f"{path}: missing Chinese page (docs/zh/{path})"]

    en_text = en_file.read_text(encoding="utf-8")
    zh_text = zh_file.read_text(encoding="utf-8")
    is_fallback = zh_text.lstrip().startswith(FALLBACK_MARK)

    en_headings = headings(en_text)
    zh_headings = headings(zh_text)
    if [level for level, _ in en_headings] != [level for level, _ in zh_headings]:
        problems.append(
            f"{path}: heading structure differs "
            f"(en={len(en_headings)} headings, zh={len(zh_headings)})"
        )
    elif not is_fallback:
        for index, ((_, en_title), (_, zh_title)) in enumerate(zip(en_headings, zh_headings)):
            if (
                en_title == zh_title
                and re.search(r"[A-Za-z]", en_title)
                and len(en_title) > 3
                and not looks_technical(en_title)
            ):
                problems.append(
                    f"{path}: heading #{index + 1} appears untranslated: {en_title!r}"
                )

    en_blocks = code_blocks(en_text)
    zh_blocks = code_blocks(zh_text)
    if en_blocks != zh_blocks:
        problems.append(
            f"{path}: code blocks differ (en={len(en_blocks)} blocks, zh={len(zh_blocks)} blocks)"
        )

    if not is_fallback:
        missing_code = inline_codes(en_text) - inline_codes(zh_text)
        if missing_code:
            sample = ", ".join(sorted(missing_code)[:5])
            problems.append(f"{path}: {len(missing_code)} inline code span(s) missing, e.g. {sample}")

        ratio = len(zh_text) / max(len(en_text), 1)
        if ratio < 0.40:
            problems.append(f"{path}: translation looks truncated ({ratio:.0%} of source size)")
        elif ratio > 1.60:
            problems.append(f"{path}: translation is unexpectedly padded ({ratio:.0%} of source size)")

    en_links = links(en_text)
    zh_links = links(zh_text)
    if en_links != zh_links:
        problems.append(
            f"{path}: link targets differ (en={len(en_links)} links, zh={len(zh_links)} links)"
        )

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", action="append", default=None, help="check only this path (repeatable)")
    args = parser.parse_args()

    site_map = json.loads((ROOT / "site-map.json").read_text(encoding="utf-8"))
    pages = site_map["pages"]
    known = {page["path"] for page in pages}

    if args.page:
        selected = [page for page in pages if page["path"] in set(args.page)]
        unknown = sorted(set(args.page) - {page["path"] for page in selected})
        if unknown:
            print(f"unknown page(s): {', '.join(unknown)}", file=sys.stderr)
            return 1
    else:
        selected = pages

    problems: list[str] = []
    for page in selected:
        problems.extend(check_page(page))

    if not args.page:
        extra = sorted(
            str(file.relative_to(ZH))
            for file in ZH.rglob("*.md")
            if str(file.relative_to(ZH)) not in known
        )
        if extra:
            problems.append(f"unexpected Chinese pages: {', '.join(extra[:10])}")

    if problems:
        print(f"parity check FAILED ({len(problems)} problem(s)):")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"parity check passed: {len(selected)} page(s) in sync (headings, code, links)")
    return 0


if __name__ == "__main__":
    sys.exit(main())