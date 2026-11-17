# 文件面板 {#files-pane}

`files` 驱动 Tern 各 block 旁的目录树：它的根目录、已展开的文件夹、选中项、过滤器
与实时更新。可以用它浏览真实文件夹，或把面板置入可复现的状态，以便截图、观察加载
状态以及测量大树。

## 面板与根目录 {#pane-and-root}

| 命令 | 作用 |
| --- | --- |
| `files show` | 打开文件面板。 |
| `files hide` | 关闭文件面板。 |
| `files toggle` | 在打开与关闭之间切换面板。 |
| `files focus` | 把键盘焦点交给文件面板。 |
| `files root <path>` | 打开面板，并把当前标签页的根目录固定为某个本地路径。 |
| `files follow` | 移除当前标签页的固定设置，使根目录重新跟随聚焦的 block。 |
| `files width <px>` | 以像素为单位设置面板宽度。 |

含空格的路径要加引号。`root` 不要求目录可读：根目录不可读或不存在时，会作为面板
错误显示，而不是让命令失败。宽度接受 0 到 65535 之间的整数；缺失或无效的值会导致
解析失败。固定设置按标签页生效。

除行列表与过滤器文本外，命令只使用列出的参数；其后的单词会被忽略。缺少必需的路径
会导致解析失败。

`tern ctl state` 会在 `files` 下报告这些变化：`shown`、`focused`、`width`、`root`、
`host`、`pinned` 与 `error`。没有根目录时，该条目只包含 `shown` 与 `root: null`。

## 行与过滤 {#rows-and-filtering}

| 命令 | 作用 |
| --- | --- |
| `files expand [<rel> …]` | 展开指定文件夹，包括列表尚未到达的祖先文件夹。 |
| `files collapse [<rel> …]` | 折叠指定文件夹。 |
| `files select [<rel> …]` | 用第一行替换当前选中项，随后把其余每一行切换加入或移出选中项。 |
| `files cursor [<rel> …]` | 依次单独选中每一个指定行；最后一个成为光标位置，也是唯一的选中项。 |
| `files reveal <rel>` | 打开面板，显示相对路径并聚焦这些行。 |
| `files filter [<query> …]` | 打开过滤器并设置其文本；无单词或 `""` 则清空。 |

路径相对于当前显示的根目录。`expand` 可以请求尚未列出的路径，并安排它们在列表到达
时展开。其他行命令在路径未列出时会失败；`select` 与 `cursor` 还会在行未显示时失败，
例如该行位于已折叠的文件夹中。非空的行操作需要根目录。接受空的参数列表，此时选中项
保持不变。选中类命令在选中任何内容时会聚焦这些行。

过滤器单词以空格连接，因此 `files filter "view rows"` 与 `files filter view rows`
设置的是同一个查询。

查看 `files.visible`、`rows` 和 `loaded` 可了解目录树，查看 `cursor` 和 `selected`
可了解选中情况。`visible` 最多包含 200 行，深度以缩进表示；`selected` 最多包含
64 条路径。`files.filter` 报告查询、匹配数、已索引数、完成标志与计时。`files.pool`
在存在行池时报告可见行范围、滚动位置与延后处理的工作。

## 生成的夹具与性能 {#generated-fixtures-and-performance}

这些夹具在临时目录中构建，不会读取源码树的 fixture 文件夹。每次构建都有独立的
目录。夹具会打开面板、修改聚焦 block 的工作目录，并在其有 shell 时向 shell 发送
`cd`。没有聚焦的 block 或构建夹具失败时，命令失败。固定的根目录仍然优先；必要时
先执行 `files follow`。若下一步需要 shell 提示符，随后使用 `ready`。

| 命令 | 作用 |
| --- | --- |
| `files fixture small` | 构建多种文件类型、点文件、紧凑的文件夹链，并在 Unix 上构建一个目录符号链接。 |
| `files fixture git` | 构建一个包含已修改、已暂存、未跟踪、冲突与被忽略文件的仓库，并固定提交日期。 |
| `files fixture wide` | 在 `wide` 中构建 10000 个文件，外加一个根目录 README。 |
| `files fixture deep` | 构建嵌套的紧凑链，以及适合三级吸顶表头堆叠的文件夹。 |
| `files fixture denied` | 构建小型目录树并加上 `locked/secret.txt`；在 Unix 上移除访问 `locked` 的权限。 |
| `files fixture empty` | 构建空目录。 |
| `files fixture synth [<n>]` | 构建平衡树，文件夹每层 32 个条目，文件之前最多三级文件夹。 |
| `files model <n>` | 用合成的已展开文件夹与文件替换根目录的内存列表，不写入磁盘。 |

