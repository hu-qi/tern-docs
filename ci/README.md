# GitHub Pages 部署工作流

此文件与 `.github/workflows/deploy.yml` 的内容完全一致，放在 `ci/` 下是因为创建
`.github/workflows/` 下的文件需要 GitHub token 具备 `workflow` 权限；当前自动化任务的
token 不具备该权限，推送会被拒绝（`refusing to allow a Personal Access Token to create or
update workflow ... without workflow scope`）。

启用方式（二选一，均为一次性人工操作）：

1. 仓库 **Settings → Actions → General** 允许 Actions 后，把本文件移动到工作流目录：
   ```bash
   git mv ci/github-pages-deploy.yml .github/workflows/deploy.yml
   git commit -m "ci: enable GitHub Pages deployment"
   git push
   ```
2. 或在 GitHub 网页端直接新建 `.github/workflows/deploy.yml`，粘贴本文件内容。

首次部署还需要在 **Settings → Pages → Build and deployment → Source** 选择
**GitHub Actions**，否则 `deploy` 作业会因 Pages 未启用而失败。

工作流内容：`push(main)` / `workflow_dispatch` → `npm ci` → 单元测试 →
译文回退/锚点/插图规范化 → 译文一致性校验 → 构建 → 站内链接校验 →
`actions/upload-pages-artifact` + `actions/deploy-pages`。