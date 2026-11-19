#!/usr/bin/env python3
"""Unit tests for scripts/emit_markdown.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import emit_markdown  # noqa: E402


class EmitMarkdownTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.docs = root / "docs"
        self.dist = self.docs / ".vitepress" / "dist"
        self.dist.mkdir(parents=True)

        self.write(self.docs / "index.md", "# Overview\n")
        self.write(self.docs / "concepts" / "architecture.md", "# Architecture\n\n```mermaid\nflowchart TB\n```\n")
        self.write(self.docs / "zh" / "index.md", "# 总览\n")
        self.write(self.docs / "zh" / "concepts" / "architecture.md", "# 架构 {#architecture}\n")
        self.write(self.docs / "issue-5" / "spec.md", "# private spec\n")
        self.write(self.docs / ".vitepress" / "notes.md", "# build notes\n")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    @staticmethod
    def write(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_copies_public_pages_for_both_languages(self) -> None:
        copied = emit_markdown.emit(self.docs, self.dist)
        self.assertEqual(copied, 4)
        for relative in (
            "index.md",
            "concepts/architecture.md",
            "zh/index.md",
            "zh/concepts/architecture.md",
        ):
            self.assertTrue((self.dist / relative).is_file(), relative)

    def test_output_is_byte_identical_to_source(self) -> None:
        emit_markdown.emit(self.docs, self.dist)
        source = self.docs / "concepts" / "architecture.md"
        target = self.dist / "concepts" / "architecture.md"
        self.assertEqual(target.read_bytes(), source.read_bytes())

    def test_skips_excluded_directories(self) -> None:
        emit_markdown.emit(self.docs, self.dist)
        self.assertFalse((self.dist / "issue-5" / "spec.md").exists())
        self.assertFalse((self.dist / ".vitepress" / "notes.md").exists())

    def test_missing_dist_is_reported(self) -> None:
        with self.assertRaises(FileNotFoundError):
            emit_markdown.emit(self.docs, self.docs / "does-not-exist")


class RealDocsCountTest(unittest.TestCase):
    def test_every_site_page_has_a_source_file(self) -> None:
        import json

        site_map = json.loads((ROOT / "site-map.json").read_text(encoding="utf-8"))
        expected = {page["path"] for page in site_map["pages"]}
        relatives = [relative for _, relative in emit_markdown.markdown_sources(ROOT / "docs")]
        english = {str(relative) for relative in relatives if relative.parts[0] != "zh"}
        chinese = {
            str(relative.relative_to("zh")) for relative in relatives if relative.parts[0] == "zh"
        }
        self.assertEqual(english, expected)
        self.assertEqual(chinese, expected)
        self.assertEqual(len(relatives), len(expected) * 2)


if __name__ == "__main__":
    unittest.main()