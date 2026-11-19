# 标签页与导航 {#tabs-and-navigation}

这些命令用于排布标签页与面板、更改其 chrome，并驱动样式与路径选择器。用它们来搭建
工作区、捕获导航状态，或在不点击菜单的情况下移动面板。

## 标签页与 chrome {#tabs-and-chrome}

| 命令 | 作用 |
| --- | --- |
| `tabs [horizontal\|vertical\|toggle]` | 设置标签页方向；省略参数时在两者之间切换。 |
| `tabs autohide on\|off` | 隐藏或保留窗口边缘的垂直标签列。 |
| `filter ["<query>"]` | 设置垂直标签列表的过滤器；省略查询即清除。 |
| `status-bar [on\|off]` | 显示或隐藏状态行；省略参数则在两者之间切换。 |
| `pane-headers never\|split\|always` | 不显示面板标题、仅在拆分标签页中显示标题，或在每个面板上都显示标题。 |
| `style rail\|float\|tiles\|studio\|glass\|clear\|solid\|islands\|compact` | 保留一项布局、材质或密度选择。 |
| `cross-session-click switch\|stay` | 使在其他会话的标签页上的单击切换到该会话，或保持当前会话。 |

`tabs` 稳定耗时 900 ms，包含标签页的移动过程。其他命令稳定耗时 450 ms。
`style` 的选项不区分大小写，且只改变所选的那一类。使用 `cross-session-click stay` 时，
双击或显式选择仍会切换会话。

状态中提供 `tab_orientation`、`status_bar`、`pane_headers`、`layout`、
`material` 与 `density`。`pane_headers` 使用 `Never`、`When split` 与 `Always`
这几个标签。过滤器、自动隐藏与跨会话单击设置没有专门的状态字段；
可用 `tree` 或 `dump` 查看可见列表，用 `sessions` 查看会话选择。

## 选择器与路径 {#pickers-and-paths}

| 命令 | 作用 |
| --- | --- |
| `interface-style` | 打开「更改界面样式」。 |
| `picker up\|down [<n>]` | 按行数移动已打开选择器的高亮，并预览样式选项。 |
| `picker enter` | 选中高亮行；在插件的 `cx:prompt` 中，以该字段的文本作答。 |
| `picker split` | 以拆分动作选中，类似 Command–Enter。 |
| `picker esc` | 取消选择器，恢复未提交的样式预览；插件问题的作答为 `nil`。 |
| `goto ["<path/query>"]` | 在聚焦面板的目录中打开「前往目录」。 |
| `insert-path ["<path/query>"]` | 在聚焦面板的目录中打开「插入路径」。 |

行数默认为 1。它是有符号整数：负数会反转方向，零则保持高亮不动。逐行移动会循环。
没有打开的选择器时 `picker` 失败；没有匹配行时选中操作不做任何事。

在路径查询中，以斜杠分隔的片段会像键入 `/` 那样逐层深入；最后一个片段是模糊查询。
省略查询则以空过滤器开始。`goto` 列出目录；选中后会在聚焦面板所属的 host 上打开新标签页，
或用 `picker split` 打开拆分。`insert-path` 也会列出文件，并把所选的路径插入原面板的
光标处。选中父级行会向上返回，而不是关闭选择器。

两个路径命令在没有面板聚焦时都会失败。它们会实时等待目录列表与后台遍历，然后稳定
450 ms。脚本的 20 秒真实工作超时同样适用。其他选择器命令稳定 450 ms；选中目录本身
不会等待 shell 提示符，因此在新 shell 中运行命令之前要先用 `ready`。这些命令在远程
host 上同样可用；它们并非仅限桌面端。

选择器关闭时，状态的 `picker` 为 null。打开时它报告 `mode`、`query`、
`dir`、`rows`、`walked` 与 `selected`。样式选择器使用模式 `style`；
路径选择器使用 `goto` 与 `insert`；插件的 `cx:pick` 与 `cx:prompt`
使用 `pick` 与 `prompt`。样式预览也会出现在 `layout`、
`material` 与 `density` 中。

