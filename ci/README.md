# GitHub Pages 部署工作流

部署工作流的规范位置是 `.github/workflows/deploy.yml`——GitHub 只识别 `.github/workflows/`
下的工作流，工作流放在该位置才会被触发。

**当前状态：该文件尚未进入仓库（待补交）。** 创建或更新 `.github/workflows/` 下的文件需要
GitHub token 具备 `workflow` 权限，自动化账号的推送会被拒绝：

```
! [remote rejected] feat/issue-3 -> feat/issue-3
  (refusing to allow a Personal Access Token to create or update workflow
   `.github/workflows/deploy.yml` without `workflow` scope)
```

因此该文件需由具备 `workflow` 权限的维护者账号补交（内容见 PR #4 描述，与已删除的
`ci/github-pages-deploy.yml` 逐字一致，仅首行注释改为陈述当前状态）。**文件补交前，
向 `main` 推送不会触发构建，`Actions` 中也不会有 `Deploy docs to GitHub Pages` 运行记录。**

补交后的行为：

- 触发方式：向 `main` 推送，或在 Actions 页面手动执行 `workflow_dispatch`。
- 工作流内容：`npm ci` → 单元测试 → 译文回退/锚点/插图规范化 → 译文一致性校验 →
  构建 → 站内链接校验 → `actions/upload-pages-artifact` + `actions/deploy-pages`。
  `build` / `deploy` 双作业，`concurrency: group: pages`，
  `permissions: contents: read / pages: write / id-token: write`。
- 首次发布前还需在 **Settings → Pages → Build and deployment → Source** 选择
  **GitHub Actions**，否则 `deploy` 作业会因 Pages 未启用而失败。

## 为什么不再保留 `ci/` 副本

工作流一度以副本形式存放于 `ci/` 下，等待具备 `workflow` 权限的账号提交；该副本已删除，
避免出现「仓库里有两份工作流、GitHub 只认其中一份」的分叉状态。规范内容以 PR #4 描述的
YAML 为准，补交时直接落到 `.github/workflows/deploy.yml`。

> 后续若由自动化账号修改该工作流，仍需 token 具备 `workflow` 权限；否则请由维护者账号提交。