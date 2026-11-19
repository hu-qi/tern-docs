#!/usr/bin/env python3
"""Regenerate SITE_MAP.md from site-map.json and the current translations.

The page list mirrors the upstream table of contents; the status column says
whether the page has a Simplified Chinese translation or still falls back to
English. Run after `docs:fetch` and after adding translations.

Usage: python3 scripts/gen_site_map.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ZH = DOCS / "zh"
FALLBACK_MARK = "<!-- fallback: english source -->"


ANCHOR_SUFFIX = re.compile(r"\s*\{#[^}]+\}\s*$")
UPSTREAM_SECTION = re.compile(
    r"<!-- upstream-diff:start -->.*?<!-- upstream-diff:end -->\n?",
    re.S,
)


def first_heading(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return ANCHOR_SUFFIX.sub("", line[2:]).strip()
    except FileNotFoundError:
        pass
    return ""


def status(page: str) -> str:
    target = ZH / page
    if not target.exists():
        return "回退英文"
    text = target.read_text(encoding="utf-8")
    return "回退英文" if text.lstrip().startswith(FALLBACK_MARK) else "已翻译"


def main() -> int:
    site_map = json.loads((ROOT / "site-map.json").read_text(encoding="utf-8"))
    sections = site_map["sections"]
    pages = site_map["pages"]

    translated = sum(1 for page in pages if status(page["path"]) == "已翻译")
    total = len(pages)

    lines = [
        "# 全站页面清单（SITE_MAP）",
        "",
        f"上游：<{site_map['source']}>　页面总数：**{total}**　已翻译：**{translated}**"
        f"（{translated / total:.0%}）",
        "",
        "| 章节 | 页面 | 英文标题 | 中文标题 | 状态 | 源路径 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for section in sections:
        for page in section["pages"]:
            path = page["path"]
            zh_title = first_heading(ZH / path) if (ZH / path).exists() else ""
            lines.append(
                f"| {section['title']} | `{path}` | {page['title']} | {zh_title or '—'} "
                f"| {status(path)} | [docs/{path}](../docs/{path}) |"
            )

    lines += [
        "",
        "## 说明",
        "",
        "- 页面路径与上游 mdBook 目录一一对应，`docs/<path>` 为英文原文，`docs/zh/<path>` 为中文译文。",
        "- `回退英文` 表示该页尚未翻译，构建时由 `npm run docs:fallback` 以英文原文补齐并加提示。",
        "- 本文件由 `python3 scripts/gen_site_map.py` 生成，请勿手工编辑。",
        "- 「上游对齐」小节由 `npm run docs:upstream` 生成，重跑 `docs:map` 时会保留。",
        "",
    ]

    previous = ""
    target = ROOT / "SITE_MAP.md"
    if target.exists():
        previous = target.read_text(encoding="utf-8")
        preserved = UPSTREAM_SECTION.search(previous)
        if preserved:
            lines += ["", preserved.group(0).rstrip("\n"), ""]

    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"SITE_MAP.md written: {total} pages, {translated} translated ({translated / total:.0%})")
    return 0


if __name__ == "__main__":
    sys.exit(main())