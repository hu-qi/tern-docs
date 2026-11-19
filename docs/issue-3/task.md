# Issue #3 任务拆解（Task）

> 状态以仓库实际内容为准：`npm test` 全绿。

## M1 工作流迁移

- [x] 删除 `ci/github-pages-deploy.yml`（过渡副本），目标内容 = 原文件仅改首行注释
- [ ] `.github/workflows/deploy.yml` 由维护者账号补交（自动化 token 缺 `workflow` 权限，推送被拒）
- [x] 首行过期注释改写为当前状态说明（YAML 逻辑逐字不变）
- [x] 核对：`push: branches: [main]`、`workflow_dispatch`、`permissions`、`concurrency: pages`、
      `build` / `deploy` 双作业与原文一致

## M2 文档同步

- [x] `ci/README.md`：改为「规范位置 + 当前待补交」，保留 `workflow` 权限背景与被拒原文作为历史说明
- [x] `SYNC.md`：删去「需先把 ci/ 副本移为工作流」的提示，改指规范路径并注明补交后生效
- [x] `README.md`「部署」段：指向 `.github/workflows/deploy.yml`（行内代码，避免指向不存在文件的相对链接），
      一次性人工操作写清「补交工作流文件 + Pages Source 设为 GitHub Actions」两项
- [x] `docs/issue-3/spec.md` / `plan.md` / `task.md`

## M3 回归守护

- [x] `tests/test_scripts.py` 新增 `WorkflowLocationTest`：
      `ci/` 副本已移除、文档指向规范路径且无「移动」措辞、**文件状态与文档口径一致**
      （缺失 ⇒ 必须声明「待补交」且不得称已生效/已启用；存在 ⇒ 不得再称待补交），
      工作流存在时核对触发条件/权限/并发/双作业（缺文件时不再 skip）

## 验证命令

```bash
npm test
```

## 后续（不在本 PR 范围）

- 维护者在 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
- 合入 `main` 后由 sre 线上核对：Actions 双作业成功、`/` 与 `/zh/` 可访问、语言菜单互切、
  `workflow_dispatch` 可重复发布。