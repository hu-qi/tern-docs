# GitHub Pages 部署工作流

部署工作流的规范位置是 `.github/workflows/deploy.yml`——GitHub 只识别 `.github/workflows/`
下的工作流，工作流放在该位置才会被触发。

**当前状态：该工作流已在规范位置落地生效。** 创建或更新 `.github/workflows/` 下的文件需要
GitHub token 具备 `workflow` 权限，此前自动化账号曾因 token 缺 scope 报错：

```
! [remote rejected] feat/issue-3 -> feat/issue-3
  (refusing to allow a Personal Access Token to create or update workflow
   `.github/workflows/deploy.yml` without `workflow` scope)
```

工作流行为：

- 触发方式：向 `main` 推送，或在 Actions 页面手动执行 `workflow_dispatch`。
- 工作流内容：`npm ci` → 单元测试 → 译文回退/锚点/插图规范化 → 译文一致性校验 →
  构建 → 站内链接校验 → `actions/upload-pages-artifact` + `actions/deploy-pages`。
  `build` / `deploy` 双作业，`concurrency: group: pages`，
  `permissions: contents: read / pages: write / id-token: write`。
- 首次发布前还需在 **Settings → Pages → Build and deployment → Source** 选择
  **GitHub Actions**，否则 `deploy` 作业会因 Pages 未启用而失败。

## 为什么不再保留 `ci/` 副本

工作流一度以副本形式存放于 `ci/` 下，等待具备 `workflow` 权限的账号提交；该副本已删除，
避免出现「仓库里有两份工作流、GitHub 只认其中一份」的分叉状态。规范内容已落到 `.github/workflows/deploy.yml`。

> 后续若由自动化账号修改该工作流，仍需 token 具备 `workflow` 权限；否则请由维护者账号提交。