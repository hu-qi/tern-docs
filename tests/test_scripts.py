#!/usr/bin/env python3
"""Unit tests for the documentation tooling in scripts/.

Run with: python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_links  # noqa: E402
import check_parity  # noqa: E402
import fetch_docs  # noqa: E402
import fix_anchors  # noqa: E402
import fix_zh_assets  # noqa: E402
import gen_site_map  # noqa: E402
import normalize_zh  # noqa: E402


class SlugifyTest(unittest.TestCase):
    def test_matches_vitepress_rules(self) -> None:
        self.assertEqual(fix_anchors.slugify("Packages and Manifests"), "packages-and-manifests")
        self.assertEqual(fix_anchors.slugify("The `catalog`"), "the-catalog")
        self.assertEqual(fix_anchors.slugify("`tern.on`"), "tern-on")
        self.assertEqual(fix_anchors.slugify("Editor: text and keys"), "editor-text-and-keys")
        self.assertEqual(fix_anchors.slugify("2 modes"), "_2-modes")

    def test_compact_matches_mdbook_style_ids(self) -> None:
        self.assertEqual(fix_anchors.compact("`tern.on`"), "ternon")
        self.assertEqual(fix_anchors.compact("`test_summary`"), "test_summary")


class SiteMapTest(unittest.TestCase):
    TOC = (
        '<ol class="chapter">'
        '<li class="chapter-item expanded "><a href="index.html" target="_parent">Overview</a></li>'
        '<li class="part-title">Concepts</li>'
        '<li class="chapter-item expanded "><a href="concepts/architecture.html">Architecture</a></li>'
        '<li class="part-title">Guides</li>'
        '<li class="chapter-item expanded "><a href="guides/io.html">I/O</a></li>'
        "</ol>"
    )

    def test_parse_toc_and_sections(self) -> None:
        items = fetch_docs.parse_toc(self.TOC)
        site_map = fetch_docs.build_site_map(items)
        self.assertEqual([page["path"] for page in site_map["pages"]], [
            "index.md",
            "concepts/architecture.md",
            "guides/io.md",
        ])
        self.assertEqual([section["title"] for section in site_map["sections"]], [
            "Overview",
            "Concepts",
            "Guides",
        ])
        self.assertEqual(len(site_map["sections"][1]["pages"]), 1)

    def test_collect_assets_is_relative_and_deduplicated(self) -> None:
        text = (
            '<img src="../figures/a.png" srcset="../figures/a.png 2x">'
            '<figure><img src="../figures/a.png"></figure>'
            '<a href="../guides/io.md">io</a>'
        )
        self.assertEqual(fetch_docs.collect_assets(text, "elements/text.md"), ["figures/a.png"])

    def test_collect_assets_ignores_remote_and_parent_paths(self) -> None:
        text = '<img src="https://example.com/x.png"><img src="../../outside.png">'
        self.assertEqual(fetch_docs.collect_assets(text, "index.md"), [])

    def test_collect_assets_ignores_absolute_paths(self) -> None:
        text = '<img src="/etc/passwd"><img src="../figures/a.png">'
        self.assertEqual(fetch_docs.collect_assets(text, "concepts/a.md"), ["figures/a.png"])

    def test_safe_join_keeps_paths_inside_the_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inside = fetch_docs.safe_join(tmp, "concepts/architecture.md")
            self.assertIsNotNone(inside)
            assert inside is not None
            self.assertTrue(inside.startswith(str(Path(tmp).resolve()) + os.sep))

    def test_safe_join_rejects_absolute_and_parent_escapes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(fetch_docs.safe_join(tmp, "/etc/passwd"))
            self.assertIsNone(fetch_docs.safe_join(tmp, "../outside.md"))
            self.assertIsNone(fetch_docs.safe_join(tmp, "concepts/../../outside.md"))
            self.assertIsNone(fetch_docs.safe_join(tmp, "concepts/../../../etc/passwd"))


class ParityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.docs = root / "docs"
        self.zh = self.docs / "zh"
        self.docs.mkdir()
        self.zh.mkdir()
        self._original = (check_parity.DOCS, check_parity.ZH)
        check_parity.DOCS = self.docs
        check_parity.ZH = self.zh

    def tearDown(self) -> None:
        check_parity.DOCS, check_parity.ZH = self._original
        self.tmp.cleanup()

    def write(self, relative: str, text: str, chinese: bool = False) -> None:
        base = self.zh if chinese else self.docs
        path = base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def page(self, path: str = "concepts/a.md") -> dict:
        return {"path": path, "title": "A"}

    def test_matching_translation_passes(self) -> None:
        self.write("concepts/a.md", "# Architecture\n\nSee `tern.ui` here.\n\n```lua\nprint(1)\n```\n")
        self.write(
            "concepts/a.md",
            "# 架构\n\n这里用到 `tern.ui`。\n\n```lua\nprint(1)\n```\n",
            chinese=True,
        )
        self.assertEqual(check_parity.check_page(self.page()), [])

    def test_missing_page_is_reported(self) -> None:
        self.write("concepts/a.md", "# Architecture\n")
        problems = check_parity.check_page(self.page())
        self.assertTrue(problems and "missing Chinese page" in problems[0])

    def test_code_block_drift_is_reported(self) -> None:
        self.write("concepts/a.md", "# Architecture\n\n```lua\nprint(1)\n```\n")
        self.write("concepts/a.md", "# 架构\n\n```lua\nprint(2)\n```\n", chinese=True)
        problems = check_parity.check_page(self.page())
        self.assertTrue(any("code blocks differ" in problem for problem in problems))

    def test_untranslated_heading_is_reported(self) -> None:
        self.write("concepts/a.md", "# Architecture notes\n\nText here about the thing.\n")
        self.write("concepts/a.md", "# Architecture notes\n\n这里是那段文本的描述。\n", chinese=True)
        problems = check_parity.check_page(self.page())
        self.assertTrue(any("untranslated" in problem for problem in problems))

    def test_truncated_translation_is_reported(self) -> None:
        self.write("concepts/a.md", "# Architecture\n\n" + "word " * 200 + "\n")
        self.write("concepts/a.md", "# 架构\n\n太短。\n", chinese=True)
        problems = check_parity.check_page(self.page())
        self.assertTrue(any("truncated" in problem for problem in problems))

    def test_fallback_page_is_exempt_from_prose_checks(self) -> None:
        body = "# Architecture\n\n" + "word " * 50 + "\n"
        self.write("concepts/a.md", body)
        self.write(
            "concepts/a.md",
            check_parity.FALLBACK_MARK + "\n\n> 本页尚未翻译。\n\n" + body,
            chinese=True,
        )
        self.assertEqual(check_parity.check_page(self.page()), [])

    def test_link_target_drift_is_reported(self) -> None:
        self.write("concepts/a.md", "# Architecture\n\n[Guides](b.md)\n[Other](../guides/x.md)\n")
        self.write("concepts/a.md", "# 架构\n\n[指南](b.md)\n[其它](../guides/y.md)\n", chinese=True)
        problems = check_parity.check_page(self.page())
        self.assertTrue(any("link targets differ" in problem for problem in problems))


class AssetRewriteTest(unittest.TestCase):
    def test_rewrites_figure_paths_and_keeps_descriptors(self) -> None:
        value = "../figures/a.png 2x, ../figures/b.png 3x"
        self.assertEqual(
            fix_zh_assets.fix_value(value, "../../"),
            "../../figures/a.png 2x, ../../figures/b.png 3x",
        )

    def test_keeps_remote_and_absolute_urls(self) -> None:
        value = "https://example.com/figures/a.png, /figures/b.png"
        self.assertEqual(fix_zh_assets.fix_value(value, "../../"), value)


class NormalizeZhTest(unittest.TestCase):
    def test_inserts_blank_line_before_heading_after_figure(self) -> None:
        text = "<figure>\n<img src=\"x.png\">\n</figure>\n## 标题\n"
        updated, inserted = normalize_zh.normalize(text)
        self.assertEqual(inserted, 1)
        self.assertEqual(updated, "<figure>\n<img src=\"x.png\">\n</figure>\n\n## 标题\n")

    def test_inserts_blank_line_before_figure(self) -> None:
        text = "正文。\n<figure>\n<img src=\"x.png\">\n</figure>\n"
        updated, inserted = normalize_zh.normalize(text)
        self.assertEqual(inserted, 1)
        self.assertTrue(updated.startswith("正文。\n\n<figure>"))

    def test_is_idempotent(self) -> None:
        text = "正文。\n<figure>\n<img src=\"x.png\">\n</figure>\n## 标题\n"
        once, _ = normalize_zh.normalize(text)
        twice, inserted = normalize_zh.normalize(once)
        self.assertEqual(inserted, 0)
        self.assertEqual(twice, once)

    def test_ignores_headings_inside_fenced_code(self) -> None:
        text = "```\n代码\n## 不是标题\n```\n"
        updated, inserted = normalize_zh.normalize(text)
        self.assertEqual(inserted, 0)
        self.assertEqual(updated, text)


class LinkCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dist = Path(self.tmp.name)
        (self.dist / "assets").mkdir()
        (self.dist / "assets" / "pic.hash.png").write_bytes(b"png")
        (self.dist / "index.html").write_text('<a href="/tern-docs/guide">Guide</a>', encoding="utf-8")
        (self.dist / "guide.html").write_text(
            '<h2 id="start">Start</h2><img src="/tern-docs/assets/pic.hash.png"'
            ' srcset="/tern-docs/assets/pic.hash.png 2x">',
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_normalize_strips_base(self) -> None:
        self.assertEqual(check_links.normalize("/tern-docs/guide#start"), ("guide", "start"))
        self.assertEqual(check_links.normalize("#local"), ("", "local"))

    def test_find_page_resolves_clean_urls(self) -> None:
        current = self.dist / "index.html"
        self.assertEqual(check_links.find_page(self.dist, current, "guide"), self.dist / "guide.html")
        self.assertIsNone(check_links.find_page(self.dist, current, "missing"))

    def test_img_and_srcset_targets_count_and_resolve(self) -> None:
        checked, assets, broken = check_links.check_dist(self.dist)
        self.assertEqual(broken, [])
        self.assertGreaterEqual(checked, 1)
        self.assertEqual(assets, 1)

    def test_missing_img_and_srcset_targets_fail(self) -> None:
        (self.dist / "broken.html").write_text(
            '<figure><img src="../figures/missing.light.png"'
            ' srcset="../figures/missing.light.png 2x, ../figures/missing.dark.png 2x">'
            "</figure>",
            encoding="utf-8",
        )
        _, _, broken = check_links.check_dist(self.dist)
        self.assertEqual(len(broken), 2)
        self.assertTrue(all("missing image asset" in item for item in broken))

    def test_missing_img_target_in_zh_section_page_fails(self) -> None:
        zh_dir = self.dist / "zh" / "elements"
        zh_dir.mkdir(parents=True)
        (zh_dir / "text.html").write_text('<img src="../figures/a.png">', encoding="utf-8")
        _, _, broken = check_links.check_dist(self.dist)
        self.assertTrue(any("zh/elements/text.html" in item for item in broken))


class SiteMapDocumentTest(unittest.TestCase):
    def test_status_reads_fallback_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            zh = Path(tmp)
            (zh / "a.md").write_text("# 标题\n", encoding="utf-8")
            (zh / "b.md").write_text(gen_site_map.FALLBACK_MARK + "\n", encoding="utf-8")
            original = gen_site_map.ZH
            gen_site_map.ZH = zh
            try:
                self.assertEqual(gen_site_map.status("a.md"), "已翻译")
                self.assertEqual(gen_site_map.status("b.md"), "回退英文")
                self.assertEqual(gen_site_map.status("c.md"), "回退英文")
            finally:
                gen_site_map.ZH = original


class WorkflowLocationTest(unittest.TestCase):
    """部署工作流只允许一个规范位置：.github/workflows/deploy.yml。

    工作流文件需要 token 具备 `workflow` 权限才能提交，本分支由维护者账号补交。因此本用例
    断言的是「文件实际状态」与「文档口径」必须一致，而不是在文件缺失时静默跳过：

    - 文件缺失 → 文档必须声明「待补交」，且不得出现「已生效 / 已启用」这类既成事实表述，
      否则读者会按文档预期等待一个永远不会触发的构建；
    - 文件存在 → 文档不得再称待补交，并逐项核对触发条件、权限、并发与双作业没有漂移。
    """

    WORKFLOW = ROOT / ".github" / "workflows" / "deploy.yml"
    LEGACY = ROOT / "ci" / "github-pages-deploy.yml"
    DOCS = ("README.md", os.path.join("ci", "README.md"))
    PENDING_MARKER = "待补交"
    LIVE_CLAIMS = ("已生效", "已启用", "会自动构建并部署")

    def _doc(self, name: str) -> str:
        return (ROOT / name).read_text(encoding="utf-8")

    def test_legacy_copy_removed(self) -> None:
        self.assertFalse(self.LEGACY.exists(), "ci/ 下不应再保留工作流副本")

    def test_docs_point_to_canonical_workflow(self) -> None:
        for name in self.DOCS:
            text = self._doc(name)
            self.assertIn(".github/workflows/deploy.yml", text, f"{name} 未指向规范工作流路径")
            self.assertNotIn("移动", text, f"{name} 仍在描述手工移动工作流文件")
            if not self.WORKFLOW.is_file():
                self.assertNotIn(
                    "](.github/workflows/deploy.yml)",
                    text,
                    f"{name} 用相对链接指向尚不存在的文件（点击即 404）",
                )

    def test_docs_state_matches_workflow_presence(self) -> None:
        """文件存在与否必须与文档口径一致；这是「工作流存在」验收项的红绿信号。"""
        present = self.WORKFLOW.is_file()
        for name in self.DOCS:
            text = self._doc(name)
            if present:
                self.assertNotIn(
                    self.PENDING_MARKER,
                    text,
                    f"{name} 仍称工作流待补交，但 .github/workflows/deploy.yml 已存在",
                )
            else:
                self.assertIn(
                    self.PENDING_MARKER,
                    text,
                    f"{name} 未声明工作流待补交，读者会误以为部署已生效",
                )
                for claim in self.LIVE_CLAIMS:
                    self.assertNotIn(
                        claim,
                        text,
                        f"{name} 在工作流文件缺失时仍声称「{claim}」",
                    )
        if not present:
            self.assertIn(
                "不会触发",
                self._doc("README.md"),
                "README.md 未说明补交前推送不会触发构建",
            )

    def test_workflow_keeps_triggers_permissions_and_jobs(self) -> None:
        if not self.WORKFLOW.is_file():
            # 文件缺失属阻塞态，但必须由文档口径显式披露（见上一个用例），不得静默 skip
            self.assertIn(self.PENDING_MARKER, self._doc("README.md"))
            return
        text = self.WORKFLOW.read_text(encoding="utf-8")
        for expected in (
            "name: Deploy docs to GitHub Pages",
            "branches: [main]",
            "workflow_dispatch:",
            "permissions:",
            "pages: write",
            "id-token: write",
            "concurrency:",
            "group: pages",
            "cancel-in-progress: false",
            "  build:",
            "  deploy:",
            "    needs: build",
            "actions/upload-pages-artifact@v3",
            "actions/deploy-pages@v4",
        ):
            self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()