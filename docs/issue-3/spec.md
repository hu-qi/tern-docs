# Issue #3 需求文档（Spec）

> 目标仓库：`hu-qi/tern-docs`｜目标分支：`main`｜来源：Issue #3「发布到 github page」

## 1. 需求来源

站点构建与校验链路已在 Issue #1 / PR #2 合入 `main`，但部署工作流放在 `ci/` 目录下，
GitHub 只识别 `.github/workflows/` 下的文件，因此推送 `main` 不会触发任何构建与发布，
对外文档始终没有自动上线。

Issue Agent 的可开发性结论：评级 ready，目标分支 `main`，方案为「纯文件迁移 + 文档措辞更新」。

## 2. 范围

### In Scope

1. `ci/github-pages-deploy.yml` → `.github/workflows/deploy.yml`（工作流逻辑零改动）。
2. `README.md`「部署」段与 `ci/README.md` 同步更新，移除「文件需手动移动才生效」的表述。
3. 仓库 Settings → Pages → Source 设为 **GitHub Actions**（维护者一次性人工操作，不在代码范围）。

### Out of Scope

- 工作流逻辑改动：`build` / `deploy` 双作业、`concurrency: pages`、`permissions` 均保持原样。
- 站点内容、译文、VitePress 配置变更。
- Pages Source 的自动切换（平台限制，无法由代码完成）。
- 首次线上发布与访问验收（由 sre / 维护者在 Pages Source 切换后执行）。

## 3. 验收标准与对应实现

| 验收标准 | 实现 |
| --- | --- |
| `ci/` 下不再有该工作流文件；`.github/workflows/deploy.yml` 为唯一规范位置 | 本分支删除 `ci/` 副本；工作流文件由具备 `workflow` 权限的账号补交（自动化 token 推送被 GitHub 拒绝，见 §4） |
| 工作流内容与原文件一致 | 仅替换首行「本文件需移动才生效」的过期注释，YAML 逻辑逐字不变（`diff` 除首行外无差异） |
| `README.md`、`ci/README.md` 不再出现「需手动移动文件才生效」类表述 | 两处部署说明改写为「规范位置 + 当前待补交」，并写明补交前推送不会触发部署；文件补交后改回「已生效」 |
| push `main` / `workflow_dispatch` 触发 `Deploy docs to GitHub Pages`，build 与 deploy 均成功 | 工作流原样迁移，触发条件与作业图不变 |
| `https://<owner>.github.io/tern-docs/` 与 `/zh/` 可访问，语言菜单可互切 | 站点既有能力，发布后由 sre 线上核对 |
| `workflow_dispatch` 可重复发布，无并发部署冲突 | 保留 `concurrency: group: pages, cancel-in-progress: false` |
| 现有测试 `npm test` 全部通过 | 新增守护测试后仍全绿（27 → 31 项 Python 用例 + 6 项 node 用例） |

## 4. 约束与风险

- 推送到 `.github/workflows/` 需要 token 具备 `workflow` 权限（`ci/README.md` 已记录历史被拒
  原因）。本次自动化 token 实测被 GitHub 拒绝：
  `refusing to allow a Personal Access Token to create or update workflow
  .github/workflows/deploy.yml without workflow scope`——因此工作流文件本身由维护者账号补交，
  其余改动（删除 `ci/` 副本、文档改写、守护测试）由本分支交付。
- Pages Source 未切换为 GitHub Actions 时，`deploy` 作业会因 Pages 未启用而失败——属一次性人工操作。
- `docs/issue-*/` 下的文档会被 VitePress 一并构建，新增页面须与既有 `docs/issue-1/` 保持同样的
  可构建性（不引入断链、不触发 `docs:check` 结构漂移）。