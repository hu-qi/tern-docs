# Issue #1 方案设计（Plan）

## 1. 总体方案

```
上游 mdBook 站 ──fetch_docs.py──▶ docs/*.md + docs/figures/*
                                      │
                     ┌────────────────┴────────────────┐
                     ▼                                 ▼
                Lang=English                      docs/zh/*.md（简体中文，逐页对应）
                     └────────────┬────────────────────┘
                                  ▼
                       VitePress（locales: en / zh-Hans）
                                  ▼
                        GitHub Actions → GitHub Pages
```

选型：**VitePress**（原生 `locales`，默认英文 + 语言切换，静态构建，GitHub Pages 官方部署动作可直接复用）。
上游 `.md` 直取（源站每页都提供与 `.html` 同路径的 `.md`），不做 HTML 清洗，保证内容保真。

## 2. 目录与路径映射

| 仓库路径 | 含义 |
| --- | --- |
| `docs/<path>.md` | 英文页（= 上游 `<path>.md`），URL `/<path>` |
| `docs/zh/<path>.md` | 中文页，URL `/zh/<path>` |
| `docs/figures/*.png` | 上游插图（`<img src="../figures/…">` 引用） |
| `site-map.json` | 上游目录树（章节 + 标题），驱动侧边栏与校验 |
| `docs/.vitepress/` | 站点配置、Vue 转义插件 |

中英路径一一对应，页面内的相对链接（`../guides/x.md#anchor`）在两种语言下都无需改写即可命中。

## 3. 关键设计决策

| 决策 | 选项 | 选择 | 理由 |
| --- | --- | --- | --- |
| 站点框架 | mdBook / VitePress | VitePress | 原生 locales + 语言切换；mdBook 的 gettext 双构建链路更复杂 |
| 抓取方式 | HTML 解析 / `.md` 直取 | `.md` 直取 | 源站每页有同路径 `.md`，结构保真、免清洗 |
| 站点路径 | `docs/en` + `docs/zh` / `docs` + `docs/zh` | `docs` + `docs/zh` | 英文 URL 保持根路径（`/`），中文 `/zh/`，链接对称 |
| 锚点 | 依赖自动 slug / 显式 `{#id}` | 中文页显式镜像英文 id | mdBook 的 id（`ternon`）与 VitePress（`tern-on`）不同；中文标题更会变。`scripts/fix_anchors.py` 保证两种语言同一 id |
| 插图 | 中英各存一份 / 单一副本 | 单一副本 `docs/figures` | 中文页深一层，`scripts/fix_zh_assets.py` 把 `../figures/` 改成 `../../figures/` |
| 未翻译页 | 404 / 英文回退 | 英文回退 | `scripts/sync_fallback.py` 生成带 `<!-- fallback -->` 标记的英文副本，构建不缺口 |
| 译文守门 | 人工抽查 / 脚本校验 | 脚本校验 | `check_parity.py` 比对标题结构、代码块逐字一致、行内代码、链接目标、篇幅比例 |

## 4. 上游内容的两处兼容处理

1. **Vue 模板字符**：上游正文里存在 `{{start, end}`、`<config>`、`<builder>` 这类内容，VitePress 会把
   页面当 Vue 模板编译而报错。`docs/.vitepress/escape-vue.mjs` 在 markdown-it 的 core 阶段只对
   文本/行内代码 token 做实体转义，代码块、真实 HTML（`figure/img/div`）保持原样。
2. **HTML 块吞标题**：`</figure>` 后缺空行会让后续标题被当作 HTML 块内容。`scripts/normalize_zh.py`
   补齐空行（只改空白，不改文字）。

## 5. 质量闸门（CI 顺序）

```
test:scripts → docs:fallback → docs:anchors → docs:assets → docs:check → docs:build → docs:links
```

- `test:scripts`：17 个单元测试覆盖抓取解析、译文一致性、slug/锚点、插图路径、链接解析、清单状态。
- `docs:check`：85 页逐页比对，任何结构漂移即失败。
- `docs:links`：对构建产物校验全部站内链接与锚点（当前 2 万余条）。

## 6. 部署

`ci/github-pages-deploy.yml`（需人工移为 `.github/workflows/deploy.yml`，见 §8）`push(main)` / `workflow_dispatch` → Node 20 + `npm ci` → 上述闸门 →
`actions/configure-pages` + `upload-pages-artifact` → `actions/deploy-pages`。
首次部署需在仓库 Settings → Pages 选择 **GitHub Actions** 作为来源。

## 7. 风险与对策

| 风险 | 影响 | 对策 |
| --- | --- | --- |
| 上游页面遗漏 | 高 | `toc.html` 全量清单 + `site-map.json` 对账（85/85） |
| 译文结构漂移/漏译 | 中 | `check_parity.py` 双语文档闸门，缺失即 CI 失败 |
| 中文锚点失效 | 中 | 显式 `{#id}` 镜像 + `check_links.py` 产物校验 |
| 空仓库无 base 分支 | 中 | 先推 `main` 引导提交（含 README/.gitignore），后续全部走 PR |
| Pages 未启用 | 中 | README/SYNC 明确一次性人工设置项 |
## 8. 已知限制：工作流文件需人工启用

当前自动化 token 不具备 GitHub 的 `workflow` scope，向 `.github/workflows/` 推送文件会被拒绝：

```
refusing to allow a Personal Access Token to create or update workflow
`.github/workflows/deploy.yml` without `workflow` scope
```

因此工作流以 `ci/github-pages-deploy.yml` 形式随 PR 提交，启用方式与原因见 `ci/README.md`
（`git mv` 到 `.github/workflows/deploy.yml` 后推送）。这是唯一需要人工介入的部署步骤，
文档站本身（85 页英文 + 85 页中文、双语切换、站内链接）已在本地构建与校验通过。
