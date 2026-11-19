# Issue #3 任务拆解（Task）

> 状态以仓库实际内容为准：`npm test` 全绿。

## M1 工作流迁移

- [x] 删除 `ci/github-pages-deploy.yml`（过渡副本），目标内容 = 原文件仅改首行注释
- [ ] `.github/workflows/deploy.yml` 由维护者账号补交（自动化 token 缺 `workflow` 权限，推送被拒）
- [x] 首行过期注释改写为当前状态说明（YAML 逻辑逐字不变）
- [x] 核对：`push: branches: [main]`、`workflow_dispatch`、`permissions`、`concurrency: pages`、
      `build` / `deploy` 双作业与原文一致

## M2 文档同步

- [x] `ci/README.md`：改为「工作流已生效」，保留 `workflow` 权限背景作为历史说明
- [x] `SYNC.md`：删去「需先把 ci/ 副本移为工作流」的提示，改指已生效的工作流
- [x] `README.md`「部署」段：指向 `.github/workflows/deploy.yml`，一次性人工操作只剩 Pages Source
- [x] `docs/issue-3/spec.md` / `plan.md` / `task.md`

## M3 回归守护

- [x] `tests/test_scripts.py` 新增 `WorkflowLocationTest`：
      `ci/` 副本已移除、文档指向规范路径且无「移动」措辞、工作流存在时核对触发条件/权限/并发/双作业

## 验证命令

```bash
npm test
```

## 后续（不在本 PR 范围）

- 维护者在 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
- 合入 `main` 后由 sre 线上核对：Actions 双作业成功、`/` 与 `/zh/` 可访问、语言菜单互切、
  `workflow_dispatch` 可重复发布。