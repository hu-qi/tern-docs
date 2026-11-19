#!/usr/bin/env python3
"""Copy Markdown sources into the VitePress build output.

Upstream serves `<page>.md` next to the rendered HTML. `cleanUrls: true` keeps
the site routes unchanged, but the build only emits HTML, so this post-build
step copies every source page to the same path under `dist/`:

- `docs/<path>.md`    → `docs/.vitepress/dist/<path>.md`
- `docs/zh/<path>.md` → `docs/.vitepress/dist/zh/<path>.md`

Files excluded from the site (`docs/issue-*`, `docs/.vitepress`) are skipped so
the public build only exposes the documentation itself.

Usage: python3 scripts/emit_markdown.py [--docs DIR] [--dist DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DEFAULT_DIST = DOCS / ".vitepress" / "dist"
SKIP_PARTS = (".vitepress", "issue-1", "issue-3", "issue-5")


def markdown_sources(docs: Path = DOCS):
    """Yield (source, relative path) for every public Markdown page."""
    for path in sorted(docs.rglob("*.md")):
        relative = path.relative_to(docs)
        if relative.parts and relative.parts[0] in SKIP_PARTS:
            continue
        yield path, relative


def emit(docs: Path = DOCS, dist: Path = DEFAULT_DIST) -> int:
    """Copy every Markdown source into `dist`, returning the number of pages."""
    if not dist.is_dir():
        raise FileNotFoundError(f"构建目录不存在：{dist}，请先运行 npm run docs:build")
    copied = 0
    for source, relative in markdown_sources(docs):
        target = dist / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        copied += 1
    return copied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Copy Markdown sources into the build output.")
    parser.add_argument("--docs", type=Path, default=DOCS)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    args = parser.parse_args(argv)

    try:
        copied = emit(args.docs, args.dist)
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        return 1
    print(f"已复制 {copied} 个 Markdown 源文件到 {args.dist}")
    return 0


if __name__ == "__main__":
    sys.exit(main())