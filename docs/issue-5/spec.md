# Issue #5 需求文档：发现和补齐差距

## 目标

让 `https://<owner>.github.io/tern-docs/`（含 `/zh/`）在上游
`https://docs.stencil.so/tern/` 的**阅读正确性、取用原文、打印、内容完整性**四个
维度无可见差距，并把「与上游是否一致」做成一条可重复执行的命令。

## 现状

| # | 差距 | 证据 |
| --- | --- | --- |
| 1 | mermaid / `flowchart TB` 未渲染 | `docs/concepts/architecture.md` L181、`docs/zh/concepts/architecture.md` L98 为 mermaid 围栏；`config.mts` 只注册 `escapeVueUnsafeTokens` |
| 2 | 无法查看 `.md` 原文 | `cleanUrls: true`，构建产物只有 HTML；上游 `/concepts/architecture.md` 返回 `200 text/markdown` |
| 3 | 无「复制本页」 | 无自定义主题，默认主题无该入口 |
| 4 | 无打印入口/样式 | 无 `@media print` 规则，`Ctrl+P` 会打印导航/侧边栏 |
| 5 | 无上游比对工具 | 页面清单与内容已对齐（85/85、76 逐字节一致、9 页仅 `{#slug}` 锚点差异），但缺少可重复命令与留痕 |

## 范围

### In Scope

- S1 mermaid 渲染（英文站 + 中文站架构页 1 张图）
- S2 `scripts/diff_upstream.py` + `npm run docs:upstream` + `SITE_MAP.md` 留痕
- S3 构建后产出 `<path>.md` 原文（en/zh）+ `head` 注入 `link rel="alternate"`
- S4「复制本页」入口（复用 S3 产物）
- S5 打印样式 + 打印入口

### Out of Scope

- 不改 `cleanUrls: true`
- 不重译/重写正文，不回改上游原文（9 页 anchor 差异由 S2 归一化）
- 不迁移托管方式，不改 `scripts/fetch_docs.py` 抓取口径

## 验收标准

1. 中英两站架构页出现渲染后的 SVG，控制台无 mermaid 报错，`<br/>` 换行正确。
2. `npm run docs:upstream` 输出「缺失 0 / 多余 0」，anchor-only 差异归一化后不计差异，结果写入 `SITE_MAP.md`。
3. 构建产物中 `/concepts/architecture.md`、`/zh/concepts/architecture.md` 与源文件逐字节一致。
4. 「复制本页」内容与对应语言源文件一致，失败降级为打开原文。
5. 打印无导航/侧边栏/页脚，代码块与表格不跨页截断。
6. `npm test`、`npm run docs:check`、`npm run docs:links` 全通过，中文站结构一致性不回归。