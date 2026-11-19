# 上游增量同步与补译（SYNC）

上游文档站：<https://docs.stencil.so/tern/>（mdBook）。本仓库的 `docs/` 与上游逐页对应，
`docs/zh/` 是中文译文。上游更新后按下面流程增量同步，**不要手工逐页复制**。

## 1. 抓取上游最新页面

```bash
npm run docs:fetch
```

`scripts/fetch_docs.py` 会：

- 读取上游 `toc.html`，得到章节结构与全部页面清单（当前 85 页）；
- 逐页抓取与 `.html` 同路径的 `.md` 源（例如 `concepts/architecture.html` →
  `concepts/architecture.md`），写入 `docs/` 的同路径文件；
- 重写 `site-map.json`（章节、标题、页面路径），供侧边栏与校验脚本使用；
- **不触碰** `docs/zh/` 与 `docs/.vitepress/`，因此可以安全重复执行。

抓取失败会以非 0 退出并列出失败页面，可直接重跑（脚本幂等）。

## 2. 查看差异

```bash
git status --short docs/ site-map.json
git diff --stat -- docs/
```

- 新增页面：`docs/` 下出现 `site-map.json` 中新的路径。
- 变更页面：`docs/` 下已有文件内容变化（`git diff` 可见）。
- 删除页面：上游目录删除某页时，`site-map.json` 不再包含它，需同步删除
  `docs/<path>` 与 `docs/zh/<path>`，否则 `docs:check` 会报"unexpected"。

## 3. 补译

| 情况 | 处理 |
| --- | --- |
| 新增页面 | 在 `docs/zh/` 同路径新建译文；未翻译时可先跳过，构建时自动回退英文 |
| 内容变更 | 对比 `git diff -- docs/<path>`，只修改 `docs/zh/<path>` 中对应的段落 |
| 页面删除 | 删除 `docs/<path>` 与 `docs/zh/<path>` |

翻译约定见 [TRANSLATION.md](TRANSLATION.md)（术语表、代码块与链接保留规则）。

## 4. 校验与提交

```bash
npm run docs:fallback   # 缺失译文补英文回退页（带"尚未翻译"标记）
npm run docs:anchors    # 中英标题锚点对齐（英文补 {#id}，中文镜像）
npm run docs:assets     # 中文页面插图路径修正到 docs/figures/
npm run docs:normalize  # 补全标题/插图块前后的空行（构建前自动执行）
npm run docs:check      # 结构 / 代码块 / 行内代码 / 链接 / 篇幅一致性
npm run docs:build      # 静态构建
npm run docs:links      # 构建产物站内链接、锚点与插图校验
npm run docs:map        # 刷新 SITE_MAP.md（翻译状态与覆盖率）
```

上述检查全部通过后提交：

```bash
git add docs site-map.json SITE_MAP.md
git commit -m "docs: sync upstream tern documentation"
```

提交到 `main` 后 GitHub Actions 会自动构建并部署到 GitHub Pages（工作流
`.github/workflows/deploy.yml`；`ci/README.md` 记录了 `workflow` 权限背景）。

## 5. 翻译覆盖率

`SITE_MAP.md` 记录全站页面与翻译状态（`已翻译` / `回退英文`）。回退页在中文站点顶部有
"本页尚未翻译"提示，补译后该提示消失。统计当前覆盖率：

```bash
grep -c '已翻译' SITE_MAP.md
```

## 6. 已知约束

- 上游页面内的锚点链接（`page.md#anchor`）依赖英文标题的 slug；中文标题使用显式锚点
  `{#slug}` 保持与英文一致，改标题时不要删除该后缀，否则站内跳转会失效。
- 上游若改变章节层级或重命名路径，`site-map.json` 会随之变化，侧边栏自动跟随；此时需要
  同步移动 `docs/zh/` 下的译文路径。
- 抓取频率保持默认的 0.2 秒间隔，避免对上游站点造成压力。