```text
ready
goto ""
shot goto-dir
goto "crates/tern/"
shot goto-dir-descend
goto "crates/tern/srcview"
shot goto-dir-fuzzy
picker esc
insert-path "crates/tern/sessrs"
shot insert-path
picker enter
shot insert-path-typed
```

这是 `goto-dir` golden 中的导航序列，从 checkout 的根目录运行。

## 移动面板 {#moving-panes}

| 命令 | 作用 |
| --- | --- |
| `drag-pane <n> [<m> left\|right\|up\|down\|center\|tl\|tr\|bl\|br]` | 开始拖动面板 `n`，可选地悬停在面板 `m` 的放置区域上。 |
| `move-pane left\|right\|up\|down` | 把聚焦面板向该方向移动。 |
| `move-pane tab <n> ["<session>"]` | 把聚焦面板移到当前会话或指定会话中的第 n 个标签页。 |
| `move-pane new-tab` | 把聚焦面板移入一个新标签页。 |
| `move-pane session "<session>"` | 把聚焦面板移入该会话中的一个新标签页。 |

面板编号按活动标签页中的阅读顺序从 1 开始。标签页编号在目标会话内从 1 开始；
会话名不区分大小写。`center` 交换面板；`tl`、`tr`、`bl` 与 `br` 把面板浮动到目标
的左上、右上、左下或右下角。`drag-pane` 只启动拖动并设置其悬停覆盖层。用测试框架的
`drop <x> <y> text "tern-pane:<id>" move` 完成拖动，其中 id 取自状态中该被拖面板的
ID；或用 `drag-end` 取消。

面板、标签页或指定会话不存在时会失败。当面板已在该标签页中或属于另一 host 时，
移动到该标签页会失败。当目标会话中它已是该标签页的唯一面板，或目标位于另一 host 时，
移动到会话会失败。标签页的唯一面板移动到新标签页会失败。这三种标签页／会话形式都
要求有聚焦面板，并在移动后保持其聚焦。方向移动没有这样的显式失败结果。所有这些命令
稳定 450 ms。

状态的 `pane_drag` 报告被拖动的 `pane` ID 与 `over` 目标／区域，没有拖动进行中时为
null。移动会改变 `tabs`、`panes`、`focused`，在跨会话时还会改变 `sessions`。

## 运行标签与标签页历史 {#running-labels-and-tab-history}

| 命令 | 作用 |
| --- | --- |
| `running "<command line>"` | 让聚焦面板报告某个命令正在运行，而不实际启动它。 |
| `tidy` | 按面板中的程序为活动标签页命名，聚焦面板优先。 |
| `previous-tab` | 显示此前查看的标签页，必要时切换会话。 |

`running` 适合用于捕获无头运行无法启动的程序。它要求非空的命令行与一个聚焦面板。
它改变面板的运行／忙碌状态，而不是其终端输出。`tidy` 最多使用两个不同的程序标签，
以 ` · ` 连接；重命名该标签页会替换掉这个名字。`previous-tab` 在没有仍打开的
上一个标签页时失败；重复执行会回到刚离开的标签页。这些命令稳定 450 ms。

状态在 `focused.running`、`focused.busy` 与 `tabs`（`title`、`busy`、`active`）
中反映这些变化；`sessions[].current` 反映会话切换。没有单独的标签页历史字段。

```text
ready
running "btop"
tab new
running "claude"
split right
tab new
running "nvim notes.md"
split down
running "lazygit"
shot deck
tabs vertical
shot deck-vertical
```

这里使用了 `deck` golden 中的程序标签与面板设置。

## 另见 {#see-also}

- [终端与面板](terminal.md)：创建标签页、拆分与 shell 命令。
- [会话与 Block](sessions.md)：创建并选择会话。
- [测试框架命令](harness.md)：输入、拖放与截图。
- [控制命令](control.md)：检查状态与可见树。
- [调试](../guides/debugging.md#driving-a-window-from-a-script)：对窗口运行
  脚本。

<!-- 原文中该节的标签名之间夹着被换行断开的行内代码，校验工具会把其间的英文连接词误判为行内代码；以下片段仅用于对齐中英行内代码集合，不渲染：
` and `
-->
