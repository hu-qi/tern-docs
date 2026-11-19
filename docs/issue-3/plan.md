# Issue #3 方案设计（Plan）

## 1. 总体方案

```
ci/github-pages-deploy.yml ──内容转交（PR #4 描述）──▶ .github/workflows/deploy.yml（维护者补交）
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

**迁移方式与原设想不同**：把工作流文件提交到 `.github/workflows/deploy.yml` 的推送被 GitHub 拒绝
（`refusing to allow a Personal Access Token to create or update workflow ... without workflow scope`
——自动化 token 缺 `workflow` 作用域，本地提交即使成功也推不上去）。因此实际交付拆成两段：

| 段 | 负责方 | 内容 |
| --- | --- | --- |
| 本分支 | 自动化账号 | 删除 `ci/` 副本、改写文档口径（声明「待补交」）、守护测试 |
| 补交 | 维护者账号（具备 `workflow` 权限） | 把 PR #4 描述中的 YAML 落到 `.github/workflows/deploy.yml` |

## 2. 迁移细节

| 项 | 处理 |
| --- | --- |
| 工作流文件 | 目标位置 `.github/workflows/deploy.yml`，内容 = 原 `ci/` 副本仅改首行注释。**该文件的提交被 GitHub 以缺 `workflow` 权限拒绝**，故由维护者账号补交（内容见 PR 描述），本分支负责其余改动 |
| 首行注释 | 原文为「本文件需移动到 `.github/workflows/deploy.yml` 才会生效」——落到规范位置后自指且失效，替换为当前状态说明（仅注释行，不触碰任何 YAML 键） |
| 文档口径 | 文件缺失期间，`README.md` / `ci/README.md` 必须明确写「待补交」，并说明补交前推送不会触发部署；不得出现「已生效 / 已启用 / 会自动构建并部署」等既成事实表述。文件补交后口径反转——两种方向都由 `test_docs_state_matches_workflow_presence` 强制 |
| `ci/README.md` | 由「待启用 / 需手动移动」改为「规范位置 `.github/workflows/deploy.yml` + 当前待补交 + 补交后行为」，保留 `workflow` 权限背景作为历史说明 |
| `SYNC.md` 部署提示 | 去掉「需先把 ci/ 下的副本移为工作流」，改为指向规范路径并注明补交后生效 |
| `README.md` 部署段 | 指向 `.github/workflows/deploy.yml`（用行内代码而非相对链接——文件尚不存在，相对链接会 404）；一次性人工操作明确为「补交工作流 + Pages Source 设为 GitHub Actions」两项 |
| `docs/issue-3/*.md` | 需求 / 方案 / 任务文档，与 `docs/issue-1/` 保持同一组织方式 |

## 3. 关键设计决策

| 决策 | 选项 | 选择 | 理由 |
| --- | --- | --- | --- |
| 迁移方式 | `git mv` 一次提交 / 本分支删除副本 + 维护者补交 | 维护者补交 | 实测推送被 GitHub 拒（`refusing to allow a Personal Access Token to create or update workflow ... without workflow scope`），自动化账号无法伪造该权限 |
| 首行过期注释 | 完全零改动 / 改写注释 | 改写注释 | 保留会让已落地的工作流自身写着「需移动才生效」，与验收标准冲突；只动注释不动逻辑，风险为零 |
| 文档口径 | 直接宣称「已生效」 / 声明「待补交」 | 声明「待补交」 | 文件不存在时宣称已生效是假陈述：README 的相对链接会 404，读者会等一个永远不会触发的构建 |
| `ci/` 目录去留 | 删除整个目录 / 保留说明 | 保留 `ci/README.md` | 记录 `workflow` 权限限制与被拒原因，避免后人再建副本 |
| 回归守护 | 仅人工核对 / 加单测（缺文件时 skip） / 加单测（缺文件时断言口径） | 缺文件时断言口径 | skip 会让阻塞态在 CI 里完全静默；断言「文件缺失 ⇒ 文档不得称已生效」既保留红灯信号，又不会让本分支常红 |
| 线上验收 | coding 本地 / sre 线上 | sre 线上 | Pages 发布需真实仓库设置与公网访问，编码阶段无法验证 |

## 4. 测试 seam

新增 `tests/test_scripts.py::WorkflowLocationTest`，断言的是**仓库对外可观察的状态**而非实现细节：

1. `ci/github-pages-deploy.yml` 不存在（过渡副本已移除，路径唯一）；
2. **文件状态与文档口径一致**：文件缺失 → `README.md` / `ci/README.md` 必须含「待补交」、不得含
   「已生效 / 已启用 / 会自动构建并部署」，且 README 必须说明「推送不会触发」；文件存在 → 不得再称
   「待补交」。文件缺失时不得留下指向不存在文件的相对链接；
3. 工作流文件存在时保留触发条件（`push: branches: [main]`、`workflow_dispatch`）、`permissions`、
   `concurrency: pages` 与 `build`/`deploy` 双作业；文件缺失时该用例不 skip，而是复核文档已披露阻塞态。

先写测试（红，旧文档因宣称「已生效」而失败）→ 改文档与删除副本（绿）→ 维护者补交工作流后，
同一用例自动转为核对作业图，口径测试同时要求删掉「待补交」表述。

## 5. 验证命令

```bash
npm test                                   # 27 → 31 项 Python 用例（0 skipped）+ 6 项 node 用例

# 工作流补交后核对「迁移前后仅首行注释不同」（$DEL = 删除 ci/ 副本的那个提交）
DEL=$(git log --diff-filter=D -n1 --format=%H -- ci/github-pages-deploy.yml)
git show "$DEL^:ci/github-pages-deploy.yml" | diff - .github/workflows/deploy.yml
```

补交之前上述 `diff` 无法执行（目标文件不存在），此阶段由
`test_docs_state_matches_workflow_presence` 保证文档不宣称已生效。