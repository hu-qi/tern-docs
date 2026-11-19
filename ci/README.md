# GitHub Pages 部署工作流

部署工作流位于 [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml)。
GitHub 只识别 `.github/workflows/` 下的工作流，因此它在该位置才会被触发。

触发方式：向 `main` 推送，或在 Actions 页面手动执行 `workflow_dispatch`。

工作流内容：`npm ci` → 单元测试 → 译文回退/锚点/插图规范化 → 译文一致性校验 →
构建 → 站内链接校验 → `actions/upload-pages-artifact` + `actions/deploy-pages`。
`build` / `deploy` 双作业，`concurrency: group: pages`，
`permissions: contents: read / pages: write / id-token: write`。

首次发布前的一次性人工操作：在 **Settings → Pages → Build and deployment → Source**
选择 **GitHub Actions**，否则 `deploy` 作业会因 Pages 未启用而失败。

## 历史背景：为什么工作流曾放在 ci/

创建或更新 `.github/workflows/` 下的文件需要 GitHub token 具备 `workflow` 权限，
而此前的自动化账号不具备该权限，推送会被拒绝（`refusing to allow a Personal Access Token
to create or update workflow ... without workflow scope`）。为此工作流一度以副本形式存放于
`ci/` 下，等待具备该权限的账号提交；现已在 `.github/workflows/deploy.yml` 生效，`ci/` 下
不再保留副本。

> 后续若由自动化账号修改该工作流，仍需 token 具备 `workflow` 权限；否则请由维护者账号提交。