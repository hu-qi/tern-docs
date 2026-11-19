# Issue #5 任务拆解

| # | 切片 | 交付物 | 测试 | 依赖 |
| --- | --- | --- | --- | --- |
| 1 | S1 mermaid | `docs/.vitepress/mermaid.mjs`、`theme/Mermaid.vue`、`theme/index.ts`、`config.mts` 注册、`package.json` 依赖 | `tests/mermaid.test.mjs` | — |
| 2 | S2 上游比对 | `scripts/diff_upstream.py`、`npm run docs:upstream`、`SITE_MAP.md` 区块 | `tests/test_upstream.py` 纯函数 | — |
| 3 | S3 `.md` 原文 | `scripts/emit_markdown.py`、`transformHead`、`docs:build` 串联 | `tests/test_emit_markdown.py` | — |
| 4 | S4 复制本页 | `theme/CopyPageButton.vue`、`theme/Layout.vue` | 构建产物回归 | S3 |
| 5 | S5 打印 | `theme/PrintButton.vue`、`theme/custom.css` | 构建产物回归 | — |
| 6 | 文档口径 | `README.md`、`SYNC.md`、`SITE_MAP.md` | 文档断言 | 1-5 |

每个切片先写失败测试（红），再提交最小实现（绿）。