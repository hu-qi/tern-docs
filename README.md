# tern-docs

[Tern Plugin SDK](https://docs.stencil.so/tern/) 官方文档的镜像与简体中文译本，
使用 [VitePress](https://vitepress.dev/) 构建，通过 GitHub Actions 部署到 GitHub Pages。

- 站点：`https://<owner>.github.io/tern-docs/`（英文，默认语言）
- 中文：`https://<owner>.github.io/tern-docs/zh/`（页面右上角语言菜单可切换）

## 目录结构

```
.github/workflows/deploy.yml  GitHub Actions：push main 构建并发布 GitHub Pages
docs/                    英文原文（与上游 mdBook 逐页对应）
docs/zh/                 简体中文译文（与 docs/ 路径一一对应）
docs/figures/            上游页面引用的全部插图（由抓取脚本一并下载）
docs/.vitepress/         VitePress 配置（locales / sidebar / 搜索 / Vue 转义）
scripts/fetch_docs.py    抓取上游全部页面与插图（HTML 对应的 .md 源）
scripts/sync_fallback.py 为尚未翻译的页面生成英文回退页
scripts/fix_anchors.py   对齐中英标题锚点（显式 {#id}）
scripts/fix_zh_assets.py 修正中文页面的插图相对路径
scripts/check_parity.py  校验中英页面结构、代码块、行内代码、链接一致
scripts/check_links.py   校验构建产物中的站内链接、锚点与插图
scripts/normalize_zh.py  补全中文页面标题/插图块前后的空行
scripts/gen_site_map.py  生成 SITE_MAP.md
tests/test_scripts.py    上述 Python 脚本的单元测试
tests/escape-vue.test.mjs  Vue 模板转义插件（escape-vue.mjs）的 node 单元测试
site-map.json            全站页面清单（章节 + 标题，用于生成侧边栏）
TRANSLATION.md           翻译约定与术语表
SITE_MAP.md              全站页面清单与翻译状态
SYNC.md                  上游增量同步与补译流程
```

## 本地开发

```bash
npm install
npm run docs:dev        # 本地预览 http://localhost:5173/tern-docs/
npm run docs:build      # 构建静态站点到 docs/.vitepress/dist
npm run docs:preview    # 预览构建产物
```

辅助命令：

```bash
npm run docs:fetch      # 重新抓取上游页面与插图，刷新 site-map.json（不改动 docs/zh/）
npm run docs:fallback   # 为缺失的译文生成英文回退页
npm run docs:anchors    # 对齐中英标题锚点（英文补 {#id}，中文镜像同一 id）
npm run docs:assets     # 修正中文页面的插图相对路径
npm run docs:normalize  # 补全中文页面标题/插图块前后的空行
npm run docs:check      # 中英页面一致性校验（CI 在构建前执行）
npm run docs:links      # 构建产物站内链接/锚点/插图校验（CI 在构建后执行）
npm run docs:map        # 重新生成 SITE_MAP.md
npm test                # 文档工具链单元测试（Python + node）
```

## 翻译

- 英文原文位于 `docs/`，中文译文位于 `docs/zh/`，两者相对路径必须一致，页面内相对链接
  因此无需改写。
- 代码块、行内代码、API 与类型标识、命令与路径一律保留原文；详见
  [TRANSLATION.md](TRANSLATION.md)。
- 未翻译的页面由 `npm run docs:fallback` 以英文原文补齐并标注"尚未翻译"，中文站点不会
  出现空页；补译后标记随译文消失。

## 部署

[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) 在 `main` 分支推送（或手动
`workflow_dispatch`）时执行：

1. `npm ci` + `npm test`（工具链单元测试，含 Python 脚本与 Vue 转义插件）
2. `npm run docs:fallback` + `docs:anchors` + `docs:assets` + `docs:normalize` + `docs:check`（译文一致性闸门）
3. `npm run docs:build` + `docs:links`（构建与站内链接/插图校验）
4. `actions/upload-pages-artifact` + `actions/deploy-pages` 发布到 GitHub Pages

首次发布前还需要一项一次性人工操作：在 **Settings → Pages → Build and deployment** 中将
**Source** 设为 **GitHub Actions**，否则 `deploy` 作业会因 Pages 未启用而失败。

设置完成后，每次向 `main` 推送或手动触发 `workflow_dispatch` 都会重新构建并发布
`https://<owner>.github.io/tern-docs/`（英文）与 `/zh/`（中文）；`concurrency: pages`
保证同一时间只有一次部署，重复发布不会冲突。工作流文件的权限背景见
[`ci/README.md`](ci/README.md)。

## 上游同步

上游页面有更新时按 [SYNC.md](SYNC.md) 的流程增量同步：抓取 → 对比 `site-map.json` 与
页面清单 → 补译变更页 → `npm run docs:check` → 提交。页面清单见
[SITE_MAP.md](SITE_MAP.md)。

## 许可与来源

文档内容来自 [stencil-hq/tern-sdk](https://github.com/stencil-hq/tern-sdk) 的
Tern Plugin SDK 文档（`https://docs.stencil.so/tern/`），本仓库仅做镜像、结构化为
VitePress 工程并附简体中文译文。