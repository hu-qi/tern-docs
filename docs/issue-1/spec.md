# Issue #1 需求文档（Spec）

> 目标仓库：`hu-qi/tern-docs`（空仓库，从零搭建）｜源站：<https://docs.stencil.so/tern/>

## 1. 需求来源

Issue #1「汉化 https://docs.stencil.so/tern/ 官方文档并部署」：

1. 扫描 `https://docs.stencil.so/tern/` 的全部文档，按结构落到本仓库；
2. 添加 i18n，支持简体中文；
3. 部署到 GitHub Pages。

Issue Agent 给出的开发性结论：评级 ready，目标分支 `main`，技术栈建议 mdBook 或等价静态站点，
中文与英文页面一一对应、未翻译页回退英文、代码与 API 标识保持原文。

## 2. 范围

### In Scope

- 抓取源站全部页面（源站为 mdBook，每页提供同路径 `.md` 纯文本版）与页面引用的全部插图，
  按源站章节结构（Overview / Concepts / Guides / Elements / Styles / Surface Protocol /
  Examples / Scripts / Reference）落地为可构建的文档工程。
- 双语站点：英文为默认语言，右上角语言菜单切换到简体中文；中英页面路径一一对应。
- 简体中文覆盖全部正文页面；代码块、行内代码、API/类型/命令/路径标识保持原文。
- 未翻译页面回退英文（带"尚未翻译"提示），后续补译不改变工程结构。
- GitHub Actions：`main` 推送触发构建并发布 GitHub Pages。
- 全站页面清单 `SITE_MAP.md`、上游增量同步说明 `SYNC.md`、翻译约定 `TRANSLATION.md`。

### Out of Scope

- 源站内容的技术性改写或补写（仅结构化落地与翻译）。
- 搜索以外的增强功能（评论、版本切换等）。
- 自定义域名（使用仓库默认 Pages 域名）。

## 3. 验收标准与对应实现

| 验收标准 | 实现 |
| --- | --- |
| 全站页面清单与源站一一对应，目录/章节层级一致 | `scripts/fetch_docs.py` 解析上游 `toc.html` 生成 `site-map.json`（85 页）；`SITE_MAP.md` 记录清单与翻译状态 |
| 站内链接/图片可正常打开 | 页面路径与上游同构；`scripts/check_links.py` 对构建产物校验 2 万余条站内链接与锚点 |
| 文档工程可本地构建 | `npm run docs:build`（VitePress） |
| 页面上提供 中文 / English 切换 | VitePress `locales`（root=en，`/zh/`=zh-Hans） |
| 简体中文覆盖全部正文页面 | `docs/zh/` 与 `docs/` 逐页对应；`scripts/check_parity.py` 校验标题结构、代码块、行内代码、链接与篇幅 |
| 术语与代码标识保持原文 | `TRANSLATION.md` 术语表 + 守门脚本的代码块/行内代码一致性检查 |
| 推送 `main` 后自动构建部署 | `ci/github-pages-deploy.yml`（启用时移入 `.github/workflows/deploy.yml`，`actions/deploy-pages`） |
| 附带增量同步与补翻译说明 | `SYNC.md`（抓取 → 差异 → 补译 → 校验 → 提交）+ `scripts/sync_fallback.py` |

## 4. 约束与假设

- 上游站点不需登录、无鉴权，抓取限速 0.02–0.2 秒/请求，失败重试 3 次。
- 仓库初始为空（无任何提交），需要先建立 `main` 基线，PR 才有可用的 base。
- 首次启用 Pages 需在仓库 Settings → Pages 将 Source 设为 **GitHub Actions**（一次性人工操作）。
- 源码目录 `docs/` 与译文目录 `docs/zh/` 的中英配对关系是后续增量同步的基础，路径不得随意变动。