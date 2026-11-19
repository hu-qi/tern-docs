#!/usr/bin/env python3
"""Compare this mirror with the upstream mdBook and record the result.

The upstream table of contents lives in a hashed `toc-<hash>.js` file, so the
script discovers the current name from the upstream home page instead of
hard-coding it. It then compares the upstream page list with `site-map.json`
and fetches every upstream `.md` source to compare it with `docs/<path>`.

The `{#slug}` heading anchors appended by `scripts/fix_anchors.py` are a local
addition; they are normalised away before comparing content so that
anchor-only differences are reported separately from real content drift.

Results are written to a fenced block in `SITE_MAP.md` (between the
`upstream-diff` markers) and can be regenerated idempotently.

Usage: python3 scripts/diff_upstream.py [--source URL] [--no-write]
Exit code 0 = no missing / extra / content-difference pages, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
SITE_MAP_JSON = ROOT / "site-map.json"
SITE_MAP_MD = ROOT / "SITE_MAP.md"
DOCS = ROOT / "docs"
DEFAULT_SOURCE = "https://docs.stencil.so/tern/"
USER_AGENT = "tern-docs-upstream-check/1.0 (+https://github.com/hu-qi/tern-docs)"
SECTION_START = "<!-- upstream-diff:start -->"
SECTION_END = "<!-- upstream-diff:end -->"
ANCHOR_SUFFIX = re.compile(r"[ \t]*\{#[^}\n]+\}")
SCRIPT_SRC = re.compile(r"<script[^>]*\bsrc=\"([^\"]+)\"", re.I)
TOC_HREF = re.compile(r"href=\"([^\"]+\.html)\"")


def find_toc_script(html: str) -> str | None:
    """Return the `toc-*.js` script path referenced by the upstream home page."""
    for src in SCRIPT_SRC.findall(html):
        name = src.rsplit("/", 1)[-1]
        if name.startswith("toc-") and name.endswith(".js"):
            return src
    return None


def parse_toc_js(js: str) -> list[str]:
    """Extract page paths (`*.md`) from the upstream sidebar TOC script."""
    pages: list[str] = []
    seen: set[str] = set()
    for href in TOC_HREF.findall(js):
        if href.startswith(("http://", "https://")):
            continue
        path = href.lstrip("./")
        if not path or path.endswith("/"):
            continue
        if path.endswith(".html"):
            path = path[: -len(".html")] + ".md"
        if path not in seen:
            seen.add(path)
            pages.append(path)
    return pages


def normalize_anchors(text: str) -> str:
    """Drop local `{#slug}` heading anchors so anchor-only diffs are ignored."""
    return ANCHOR_SUFFIX.sub("", text)


def classify(upstream_text: str, local_text: str) -> str:
    """Return `identical`, `anchor_only` or `diff` for one page."""
    if upstream_text == local_text:
        return "identical"
    if normalize_anchors(upstream_text) == normalize_anchors(local_text):
        return "anchor_only"
    return "diff"


def page_diff(upstream_paths: Iterable[str], local_paths: Iterable[str]) -> tuple[list[str], list[str]]:
    """Return (missing, extra) pages compared to the upstream list."""
    upstream = set(upstream_paths)
    local = set(local_paths)
    missing = sorted(upstream - local)
    extra = sorted(local - upstream)
    return missing, extra


def render_section(report: dict) -> str:
    """Render the markdown block written into SITE_MAP.md."""
    lines = [
        SECTION_START,
        "## 上游对齐",
        "",
        f"- 上游：<{report['source']}>（`{report['toc_script']}`）",
        f"- 上游页面：**{report['upstream_count']}**　本仓库页面：**{report['local_count']}**",
        f"- 页面差集：缺失 **{len(report['missing'])}** / 多余 **{len(report['extra'])}**",
        f"- 内容比对：逐字节一致 **{report['identical']}**，仅 `{{#slug}}` 锚点差异 "
        f"**{report['anchor_only']}**，内容差异 **{len(report['content_diff'])}**",
        "",
    ]
    for key, title in (
        ("missing", "缺失页面"),
        ("extra", "多余页面"),
        ("content_diff", "内容差异页面"),
        ("failed", "抓取失败页面"),
    ):
        items = report.get(key) or []
        if not items:
            continue
        lines.append(f"### {title}")
        lines.append("")
        lines += [f"- `{item}`" for item in items]
        lines.append("")
    lines += [
        "> 仅锚点差异来自 `scripts/fix_anchors.py` 追加的 `{#slug}`，比对前已归一化，不计为内容差异。",
        "> 由 `python3 scripts/diff_upstream.py` 生成，请勿手工编辑。",
        SECTION_END,
        "",
    ]
    return "\n".join(lines)


def upsert_section(document: str, section: str) -> str:
    """Replace the upstream-diff block, or append it when absent."""
    pattern = re.compile(
        re.escape(SECTION_START) + r".*?" + re.escape(SECTION_END) + r"\n?",
        re.S,
    )
    if pattern.search(document):
        return pattern.sub(section, document, count=1)
    stripped = document.rstrip("\n")
    return f"{stripped}\n\n{section}" if stripped else section


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def run(source: str, docs: Path = DOCS, site_map_json: Path = SITE_MAP_JSON) -> dict:
    """Fetch the upstream list and compare it with the local mirror."""
    from urllib.parse import urljoin

    source = source.rstrip("/") + "/"
    home = fetch(source).decode("utf-8", "replace")
    toc_script = find_toc_script(home)
    if not toc_script:
        raise RuntimeError("未能在上游首页解析到 toc-*.js 脚本")
    toc_url = urljoin(source, toc_script)
    upstream_paths = parse_toc_js(fetch(toc_url).decode("utf-8", "replace"))

    site_map = json.loads(site_map_json.read_text(encoding="utf-8"))
    local_paths = [page["path"] for page in site_map["pages"]]
    missing, extra = page_diff(upstream_paths, local_paths)

    identical = anchor_only = 0
    content_diff: list[str] = []
    failed: list[str] = []
    for path in upstream_paths:
        local_file = docs / path
        try:
            upstream_text = fetch(urljoin(source, path)).decode("utf-8")
        except Exception:  # noqa: BLE001 - report the page and continue
            failed.append(path)
            continue
        if not local_file.exists():
            continue
        local_text = local_file.read_text(encoding="utf-8")
        result = classify(upstream_text, local_text)
        if result == "identical":
            identical += 1
        elif result == "anchor_only":
            anchor_only += 1
        else:
            content_diff.append(path)

    return {
        "source": source,
        "toc_script": toc_script,
        "upstream_count": len(upstream_paths),
        "local_count": len(local_paths),
        "missing": missing,
        "extra": extra,
        "identical": identical,
        "anchor_only": anchor_only,
        "content_diff": sorted(content_diff),
        "failed": sorted(failed),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare the mirror with upstream.")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--docs", type=Path, default=DOCS)
    parser.add_argument("--site-map", type=Path, default=SITE_MAP_JSON)
    parser.add_argument("--document", type=Path, default=SITE_MAP_MD)
    parser.add_argument("--no-write", action="store_true", help="只打印结果，不写入 SITE_MAP.md")
    args = parser.parse_args(argv)

    try:
        report = run(args.source, args.docs, args.site_map)
    except Exception as error:  # noqa: BLE001 - surface a clear failure
        print(f"上游比对失败：{error}", file=sys.stderr)
        return 1

    print(
        f"上游 {report['upstream_count']} 页 / 本地 {report['local_count']} 页；"
        f"缺失 {len(report['missing'])} / 多余 {len(report['extra'])}；"
        f"一致 {report['identical']}，锚点差异 {report['anchor_only']}，"
        f"内容差异 {len(report['content_diff'])}，抓取失败 {len(report['failed'])}"
    )
    if not args.no_write:
        document = args.document.read_text(encoding="utf-8")
        args.document.write_text(upsert_section(document, render_section(report)), encoding="utf-8")
        print(f"已写入 {args.document.relative_to(ROOT) if args.document.is_relative_to(ROOT) else args.document}")

    ok = not (report["missing"] or report["extra"] or report["content_diff"] or report["failed"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())