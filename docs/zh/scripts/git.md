# Git block {#git-blocks}

`git` 命令驱动仓库的提交图、变更、diff Surface 与 Git 表单。可以用它们为 Git
界面截图布置状态，或从控制端点检查某个仓库。这些命令只在桌面版中运行，包括桌面的
无头运行；不受支持的平台会跳过它们并给出警告。

## 打开与等待 {#opening-and-waiting}

| 命令 | 作用 |
| --- | --- |
| `git open [fixture\|media\|"<dir>"]` | 打开包含某个目录的仓库，或打开一个生成的 fixture 仓库。当前标签页中若已有该仓库的 block，则聚焦该 block。 |
| `git wait` | 等待仓库、选中项详情与已打开文件完成加载。 |
| `git loading` | 清空仓库快照、清除其选中项并标记为未读，用于截取加载中的状态。 |

`git open` 的默认参数是 `fixture`。相对目录使用与其他 fixture 路径相同的解析
规则；目录必须属于某个 Git 仓库。仓库找不到或 fixture 无法构建时，打开会失败。

生成的仓库需要 Git 和一个可写的临时目录，而不使用 `crates/tern/goldens/fixtures`
中的文件。它们带有固定的身份与日期，并忽略用户的 Git 配置：

- `fixture` 构建 **orbit**：一个小型 Rust 库，已合并 `feature/lanes`，未合并
  `fix/long-subjects`，含标签 `v0.1.0` 与 `v0.2.0`、一个 `origin` 远程，`main`
  比 `origin/main` 多两个提交，另有一个 stash。`src/lib.rs` 已暂存，`src/graph.rs`
  有未暂存的改动，其中包含一个仅涉及格式的 hunk，`src/palette.rs` 未跟踪。
- `media` 构建 **brand-kit**，其中 `assets/badge.png` 与 `icons/mark.svg` 已改动，
  用于图像对比。

每个 fixture 在每个进程中只构建一次，存放于临时存储。同一进程中的脚本共享它；
其他进程会得到自己的副本。

除 `open` 外，每个命令都作用于聚焦的 Git block，或当前标签页中最新的可见 Git
block。没有这样的 block 时，命令以 `no git block (git open first)` 失败。

`open`、`wait`、选中、搜索、diff、context、偏好设置与提交 AI 面板都会等待真实的
仓库工作完成，随后再稳定 450 ms。它们在 20 秒后超时。加载包括选中项详情、语法
高亮与图像显示。仓库打开失败或文件加载失败也会结束等待：仅凭完成并不证明加载成功。
其他命令只稳定 450 ms，不等待仓库工作。

`tern ctl state` 把这一族命令暴露为 `git_blocks` 对象，而不是数组：
`git_blocks.blocks[]` 包含每个 block 的 `id`、`focused`、`repo`、`editor` 与
`media`。打开与加载可检查 `repo.path`、`repo.name`、`repo.ready`、`repo.head` 与
仓库计数；`repo.open.error` 报告打开文件的错误。仓库打开之前，`repo` 可以为 null。

## 提交图与选中 {#graph-and-selection}

| 命令 | 作用 |
| --- | --- |
| `git select wip` | 选中工作区，并显示文件面板的 Changes 标签页。 |
| `git select none` | 清除选中项。 |
| `git select <n>` | 选中提交图第 `n` 行并滚动到该行，行号从零开始。 |
| `git select <a>..<b>` | 选中两行提交图之间的范围。 |
| `git select "<rev>"` | 选中 `HEAD`、某个分支、某个标签、`stash@{n}`，或十六进制的提交 ID／前缀。 |
| `git search ["<query>"]` | 关闭已打开的文件，打开并聚焦提交图搜索，并设置其查询内容。省略查询则打开空白搜索。 |

行必须存在于已加载的提交图中。修订版本使用已加载仓库的分支、标签与 stash，而不接受
任意 Git 修订表达式。数字形式的词即使加了引号也按行号处理；十六进制 ID／前缀必须
至少含有一个字母才会被当作修订版本。行不存在或修订版本无法解析时命令失败。stash
只会被检查，而不会在提交图中定位。

状态在 `git_blocks.blocks[].repo.selection` 中反映这些命令（`kind` 为 `none`、
`wip` 或 `commits`，并带有提交 `ids`）以及 `repo.search`。选中工作区还会把
`git_blocks.files_tab` 改为 `changes`。

## diff 与文件 {#diffs-and-files}

| 命令 | 作用 |
| --- | --- |
| `git diff ["<path>"] [file\|history]` | 以 diff（默认）、整个文件（`file`）或其历史（`history`）的形式打开某个已改动文件。 |
| `git find ["<query>"]` | 在当前 diff 或整文件编辑器中打开查找并设置其查询内容；省略时使用空查询。 |
| `git pick <n>` | 选取前 `n` 个已改动的 diff 行。 |
| `git context more` | 展开当前 hunk 周围未改动的行。 |
| `git context all` | 展开所有未改动的行，或再次将其折叠。 |

