# 翻译约定（Translation Guide）

本仓库的文档站点提供两个语言版本：

| 目录 | 语言 | 说明 |
| --- | --- | --- |
| `docs/` | English（默认语言） | 与上游 `https://docs.stencil.so/tern/` 逐页同步的原文 |
| `docs/zh/` | 简体中文 | 与 `docs/` 目录结构一一对应的译文 |

两边的**相对路径必须完全相同**（例如 `docs/concepts/runtime.md` 对应
`docs/zh/concepts/runtime.md`），页面内的相对链接因此无需改写就能在两种语言下工作。

## 翻译规则

1. **只译正文**：段落、列表项、表格单元格、标题、链接文字、图片替代文本。
2. **代码原样保留**：围栏代码块（包含缩进与空行）、行内代码、TOML/Luau/Shell/CSS
   片段一律逐字保留，不翻译、不改写、不重排。
3. **标识符不译**：API 名称、函数名、类型名、属性名、文件名、目录名、命令与参数
   （如 `tern.ui`、`plugin.toml`、`tern plugin link`、`--!strict`）保持原文。
4. **链接目标不变**：`[文字](路径.md#锚点)` 只翻译文字，路径与锚点原样保留。
5. **结构对齐**：标题层级与数量、代码块数量与顺序、列表层级、表格列数必须与原文一致，
   既不合并也不新增章节。
6. **术语统一**：按下表翻译；表中未列出的技术名词，首次出现时可保留英文并加简短中文说明，
   之后统一使用同一种写法。
7. **语气**：技术文档口吻，简洁、直述，不使用"我们"式的口语化表达，不添加原文没有的
   解释、示例或主观评价。

## 术语表

| English | 简体中文 |
| --- | --- |
| plugin | 插件 |
| manifest | 清单（`plugin.toml` 本身不译） |
| pane | 面板 |
| window | 窗口 |
| block | block（产品概念，保留英文；需要时写作 "block 类型"） |
| lens / command lens | lens（保留英文）；"command lens" 可写作 "命令 lens" |
| host half / window half | host 半区 / window 半区 |
| host hook | host 钩子 |
| surface / Surface Protocol | Surface / Surface 协议 |
| element | 元素 |
| view / view model | 视图 / 视图模型 |
| node | 节点 |
| style hook / stylesheet | 样式钩子 / 样式表 |
| theme | 主题 |
| chrome | chrome（指标签栏、标题栏、状态行等界面外壳） |
| command palette | 命令面板 |
| key bind / chord | 快捷键 / 组合键 |
| override | 覆盖 |
| route / routing | 路由 |
| spawn filter | spawn 过滤器 |
| session daemon | 会话守护进程 |
| headless | 无头 |
| viewport | 视口 |
| budget | 预算（指性能预算） |
| SDK / API | SDK / API（不译） |

## 校验

```bash
npm run docs:check    # 逐页核对：页面存在、标题结构、代码块、行内代码、链接目标
npm run docs:anchors  # 对齐中英标题锚点（中文标题镜像英文 {#id}）
npm run docs:assets   # 修正中文页面插图相对路径
npm run docs:normalize # 补全标题/插图块前后的空行（构建前自动执行）
npm run docs:build    # 构建全站
npm run docs:links    # 校验构建产物中的站内链接、锚点与插图
```

`docs:normalize` 与 `docs:assets` 会通过 `predocs:build` 在每次构建前自动执行，
它们只调整空白与插图路径，可重复运行且不会改动正文。

`docs:check` 会比对 `docs/` 与 `docs/zh/` 的每一页：标题层级序列一致、围栏代码块
逐字一致、原文的行内代码在译文中全部存在、链接目标列表一致。任一页不符合即返回非 0，
CI 在构建前就会拦住结构漂移的译文。

## 新增或更新译文

1. `npm run docs:fetch` 拉取上游最新英文页面并刷新 `site-map.json`（不会改动
   `docs/zh/`）。
2. 对新增或变更的英文页面，在 `docs/zh/` 的同路径下补译或同步修改。
3. `npm run docs:check` 通过后再提交；CI 会用同一检查守卫 `main` 分支的构建。
4. 尚未翻译的页面不会让中文站点缺页：构建前 `npm run docs:fallback` 会把缺失页面以
   英文原文复制到 `docs/zh/` 并加上 `<!-- fallback: english source -->` 与"尚未翻译"提示，
   保证全站页面始终可访问；补译后该标记随译文一起消失。