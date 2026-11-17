# Notebook Block {#notebook-blocks}

`notebook` 命令用于打开并编辑 Jupyter notebook、用真实内核运行其单元格，并驱动搜索、补全
与 notebook sheet。可以用它们演练 notebook 编辑，或捕获真实的执行结果。这些命令仅在桌面
版中可用，iOS 与 web 上不可用。

## 打开与选择 {#opening-and-selecting}

| 命令 | 作用 |
| --- | --- |
| `notebook fixture <name>` | 把 `<name>.ipynb` 从 notebook 夹具复制到临时文件夹，并在聚焦面板旁打开它。 |
| `notebook new` | 在一个全新的临时文件夹中创建 notebook。 |
| `notebook open <path>` | 以常规的打开位置打开已有 notebook。 |
| `notebook select <n>` | 单独选择单元格 `<n>` 并进入命令模式。 |
| `notebook edit` | 在活动单元格上进入编辑模式。 |
| `notebook command` | 返回命令模式。 |
| `notebook type <text>` | 在被编辑单元格的光标处插入文本；`\n` 会变为换行。 |

单元格编号从零开始。选择越界的单元格会失败，并报出该 notebook 的单元格数量。除非某个
单元格正在编辑，否则键入会失败。除打开类命令与 `wait` 之外，命令都要求有聚焦的 notebook
block；否则会以 `no notebook block has focus` 失败。

夹具来自 `crates/tern/goldens/fixtures/notebook`。每个夹具都会被全新复制，临时检查点会
被移除；编辑它不会改变已提交的夹具。缺失的夹具与文件系统错误会使命令失败。`new` 会重建
其进程专属的临时目录，因此它不是保留先前工作的办法。

打开类命令会等待 notebook 工作稳定，随后为绘制留出 300 ms 应用时间。在
`tern ctl state` → `notebook_blocks[]` 中检查 `path`、`phase`、`focused`、`mode`、
`active`、`selected` 与 `editing`。加载失败会体现在 `phase` 中；等待稳定本身并不代表加载
成功。notebook 未加载时，选择会失败。

## 编辑单元格 {#editing-cells}

| 命令 | 作用 |
| --- | --- |
| `notebook insert above\|below [code\|markdown\|raw]` | 在选区上方或下方插入单元格；默认类型为 `code`。 |
| `notebook kind code\|markdown\|raw` | 更改所选单元格的类型。 |
| `notebook delete` | 删除所选单元格。 |
| `notebook undo` | 撤销一次 notebook 编辑。 |
| `notebook redo` | 重做一次已撤销的 notebook 编辑。 |
| `notebook move up\|down` | 把所选单元格上移或下移。 |
| `notebook merge` | 合并所选单元格；只选中一个单元格时，把它与下一个单元格合并。 |
| `notebook split` | 在被编辑单元格的光标或选区边界处拆分；并继续编辑最后一部分。 |
| `notebook collapse input\|output` | 切换所选单元格的输入或输出可见性。 |
| `notebook clear [all]` | 清除所选单元格的输出；带 `all` 时清除所有单元格的输出。 |
| `notebook save` | 保存 notebook。 |

`split` 在编辑模式之外不做任何事。没有后续单元格的合并同样不做任何事。这些编辑命令等待
300 ms 应用时间即视为完成；它们不会等待内核执行结束。

检查 `notebook_blocks[].dirty`、`can_undo`、`can_redo` 与 `cells`。每个单元格报告其
`index`、`kind`、`source`（前 80 个字符）、`lines`、`edited`、`outputs`、
`input_hidden` 与 `output_hidden`。保存状态反映在 `dirty` 中。

## 执行与内核 {#execution-and-kernel}

| 命令 | 作用 |
| --- | --- |
| `notebook run [all\|<n>]` | 默认运行所选单元格；带 `all` 时运行所有单元格，或运行单元格 `<n>`。 |
| `notebook interrupt` | 中断内核。 |
| `notebook restart` | 不经确认提示重启内核。 |
| `notebook wait` | 等待每个 notebook 的加载、执行、内核启动以及待处理的 sheet 工作稳定。 |

