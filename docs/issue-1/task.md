# Issue #1 任务拆解（Task）

> 状态以仓库实际内容为准：`npm run docs:check` / `docs:build` / `docs:links` / `test:scripts` 全绿。

## M1 抓取与落地

- [x] `scripts/fetch_docs.py`：解析上游 `toc.html` → 抓取 85 页 `.md` → 抓取 374 个插图 →
      生成 `site-map.json`
- [x] `npm run docs:fetch` 幂等复核（85/85 页面、374/374 资源）

## M2 站点工程

- [x] `package.json` + VitePress 依赖（`npm ci`）
- [x] `docs/.vitepress/config.mts`：`base=/tern-docs/`、`cleanUrls`、locales（en 默认 / zh-Hans）、
      侧边栏由 `site-map.json` 生成、本地搜索
- [x] `docs/.vitepress/escape-vue.mjs`：正文 `{{ }}`/`<tag>` 转义，保证 Vue 模板可编译
- [x] `scripts/fix_anchors.py`：中英标题锚点对齐（显式 `{#id}`，重复标题自动去重）
- [x] `scripts/fix_zh_assets.py` + `scripts/normalize_zh.py`：中文页插图路径与空行规范
- [x] `npm run docs:build` 本地构建通过

## M3 翻译

- [x] `TRANSLATION.md`：翻译规则 + 术语表 + 校验命令
- [x] `docs/zh/` 与 `docs/` 逐页对应的 85 页简体中文译文（按章节分批完成）
- [x] 代码块、行内代码、API/命令/路径标识保持原文（脚本逐页校验）
- [x] 未翻译页回退英文：`scripts/sync_fallback.py`

## M4 部署与文档

- [x] `ci/github-pages-deploy.yml`：main 推送 → 闸门 → 构建 → Pages 部署（需人工移入
      `.github/workflows/`，见 `ci/README.md`）
- [x] `README.md`（工程说明/本地开发/部署步骤）
- [x] `SITE_MAP.md`（85 页清单与翻译状态，由 `scripts/gen_site_map.py` 生成）
- [x] `SYNC.md`（上游增量同步与补译流程）
- [x] `tests/test_scripts.py`：文档工具链单元测试（17 项）

## 验证命令

```bash
npm run test:scripts
npm run docs:fallback && npm run docs:anchors && npm run docs:assets
npm run docs:check
npm run docs:build
npm run docs:links
```

## 后续（不在本 PR 范围）

- 仓库 Settings → Pages 来源设为 GitHub Actions（一次性人工操作）。
- 上游更新后按 `SYNC.md` 增量同步与补译。