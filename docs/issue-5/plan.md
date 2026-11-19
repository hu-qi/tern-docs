# Issue #5 方案设计

## 依赖与顺序

S1（mermaid）→ S2（上游比对）→ S3（`.md` 原文）→ S4（复制本页）→ S5（打印）。
S4 依赖 S3 产物；其余相互独立。

## S1 mermaid

- 新增 `docs/.vitepress/mermaid.mjs`：markdown-it core 规则，在
  `escape-vue-unsafe-tokens` **之后**把 `mermaid` 围栏改写为
  `<Mermaid source="<encodeURIComponent(图源)>" />`。
  - 图源以 prop 传入，不内联模板，避免与 `escapeVueUnsafeTokens` 的占位符机制冲突；
  - `encodeURIComponent` 只产生 URL 安全字符，可直接放进双引号 HTML 属性，避免转义歧义。
- `docs/.vitepress/config.mts`：`markdown.config` 注册 `escapeVueUnsafeTokens` + `mermaidFence`。
- `docs/.vitepress/theme/Mermaid.vue`：`onMounted` 动态 `import('mermaid')`，
  `initialize({ startOnLoad: false, securityLevel: 'loose', flowchart: { htmlLabels: true } })`
  后 `render()`，注入 SVG；`<br/>` 由 `htmlLabels` 生效。
- `docs/.vitepress/theme/index.ts`：继承默认主题，全局注册 `Mermaid`。

## S2 上游比对

- `scripts/diff_upstream.py`：
  - 从上游首页 HTML 解析现行 `<script src="toc-*.js">`，不硬编码文件名；
  - 解析 toc JS 得到页面清单，与 `site-map.json` 做差集；
  - 逐页抓取上游 `.md`，归一化 ` {#slug}` 锚点后缀后比对；
  - 输出「缺失 / 多余 / 内容差异」并幂等写入 `SITE_MAP.md` 的
    `<!-- upstream-diff:start -->` 区块。
- 纯函数（toc 解析、锚点归一化、差异分类、区块写入）可离线单测。

## S3 `.md` 原文

- `scripts/emit_markdown.py`：构建后把 `docs/**/*.md`、`docs/zh/**/*.md` 复制到
  `docs/.vitepress/dist` 同路径；跳过 `docs/issue-*`（`srcExclude`）与 `.vitepress`。
- `config.mts` 的 `transformHead`：按 `pageData.relativePath` 注入
  `<link rel="alternate" type="text/markdown" href="<base><relativePath>">`。
- `package.json`：`docs:build` 末尾串 `emit_markdown.py`；新增 `docs:md`。

## S4 复制本页

- `docs/.vitepress/theme/CopyPageButton.vue`：`fetch(base + relativePath)` →
  `navigator.clipboard.writeText` → 成功态提示；失败时 `window.open` 打开原文。
- `docs/.vitepress/theme/Layout.vue`：在默认主题 `doc-footer-before` 插槽放
  复制/打印按钮。

## S5 打印

- `docs/.vitepress/theme/custom.css`：`@media print` 隐藏
  `.VPNav`/`.VPSidebar`/`.VPLocalNav`/`.VPDocAside`/`.VPFooter`，正文全宽，
  `pre`/`table` 设 `break-inside: avoid`。
- `docs/.vitepress/theme/PrintButton.vue`：`window.print()`。

## 测试 seam

| 切片 | seam |
| --- | --- |
| S1 | `createMarkdownRenderer` 渲染含 mermaid 围栏的字符串，断言出现 `<Mermaid`、无裸围栏、图源可无损还原 |
| S2 | 纯函数夹具：toc 脚本名解析、toc JS 页面解析、锚点归一化、差异分类、区块幂等写入 |
| S3 | 真实 `docs/` 输出到临时目录，断言 85×2 页且逐字节一致 |
| S4/S5 | 构建产物回归（按钮/样式存在） |

## 风险

| 风险 | 缓解 |
| --- | --- |
| 图源含 `{}`/`<br/>` 与 Vue 转义冲突 | prop 传入 + URL 编码，保留原转义步骤并补断言 |
| `.md` 与同名 HTML 并存 | 仅追加 dist，不改 `cleanUrls`/路由，`docs:links` 回归 |
| 上游 toc 文件名变化 | 运行时解析首页 HTML |
| mermaid 拖慢首屏 | 动态 import，仅含图页面加载 |