执行使用真实内核及其已安装环境，而不是预置的输出。若该单元格不存在，`run <n>` 会失败。
`run`、`interrupt` 与 `restart` 在派发后只留出 300 ms 应用时间；在断言结果或截取已完成
输出的截图之前，请在其后接 `notebook wait`。

`wait` 不要求 notebook 聚焦。打开类命令使用相同的等待：它覆盖所有 notebook block，而不仅
是聚焦的那个，并在 20 秒真实时间后放弃。它不要求已启动内核，也不等待补全、工具提示或
Help 请求；那些请求由各自的命令负责。

状态暴露 `notebook_blocks[].python` 与 `kernel`，以及每个单元格的 `state`（`idle`、
`queued` 或 `running`）、`count`、`prompt`、`outputs` 与 `took_ms`。命令稳定完成并不
代表所执行的代码成功；请检查输出。

## 查找与替换 {#find-and-replace}

| 命令 | 作用 |
| --- | --- |
| `notebook find <text> [replace <text>]` | 打开 notebook 搜索，可选择性地设置其替换文本。 |
| `notebook find-next` | 移到下一个匹配项。 |
| `notebook find-previous` | 移到上一个匹配项。 |
| `notebook replace [all]` | 替换当前匹配项；带 `all` 时替换所有匹配项。 |
| `notebook find-close` | 关闭查找栏。 |
| `notebook find-option case\|word\|regex\|outputs` | 切换大小写敏感、全词匹配、正则表达式或搜索输出。 |

搜索文本与替换文本接受 `\n` 表示换行。它们各为一个词：含空格的文本需要加引号
（`notebook find "total population" replace count`）；`replace ""` 设置空替换。
选项是切换，而不是设定某个值。这些命令等待 300 ms 应用时间即视为完成。

`notebook_blocks` 中没有专用的查找栏字段。用可见的查找栏检查搜索状态；替换改动会出现在
`dirty` 与 `cells[].source` 中。

## Sheet 与内核辅助 {#sheets-and-kernel-assistance}

| 命令 | 作用 |
| --- | --- |
| `notebook sheet contents\|properties\|variables\|help\|none` | 显示某个 notebook sheet，或用 `none` 隐藏它。 |
| `notebook complete` | 在被编辑代码单元格的光标处请求内核补全，并等待应答。 |
| `notebook accept` | 接受已打开的补全列表中所选的条目。 |
| `notebook inspect` | 在被编辑的代码单元格中请求内核检查；重复执行会展开工具提示。 |
| `notebook help <name>` | 为某个名称打开 Help sheet，并等待内核帮助。 |

在 Tab 本应缩进的位置，`complete` 会失败：先编辑一个代码单元格，并让光标之前有文本。没有
打开补全列表时 `accept` 会失败。除非某个代码单元格正在编辑，否则 `inspect` 会失败。

`complete`、`inspect` 与 `help` 会等待所有 notebook 稳定，并等待待处理的补全、检查与 Help
请求结束，随后为绘制留出 300 ms 应用时间。它们的真实时间等待在 20 秒后失败。`sheet` 与
`accept` 只等待 300 ms 即视为完成；在打开 Variables 且其内核工作重要时，请在其后使用
`notebook wait`。

状态暴露 `notebook_blocks[].sheet`、`completion`、`tooltip` 与 `help`。

## 示例 {#examples}

运行已提交的执行夹具并捕获其结果，如 `notebook-run` 场景所示：

```text
size 1200 800
ready
notebook fixture run
zoom
notebook run all
notebook wait
shot notebook-run
```

搜索 tour 夹具，切换正则匹配，然后关闭搜索，使用 `notebook-find` 中的序列：

```text
ready
notebook fixture tour
zoom
notebook find df replace frame
notebook find-next
shot notebook-find
notebook find-option regex
notebook find (unclosed
shot notebook-find-regex
notebook find-option regex
notebook find-close
notebook select 0
notebook find kernel
shot notebook-find-markdown
```

## 另见 {#see-also}

- [脚本](index.md)：语法、夹具与计时。
- [Harness 命令](harness.md)：键盘输入与截图。
- [会话与 Block](sessions.md)：聚焦与排布 block。
- [调试](../guides/debugging.md#driving-a-window-from-a-script)：驱动正在运行的
  窗口。