`synth` 接受一个可选的非负计数。缺失或无法解析的计数会按 0 处理，而构建器至少使用
1。其他夹具名称也接受可选计数，但不使用它。未知夹具名称会导致失败。Git 夹具需要
可用的 `git` 可执行文件。denied 夹具的权限变更与 small 夹具的符号链接仅在 Unix 上
有效；权限相关失败取决于运行 Tern 的用户。

`model` 需要根目录和一个非负整数计数。它创建 `min(100, max(1, n))` 个名为
`dir000`、`dir001`……的文件夹，每个文件夹含 `n / folder-count` 个文件，向下取整。
文件每第七个使用 `.md`，其余使用 `.rs`。所有文件夹都会展开，选中项被清空；
0 会生成一个空文件夹。磁盘列表随后可以替换这棵合成树。

夹具结果会出现在 `files.root`、`repo`、`error`、`visible` 与 `loaded` 中。对于大树，
除 `rows` 与 `loaded` 外，还可查看 `files.mem`、`firstRowsMs`、`lastListMs`、
`status`、`filter` 与 `pool`。

## 磁盘变更与实时更新 {#disk-changes-and-live-updates}

| 命令 | 作用 |
| --- | --- |
| `files touch <rel>` | 创建父目录并写入空文件，已有文件会被截断。 |
| `files rm <rel>` | 删除文件或递归删除目录。 |
| `files storm <n>` | 在根目录下创建 `storm/f0` 到 `storm/f<n-1>`。 |
| `files hold` | 挂起列表应答，以保持加载状态可见。 |
| `files release` | 释放挂起的应答，并处理可用的回复。 |
| `files poll` | 从监视切换为轮询，显示 “Not live” 状态。 |
| `files watch` | 重新启用监视。 |
| `files wait` | 等待直到没有待处理的列表、状态、过滤器或操作工作。 |

**磁盘命令会改动当前根目录下的真实文件。** 测试这些命令时请使用生成的夹具。
它们需要根目录，并在文件系统出错时失败；`rm` 在路径不存在时失败。`storm` 接受非负
整数计数，且不会删除先前 storm 留下的文件。这些命令执行本地文件系统操作，即使面板
正在显示远程根目录；它们面向本地夹具。

命令会等到文件相关的工作完成，然后把脚本时间推进 350 ms。`touch` 与 `rm` 改用
600 ms；`storm` 使用 1000 ms。等待真实工作受脚本 20 秒超时的限制。被挂起的面板即使
仍有工作也算作已完成，因此 `files wait` 不会释放挂起的应答，也不会被它们阻塞。
`release` 恢复正常等待。这一组命令没有仅限桌面或仅限无头的限制。

`files.pending` 反映进行中的工作；挂起期间它可能保持为 true。`files.live` 反映是否
在监视。`events` 与 `relists` 统计监视事件与重新列表的次数，`lastListMs` 记录列表
耗时。挂起标志没有单独的状态字段。

## 示例 {#examples}

一个含嵌套文件夹并选中了某个已修改文件的 Git 夹具，与文件布局场景中所用的一致：

```text
ready
files fixture git
ready
files expand src src/view
files select src/view/rows.rs
files wait
shot files-git-selection
```

先是有匹配项的过滤器，随后是无匹配项的过滤器，来自文件过滤场景：

```text
ready
files fixture small
ready
files filter "vfr"
files wait
shot files-filter
files filter "zzqx"
files wait
shot files-filter-none
```

## 另见 {#see-also}

- [脚本](index.md)：语法、计时与运行脚本。
- [文件 block](file.md)：在 block 中打开与编辑文件。
- [远程主机](remote.md)：浏览已连接的主机。
- [Harness 命令](harness.md)：键盘输入与截图。
- [调试](../guides/debugging.md)：从脚本驱动窗口。