没有路径时，`diff` 先选择工作区中第一个已改动的文件，再选择所选提交或范围中的第一个
文件。给出路径时，它按同样的优先级处理该确切的仓库相对路径。工作区中的文件会选中
工作区；未暂存的改动优先于已暂存的改动。`file` 与 `history` 是位于末尾的模式词，
不是单独的命令。

没有匹配的改动或所选提交中的文件时，`diff` 失败。`find` 需要有已打开的文件；`pick`
需要已加载的 diff；`context` 需要有已打开的 diff Surface。`n` 是非负整数：零不选取
任何行，大于已改动行数的数字则选取所有可用的已改动行。

检查 `git_blocks.blocks[].repo.open`：`path`、`scope`（`staged`、`unstaged`、
`commit:<id>` 或 `range`）、`mode`、`loaded`、`error` 与 `picked`。整文件编辑器与
图像对比的状态位于该 block 的 `editor` 与 `media` 中。diff 查找与已展开的上下文
没有专门的状态字段。

```text
ready
git open fixture
zoom
git diff "src/graph.rs"
git context more
shot git-context
```

## diff 偏好设置 {#diff-preferences}

| 命令 | 作用 |
| --- | --- |
| `git set split on\|off` | 切换并排 diff。 |
| `git set hunk on\|off` | 切换 hunk 视图。 |
| `git set wrap on\|off` | 切换自动换行。 |
| `git set tree on\|off` | 在树形与列表之间切换文件列表。 |
| `git whitespace exact\|ignore-space\|ignore-formatting` | 设置空白字符的比较方式。 |

这些命令改变的是窗口的 Git 偏好设置，而不只是所选文件，并且在普通窗口中会保存设置。
无头模式下不保存设置。它们仍然需要 Git block。`git_blocks` 没有专门的偏好设置字段；
可用 `tree` 或截图检查生成后的 Surface。

## 文件与 refs {#files-and-refs}

| 命令 | 作用 |
| --- | --- |
| `git tab files\|changes\|refs` | 显示文件面板的对应标签页。 |
| `git refs fold branches\|remotes\|tags\|stashes\|worktrees\|submodules` | 折叠 refs 的某个分区。 |
| `git refs unfold branches\|remotes\|tags\|stashes\|worktrees\|submodules` | 展开 refs 的某个分区。 |
| `git refs filter ["<text>"]` | 设置 refs 过滤器；省略则清除。 |

未知的标签页或分区是错误。状态把当前标签页暴露为 `git_blocks.files_tab`，把 refs
视图暴露为 `git_blocks.refs`。

## AI 面板示例 {#sample-ai-panels}

| 命令 | 作用 |
| --- | --- |
| `git ai explain` | 选中 `HEAD` 并显示一段预置的提交说明。 |
| `git ai message` | 选中 `HEAD` 并显示一条预置的建议提交消息。 |
| `git ai staging` | 选中工作区并显示正在运行的 AI 暂存横幅。 |
| `git ai staged` | 选中工作区并显示已完成的 AI 暂存横幅。 |

这些命令布置的是示例 UI，而不是真实的 AI 请求或暂存操作。`HEAD` 没有任何提交时，
`explain` 与 `message` 失败。`staging` 与 `staged` 还会显示 Changes 标签页。状态
反映选中项与 `git_blocks.files_tab`，但不暴露示例 AI 答案或横幅。

## 对话框、菜单与 peek {#dialogs-menus-and-peek}

| 命令 | 作用 |
| --- | --- |
| `git dialog branch\|rename\|tag\|message\|remote\|remote-url\|init\|clone\|patch\|stash\|confirm\|discard\|ai-stage` | 打开一个部分填充的示例 Git 表单。 |
| `git menu commit\|branch\|tag\|stash\|file\|rows` | 为所选提交（否则为 `HEAD`）、当前分支、第一个标签、最新的 stash、第一个已改动文件或已选取的 diff 行打开上下文菜单。 |
| `git peek` | 打开所选提交的 peek，没有时回退到 `HEAD`。 |

对话框表单不会提交任何操作。`branch` 刻意包含一个无效名称，以展示校验；`remote`
选中 GitHub，而 `remote-url` 使用一个 URL。未知的表单会失败，`git dialog open`
也包括在内。

目标缺失时菜单会失败：没有提交、`HEAD` 处于分离状态、没有标签、没有 stash、没有
已改动的文件或没有已选取的行。在 `git menu rows` 之前先使用 `git pick`。peek 要求
提交的提交图行已绘制且其内容已加载，否则失败。

状态把 `git_blocks.dialog` 与 `git_blocks.peek` 报告为布尔值。菜单通过
`tern ctl menus` 获取，而不是 `git_blocks` 中的专门字段。

```text
ready
git open media
zoom
git diff "assets/badge.png"
shot git-image
```

## 另见 {#see-also}

- [脚本](index.md)：语法、运行脚本与计时。
- [文件面板](files.md)：文件面板的各项控制。
- [偏好设置](prefs.md)：窗口设置。
- [控制命令](control.md)：状态、菜单与检查。
- [调试](../guides/debugging.md)：从脚本驱动窗口。
