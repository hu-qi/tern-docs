#!/usr/bin/env python3
"""Unit tests for the upstream comparison helpers (scripts/diff_upstream.py)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import diff_upstream  # noqa: E402


class TocDiscoveryTest(unittest.TestCase):
    HOME = (
        '<script src="elasticlunr-ef4e11c1.min.js"></script>'
        '<script src="toc-5868f7c9.js"></script>'
        '<script src="searcher-09f2665d.js"></script>'
    )

    def test_finds_hashed_toc_script(self) -> None:
        self.assertEqual(diff_upstream.find_toc_script(self.HOME), "toc-5868f7c9.js")

    def test_returns_none_without_toc_script(self) -> None:
        self.assertIsNone(diff_upstream.find_toc_script('<script src="book.js"></script>'))

    def test_parses_pages_from_sidebar_toc(self) -> None:
        js = (
            '<ol class="chapter">'
            '<li><a href="index.html">Overview</a></li>'
            '<li class="part-title">Concepts</li>'
            '<li><a href="concepts/architecture.html">Architecture</a></li>'
            '<li><a href="concepts/architecture.html">Architecture</a></li>'
            '<li><a href="https://example.com/remote.html">Remote</a></li>'
            "</ol>"
        )
        self.assertEqual(
            diff_upstream.parse_toc_js(js),
            ["index.md", "concepts/architecture.md"],
        )


class AnchorNormalizationTest(unittest.TestCase):
    def test_removes_local_anchor_suffix(self) -> None:
        text = "## Data flow {#data-flow}\n### Right-click menus: `actions.menu` {#right-click-menus-actionsmenu}\n"
        self.assertEqual(diff_upstream.normalize_anchors(text), "## Data flow\n### Right-click menus: `actions.menu`\n")

    def test_classifies_identical(self) -> None:
        self.assertEqual(diff_upstream.classify("a\n", "a\n"), "identical")

    def test_classifies_anchor_only_difference(self) -> None:
        self.assertEqual(
            diff_upstream.classify("## Data flow\n", "## Data flow {#data-flow}\n"),
            "anchor_only",
        )

    def test_classifies_real_content_difference(self) -> None:
        self.assertEqual(diff_upstream.classify("old\n", "new\n"), "diff")


class PageDiffTest(unittest.TestCase):
    def test_reports_missing_and_extra_sorted(self) -> None:
        missing, extra = diff_upstream.page_diff(
            ["index.md", "b.md", "c.md"],
            ["index.md", "a.md", "c.md"],
        )
        self.assertEqual(missing, ["b.md"])
        self.assertEqual(extra, ["a.md"])


class SectionWriteTest(unittest.TestCase):
    REPORT = {
        "source": "https://example.com/tern/",
        "toc_script": "toc-abc.js",
        "upstream_count": 85,
        "local_count": 85,
        "missing": [],
        "extra": [],
        "identical": 76,
        "anchor_only": 9,
        "content_diff": [],
        "failed": [],
    }

    def test_renders_counts_and_markers(self) -> None:
        section = diff_upstream.render_section(self.REPORT)
        self.assertIn(diff_upstream.SECTION_START, section)
        self.assertIn(diff_upstream.SECTION_END, section)
        self.assertIn("缺失 **0** / 多余 **0**", section)
        self.assertIn("内容差异 **0**", section)

    def test_appends_block_once(self) -> None:
        section = diff_upstream.render_section(self.REPORT)
        once = diff_upstream.upsert_section("# SITE_MAP\n", section)
        twice = diff_upstream.upsert_section(once, section)
        self.assertEqual(once, twice)
        self.assertEqual(once.count(diff_upstream.SECTION_START), 1)

    def test_replaces_existing_block(self) -> None:
        section = diff_upstream.render_section(self.REPORT)
        updated = dict(self.REPORT, missing=["new.md"])
        document = diff_upstream.upsert_section("# SITE_MAP\n", section)
        document = diff_upstream.upsert_section(document, diff_upstream.render_section(updated))
        self.assertEqual(document.count(diff_upstream.SECTION_START), 1)
        self.assertIn("`new.md`", document)


if __name__ == "__main__":
    unittest.main()