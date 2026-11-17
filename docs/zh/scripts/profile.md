# Profile block {#profile-blocks}

`profile` 会把采样得到的调用栈以火焰图的形式打开，记录在任务管理器 block 中选定的进程，并操作该图及其函数表。要获得可复现的截图，可使用已记录的 fixture；要查看某个进程的时间花在哪里，可记录一个实时进程。

## 打开与记录 {#open-and-record}

| 命令 | 作用 |
| --- | --- |
| `profile fixture <name>` | 在聚焦面板旁的新 block 中打开名为 `<name>` 的已提交 profile。 |
| `profile open <path>` | 在当前 host 上，于新建的 profile block 中打开采样报告、折叠栈文件或 Chrome/V8 `.cpuprofile`。 |
| `profile record` | 打开一个新 block，记录聚焦任务管理器 block 中选定的进程。 |
| `profile stop` | 提前结束聚焦 profile block 的记录，并保留已有采样。 |

fixture 位于 `crates/tern/goldens/fixtures/profile`。名称省略扩展名：Tern 会先尝试 `<name>.sample.txt`，再尝试 `<name>.folded`。未知的 fixture 会使该命令失败。已发布版本参见 [fixture 设置](index.md#fixtures)。路径或名称中含空格时请加引号。

Chrome 与 V8 的 `.cpuprofile` 文件也会通过常规的文件打开途径进入分析器，包括 Files 面板、`tern open` 以及系统的“打开方式”操作。远程 host 上的文件会在其所属 host 上读取。报告按钮会打开该 profile 的源码；导入的 profile 无法再次记录。存在时间差值时，火焰图与函数占比按经过时间加权；没有时间差值时，则显示采样计数。

`record` 要求有一个聚焦的任务管理器 block，且其中选定了一个进程；否则会失败。该 block 会在那个任务管理器所在的 host 上打开。记录最多持续 20 秒实际时间。它在开始后等待稳定 1,500 毫秒，而不是等待整段记录结束。采样使用平台自带的记录器：macOS 上为 `sample`，Linux 上为 `perf`，Windows 上为原生采样器。权限与可用的采样工具可能阻止记录。如果 Tern 没有可用于保存记录的缓存目录，它会显示提示条而不是打开 block。

`fixture`、`open` 与 `stop` 会等待聚焦 block 显示出火焰图或错误，然后稳定等待 400 毫秒。真实工作的等待在 20 秒后超时并失败。block 中显示的文件或记录错误会使等待结束；这本身不算命令失败。`stop` 要求有聚焦的 profile block，但记录已经结束时无需调用。

这些命令在无头运行与原生窗口中都可用；Web 客户端不运行脚本。profile block 与 file block 一样，通过其 host 的文件中枢读取文件，因此在浏览器标签页中可以看到由所在机器上的桌面窗口记录的 profile 火焰图。超过 256 MiB 的文件会显示错误，而不是火焰图。

桌面窗口自行对本机的进程采样。其他 host 上的进程（远程 host 的进程，或在浏览器标签页中查看时由服务端机器承载的进程）由该 host 的会话守护进程采样，该守护进程会把 profile 写入自己的缓存。记录属于守护进程：它会跨链接断开、标签页重新加载与窗口关闭继续进行，显示该 block 的每个窗口都会跟随它，并且都可以停止它。若 host 上运行的 Tern 版本过旧、无法记录 profile，打开该 block 时会附带升级提示；若守护进程在记录完成前重启，则显示为已中断。

## 导航与高亮 {#navigate-and-highlight}

| 命令 | 作用 |
| --- | --- |
| `profile zoom <function>\|root` | 放大到该函数最重的方块；`root` 显示整个 profile。 |
| `profile select <function>` | 显示并选中该函数最重的方块。 |
| `profile hover <function>` | 显示该函数最重的方块，并把指针移到其上。 |
| `profile pick <function>\|none` | 高亮该函数的所有调用；`none` 清除已选取的函数。 |
| `profile find [<text>]` | 搜索 profile 并高亮匹配的函数；不提供文本或提供 `""` 会清除搜索。 |

这些命令作用于聚焦的 profile block，下文所有显示类命令也是如此。没有聚焦的 profile block 时它们会失败。函数查找要求火焰图已加载。查找会先尝试完整函数名，再尝试其缩短名称，最后尝试包含所给文本的名称。有多个匹配时，选择总采样数最大的那个。未匹配到函数，或函数在 `zoom`、`select`、`hover` 中没有对应图方块时，命令失败。函数名中含空格时请加引号。

搜索文本以小写形式保存。`pick` 高亮所有调用，而 `select` 与 `hover` 只针对一个方块。`root` 与 `none` 为其各自命令的保留值。每条命令都会稳定等待 400 毫秒。

## 显示与函数表 {#display-and-functions-sheet}

| 命令 | 作用 |
| --- | --- |
| `profile invert on\|off` | 显示自下而上的栈（`on`）或自上而下的栈（`off`）。 |
| `profile idle on\|off` | 显示或隐藏处于空闲等待状态的采样。 |
| `profile thread <name>\|all` | 显示某个指定线程，或显示所有线程。 |
| `profile sort self\|total` | 按自身时间或总时间排序函数表。 |

新建 block 默认自上而下、隐藏空闲采样、显示所有线程、搜索为空，函数表按自身时间排序。线程名必须完全匹配；未知线程会失败。`all` 恢复显示所有线程。开关只接受 `on` 或 `off`；排序只接受 `self` 或 `total`。这些命令都会稳定等待 400 毫秒。

## 状态 {#state}

`tern ctl state` 会在 `profile_blocks.blocks` 中报告 profile block。每个条目包含 `id`、`process`、`pid` 与 `show`。后者可能为 `blank`、`sampling`、`reading`、`elsewhere`、`interrupted`、`failed` 或 `ready`。在打开或停止记录之后应检查它，因为显示了失败同样会结束那些命令的等待。

图相关命令会更新 `focus`（缩放）、`selected`、`picked` 与 `query`。`focus` 在根层级为 null。显示相关命令会更新 `inverted`、`show_idle`、`thread`（全部线程时为 null）与 `sort`。条目还会报告 `samples`、`hidden`、`nodes`、`depth`、`threads`、`span`、`functions` 与 `side`。`weight_unit` 为 `samples` 或 `microseconds`：`samples` 与 `hidden` 中的权重即以此为单位。

## 示例 {#examples}

打开已提交的 Tern profile，放大到其样式刷新处，并显示某个匹配函数的悬停卡片：

```text
ready
profile fixture tern
zoom
profile zoom "<stencil_ui::tree::Document>::flush"
profile find "stencil_ui::style"
profile hover "stencil_ui::style::visit_children"
wait 300
shot profile-zoom
```

记录任务管理器 block 中选定的 Tern 进程，然后提前停止：

```text
ready
procs open
wait 2500
procs select "tern"
profile record
shot profile-record
profile stop
shot profile-recorded
```

## 参见 {#see-also}

- [任务管理器](procs.md)：选择要记录的进程。
- [终端与面板](terminal.md)：面板聚焦与面板缩放。
- [Harness 命令](harness.md)：指针输入与截图。
- [脚本](index.md)：语法、时序与 fixture 设置。
- [调试](../guides/debugging.md)：驱动正在运行的窗口。
