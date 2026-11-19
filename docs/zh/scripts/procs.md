# 任务管理器 {#task-manager}

`procs` 打开并驱动任务管理器 block：实时进程、机器指标、扁平或树形排列、过滤与
进程选择。可用它捕获进程视图，或打开所选进程的菜单与退出确认。

## 打开 block {#opening-a-block}

| 命令 | 作用 |
| --- | --- |
| `procs open` | 在聚焦面板旁打开任务管理器 block 并聚焦它。等待其首个显示出来的采样。 |

新 block 初始为按 CPU 排序的扁平列表，最繁忙的排在前面。它列出的是其面板所属主机
的进程，未必是窗口所在机器的进程。采样是实时的，在无头运行中也是如此；不存在
进程固定数据。

`open` 等待真实采样，受脚本的 20 秒超时限制，然后再等待 450 ms 后视为完成。本地
采样取决于平台支持；远程采样需要已连接且支持进程列表的主机。采样不可用时，`open`
可能一直等待直到超时。这些命令并非仅限无头运行；其脚本实现是原生的，而不是 Web
客户端。

`tern ctl state` 把 block 记录在 `task_manager_blocks.blocks[]` 中，含 `id` 与
`sampled`。其外层对象还报告 `paused`、`interval_ms` 与本地采样的 `seq`。当某台
机器的 block 在当前标签页中可见且更新未暂停时，该机器的采样器就会运行。

## 排列与过滤 {#arranging-and-filtering}

| 命令 | 作用 |
| --- | --- |
| `procs sort name\|pid\|user\|cpu\|memory\|gpu\|threads\|disk` | 按该列排序聚焦的任务管理器 block；重复选择当前列会反转顺序。 |
| `procs tree on\|off` | 把子进程嵌套在父进程下，或返回扁平列表。 |
| `procs filter ["<text>"]` | 设置过滤器；省略或文本为空则清除。 |

选择另一列时，name、PID 与 user 以升序开始；CPU、内存、GPU、线程与磁盘以降序
开始。在树形视图中，排序作用于同级进程。过滤不区分大小写地匹配名称、用户或
命令行；全数字的过滤器还会匹配 PID 的开头。

除 `open` 之外的所有命令都要求有聚焦的任务管理器 block，否则以
`no task-manager block has focus` 报错。缺少或未知的排序列与树形取值都是解析错误。
每条命令都等待 450 ms 后视为完成，而不等待新的采样。

每个 block 的状态字段为 `sort`、`descending`、`tree`、`filter` 与 `rows`（排列后
的行数）。排序与树形模式是会话级共享状态；过滤与选择属于当前窗口。

## 选择与操作 {#selecting-and-acting}

| 命令 | 作用 |
| --- | --- |
| `procs select ["<name>"]` | 只选择第一个显示出来且进程名完全匹配的行，并将其滚动到可见区域。 |
| `procs menu` | 为当前选择打开进程行菜单。 |
| `procs quit [force]` | 请求退出所选进程；`force` 则请求强制退出。 |

选择操作在当前排列后的行中搜索，因此过滤或折叠的树分支可能隐藏目标。没有采样时
会以 `no sample yet` 报错；没有精确匹配的名称时会以 `no row is called …` 报错。
省略名称会被当作空名称，而不是清除选择的请求。

`quit` 会打开确认框，而不是立即发送信号；没有选中进程时不做任何事。确认后的退出
会发送终止请求；强制退出会杀死目标。在 Windows 上，退出使用进程终止。对于远程
block，信号发往该主机。使用 harness 的 `dialog` 命令来应答确认框。这些命令等待
450 ms 后视为完成；它们不等待进程退出。

block 的 `selected` 状态字段包含已选中的 PID。菜单与待处理的确认框通过控制端点的
`menus` 与 `system` 命令检查，而不是额外的任务管理器字段。

解析器忽略 `open`、`sort`、`tree` 与 `menu` 之后的尾随单词。对于 `quit`，只有紧
跟在它之后且等于 `force` 的单词才会启用强制退出；换成其他单词仍解析为普通的退出。
`filter` 与 `select` 把其余所有单词作为文本消费，因此含空格的名称与过滤器要加引号。

## 示例 {#examples}

按内存排序的全标签页进程树，如同 `procs-tree` 基准场景：

```text
ready
procs open
zoom
procs tree on
procs sort memory
wait 2500
shot procs-tree
```

选择 Tern 的进程并显示其详情，如同 `procs` 基准场景。这要求显示出来的进程中有
名称完全为 `tern` 的一个：

```text
ready
procs open
wait 2500
procs select "tern"
wait 450
shot procs
```

额外的等待让实时采样得以累积；它们并不能让进程名、PID 或占用率变得确定。

## 另见 {#see-also}

- [脚本](index.md)：运行脚本、语法与时序。
- [Harness 命令](harness.md)：截图与确认对话框。
- [控制命令](control.md)：状态、菜单与系统检查。
- [Profile block](profile.md)：录制所选进程。
- [远程主机](remote.md)：附着到进程被列出的主机。
- [调试](../guides/debugging.md)：从脚本驱动窗口。
