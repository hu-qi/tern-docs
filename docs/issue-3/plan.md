# Issue #3 方案设计（Plan）

## 1. 总体方案

```
ci/github-pages-deploy.yml ──git mv──▶ .github/workflows/deploy.yml
                                            │
                     push main / workflow_dispatch
                                            ▼
                        build（npm ci → npm test → 译文闸门 → 构建 → 链接校验 → upload artifact）
                                            ▼
                        deploy（actions/deploy-pages，environment: github-pages）
                                            ▼
                            https://<owner>.github.io/tern-docs/ (+ /zh/)
```

纯文件迁移：工作流 YAML 逻辑（双作业、`needs: build`、`concurrency: pages`、`permissions`）
逐字保留，只改一行过期注释；文档侧同步改写部署说明。

## 2. 迁移细节

| 项 | 处理 |
| --- | --- |
| 工作流文件 | 目标位置 `.github/workflows/deploy.yml`，内容 = `ci/` 副本仅改首行注释。**该文件的推送被 GitHub 以缺 `workflow` 权限拒绝**，故由维护者账号补交（内容见 PR 描述），本分支负责其余改动 |
| 首行注释 | 原文为「本文件需移动到 `.github/workflows/deploy.yml` 才会生效」——迁移后自指且失效，替换为当前状态说明（仅注释行，不触碰任何 YAML 键） |
| 其余内容 | 与原文逐字一致（可用 `diff` 核对：除首行注释外无差异） |
| `ci/README.md` | 由「待启用 / 需手动移动」改为「工作流位于 `.github/workflows/deploy.yml`，已生效」，保留 `workflow` 权限背景作为历史说明 |
| `SYNC.md` 部署提示 | 同步去掉「需先把 ci/ 下的副本移为工作流」的一句，改为指向已生效的工作流 |
| `README.md` 部署段 | 直接指向 `.github/workflows/deploy.yml`；一次性人工操作只剩「Pages Source 设为 GitHub Actions」 |
| `docs/issue-3/*.md` | 需求 / 方案 / 任务文档，与 `docs/issue-1/` 保持同一组织方式 |

## 3. 关键设计决策

| 决策 | 选项 | 选择 | 理由 |
| --- | --- | --- | --- |
| 首行过期注释 | 完全零改动 / 改写注释 | 改写注释 | 保留会让已生效的工作流自身写着「需移动才生效」，与验收标准冲突；只动注释不动逻辑，风险为零 |
| `ci/` 目录去留 | 删除整个目录 / 保留说明 | 保留 `ci/README.md` | 记录 `workflow` 权限限制与被拒原因，避免后人再建副本 |
| 回归守护 | 仅人工核对 / 加单测 | 加单测 | 迁移易被后续提交回退（例如再复制一份到 `ci/`），用 `WorkflowLocationTest` 固化路径唯一性与文档措辞 |
| 线上验收 | coding 本地 / sre 线上 | sre 线上 | Pages 发布需真实仓库设置与公网访问，编码阶段无法验证 |

## 4. 测试 seam

新增 `tests/test_scripts.py::WorkflowLocationTest`，断言的是**仓库对外可观察的状态**而非实现细节：

1. `ci/github-pages-deploy.yml` 不存在（过渡副本已移除，路径唯一）；
2. 工作流文件存在时保留触发条件（`push: branches: [main]`、`workflow_dispatch`）、`permissions`、
   `concurrency: pages` 与 `build`/`deploy` 双作业（文件未补交时该用例 skip，不阻塞 CI）；
3. `README.md` 与 `ci/README.md` 中不再出现「移动」类措辞。

先写测试（红）→ 再迁移（绿），保证「先有契约」。

## 5. 验证命令

```bash
npm test                                   # 27 → 29 项 Python 用例 + 6 项 node 用例
diff <(tail -n +2 ci-original) .github/workflows/deploy.yml   # 迁移前后逻辑差异核对
```