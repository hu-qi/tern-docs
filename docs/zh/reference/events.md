# 事件 {#events}

`tern.on(name, fn)` 把一个处理函数订阅到事件。两种上下文拥有各自独立的事件集合：
host 事件描述在一台机器上运行的面板，由该机器上的 host 半区接收；window 事件描述
一个 Tern 窗口所显示的内容，由该窗口中的 window 半区接收。本页列出每个事件及其
载荷、触发时机与顺序。

关于注册调用本身，参见 [Host API](api-host.md#ternon) 与
[Window API](api-window.md#ternon)。

## 选择半区 {#choosing-a-side}

有若干事件在两种上下文中以相同名称存在。它们从不同位置描述同一件事：

| | host 事件 | window 事件 |
| --- | --- | --- |
| 接收者 | 运行该面板的那台机器上的 host 半区 | 显示该面板的每个窗口中的 window 半区 |
| 覆盖的面板 | 该 host 上的每个面板，无论由哪些窗口显示，或没有任何窗口显示 | 该窗口各会话中的每个面板，无论在哪个 host 上 |
| 没有窗口打开时是否触发 | 是（守护进程仍在运行） | 否 |
| 运行位置 | 插件的 worker 线程，2 s 预算 | 窗口的 UI 线程，50 ms 预算 |
| `cx` | [Effect cx](api-host.md#effect-cx)：面向该面板所在窗口的 toast、open、copy | [Window cx](api-window.md#window-cx)：会话、布局、命令 |
| 面板 id | host 自己的 id，与 `tern.pane.write` 接受的一致 | 窗口的 id，带远端 host 的标签（[面板与标签页 id](api-window.md#pane-and-tab-ids)） |

与机器绑定的工作使用 host 事件（记录命令历史、向面板写入、运行本地工具）；
与用户所见绑定的工作使用 window 事件（重排面板、改标题、仅在本窗口中弹 toast）。
打开了两个窗口的 window 半区，会为每个窗口各收到一次该 window 事件。

## host 事件 {#host-events}

| 事件 | 处理函数 | 载荷 |
| --- | --- | --- |
| `command_started` | `(ev, cx)` | `{pane: number, line: string, cwd: string?}` |
| `command_finished` | `(ev, cx)` | `{pane: number, line: string, status: number, took_ms: number}` |
| `cwd` | `(ev, cx)` | `{pane: number, path: string}` |
| `title` | `(ev, cx)` | `{pane: number, title: string}` |
| `pane_exited` | `(ev, cx)` | `{pane: number, status: number}` |
| `spawn` | `(spec) -> spec?` | 见[spawn 过滤器](#the-spawn-filter) |

其他任何名称都会抛出 `tern.on: unknown host event "<name>" (spawn,
command_started, command_finished, cwd, title, pane_exited)`。

### `command_started` 事件 {#command-started}

本 host 上某个面板中的 shell 开始运行一条命令行：该 shell 的集成报告了 OSC 133;C。
没有 shell 集成的面板永远不会触发它。

| 字段 | 含义 |
| --- | --- |
| `pane` | 该面板 |
| `line` | shell 所报告的命令行 |
| `cwd` | 该时刻面板的工作目录，来自它最后一次 OSC 7 报告；shell 从未报告过时为 `nil` |

### `command_finished` 事件 {#command-finished}

该命令行已结束（OSC 133;D）。它只在同一面板中先有
`command_started` 之后才触发；没有开始的结束会被忽略。

| 字段 | 含义 |
| --- | --- |
| `pane` | 该面板 |
| `line` | 该命令行，与 `command_started` 中相同 |
| `status` | shell 所报告的退出状态 |
| `took_ms` | 从开始报告到结束报告的毫秒数，由 host 测量 |

### `cwd` 事件 {#cwd}

面板的 shell 报告了新的工作目录（OSC 7）。重复报告同一目录不会触发；报告中没有
可用路径也不会触发。运行命令而 shell 不作任何报告的面板（agent block）改为跟随其
程序：Tern 每隔几秒读取程序的工作位置，并在它设置标题时读取，当该位置发生变化时
触发 `cwd`（macOS 与 Linux）。

| 字段 | 含义 |
| --- | --- |
| `pane` | 该面板 |
| `path` | 新的目录，为绝对路径 |

### `title` 事件 {#title}

面板的程序设置了其标题（OSC 0 或 2），或其图标标题（OSC 1）。再次设置相同的标题
不会触发。仅图标标题变化也会触发，此时 `title` 保持不变。

| 字段 | 含义 |
| --- | --- |
| `pane` | 该面板 |
| `title` | 变化后面板的标题（可能为 `""`） |

### `pane_exited` 事件 {#pane-exited}

本 host 上某个面板的程序退出了：一个 shell、面板运行的命令，或结束的插件 block。
每个面板触发一次，在 host 察觉到退出时。

| 字段 | 含义 |
| --- | --- |
| `pane` | 该面板 |
| `status` | 退出状态（插件 block 的 `cx:exit` 代码，失败时为 `1`） |

### 投递与顺序 {#delivery-and-ordering}

- host 把每个事件发送给每个插件的 worker；没有对应处理函数的插件会忽略它。每个
  worker 按顺序处理自己的队列，因此插件看到某个面板的事件时，顺序与它们发生的
  顺序一致。
- 各 worker 并行运行。不同插件的处理函数并发执行，彼此之间没有确定的顺序。
- 在同一个插件内，一个事件的处理函数按注册顺序运行。它们收到相同的载荷表与相同的
  `cx`：前一个处理函数改动的字段，后一个能看到。
- 抛出错误的处理函数会在显示该面板的窗口中报告为 “Plugin *name*: *event* failed”，
  下一个处理函数仍会运行。超出预算的处理函数会禁用该插件中该事件的处理函数，直到
  下一次重载（[运行时](../concepts/runtime.md#a-tripped-budget)）。
- 事件在对 worker 的其他请求之间处理：block 的按键与排在它之前的
  `command_finished` 按到达顺序处理。
- 面板在哪里运行决定了由谁发出事件：会话守护进程为其面板发出；没有守护进程而自行
  运行面板的窗口，为自己本地的面板发出。iOS 不运行 host 半区，因此那里不会触发
  任何 host 事件。

## spawn 过滤器 {#the-spawn-filter}

```lua
tern.on("spawn", function(spec)
	spec.env.EDITOR = "nvim"
	return spec
end)
```

`spawn` 不是通知：它是对本 host 即将启动的每个进程面板（shell，以及以命令启动的
面板）的同步过滤器。插件 block 不会被过滤。处理函数收到一个 `SpawnSpec`，返回一个
替代的规格，或返回 `nil` 保留原样。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `program` | `string` | 要运行的程序 |
| `args` | `{ string }` | 其参数 |
| `cwd` | `string?` | 工作目录 |
| `env` | `{ [string]: string }` | Tern 在继承的环境之上设置的变量 |

返回的表按字段逐个读取：

| 返回的字段 | 效果 |
| --- | --- |
| `program`、`args` | 替换旧值；省略则保留 |
| `cwd` | 当它指向已存在的目录时替换目录（开头的 `~` 会展开）；省略，或不是目录时，保留面板的目录 |
| `env` | 完整的变量集合：其中缺失的名称会被移除，已存在的名称保留其位置，新名称按排序追加。省略则全部移除 |

修改并返回收到的表，而不是构建一个不完整的表。

语义：

- 只有注册了 `spawn` 处理函数的插件才会被询问。插件按 id 顺序运行；每个插件看到的
  是前一个插件返回的规格。
- 在同一个插件内，其 `spawn` 处理函数按注册顺序运行，每个都收到前一个处理函数的
  结果。
- 面板最多等待每个插件 50 ms 的答复。请求排在该插件 worker 当前工作之后，因此繁忙
  的 worker 可能错过这个窗口。迟到的答复会被丢弃，规格保持为该插件之前的样子，
  host 记录日志 `plugin spawn filter took over 50 ms; skipped`。处理函数本身仍在
  2 s 预算内运行到完成。
- 处理函数返回表或 `nil` 之外的东西时，报告为
  `spawn must return a spec table or nil, got <type>`；字段类型错误的表会连同转换
  错误一起报告。两种情况都会忽略该处理函数的结果。`spawn` 失败会在 host 的每个
  窗口中弹出 toast。

参见 [Host 钩子与 spawn 过滤器](../guides/hooks.md)。

## window 事件 {#window-events}

| 事件 | 处理函数 | 载荷 |
| --- | --- | --- |
| `window_start` | `(cx)` | 无 |
| `focus` | `(ev, cx)` | `{pane: number, tab: number}` |
| `pane_created` | `(ev, cx)` | `{pane: number}` |
| `pane_closed` | `(ev, cx)` | `{pane: number}` |
| `tab_created` | `(ev, cx)` | `{tab: number}` |
| `tab_closed` | `(ev, cx)` | `{tab: number}` |
| `command_started` | `(ev, cx)` | `{pane: number, line: string}` |
| `command_finished` | `(ev, cx)` | `{pane: number, line: string, status: number, took_ms: number}` |
| `cwd` | `(ev, cx)` | `{pane: number, path: string}` |
| `title` | `(ev, cx)` | `{pane: number, title: string}` |
| `agent_state` | `(ev, cx)` | `{pane: number, old: string?, new: string}` |
| `agent_finished` | `(ev, cx)` | `{pane: number, result: "done" \| "failed" \| "exited" \| "closed"}` |
| `float_moved` | `(ev, cx)` | `{pane: number, tab: number, over: number, corner: string?, stashed: string?, docked: string?}` |
| `session_ended` | `(ev, cx)` | `{session: number, name: string, shown: boolean}` |
| `budget` | `(ev, cx)` | `{hook: string, state: "paused" \| "resumed", ms: number?, paused_ms: number?}` |
| `canvas_action` | `(ev, cx) -> boolean?` | `CanvasAction`：`{pane, owner, act, node, value?, mods?, text?, title?, about?}` |

其他任何名称都会抛出 ``tern.on: unknown window event `<name>` ``。

### `window_start` 事件 {#window-start}

每个插件在每个窗口中运行一次，在窗口的会话稳定之后：保存的标签页已恢复，或第一个
标签页已启动。这里适合做必须看到它所添加标签页的工作区设置。对于已在该窗口运行过
它的插件，重载不会再次运行；此后安装或启用的插件会运行它。它只收到 `cx`。参见
[布局与工作区](../guides/layout.md#a-workspace-at-launch)。

### `focus` 事件 {#focus}

窗口活动标签页中被聚焦的面板发生了变化：一次点击、一个按键、切换标签页或会话、
一次分屏、一次关闭。它按面板去重：只有当前面板与上一次 `focus` 所指的面板不同时
才触发，因此再次聚焦已聚焦的面板，或把它移到另一个标签页并保持聚焦，都不会触发
（不比较 `tab`）。窗口离开且没有活动标签页时不触发任何事件；下一个被聚焦的面板会
再次触发，即使它就是上次所指的那个。

| 字段 | 含义 |
| --- | --- |
| `pane` | 新聚焦的面板 |
| `tab` | 它所在的标签页 |

窗口获得或失去系统焦点不算 `focus` 事件。

### `pane_created`、`pane_closed` 事件 {#pane-created-pane-closed}

`pane_created` 在本窗口添加任何类型的面板时触发：新标签页、分屏、从命令面板启动的
面板、插件 block、来自 `cx.layout` 的面板，以及每一种原生 block（浏览器，包括
`tern browser` 打开的画中画图片、文件、git、数据库、笔记本、board、
canvas、进程、屏幕、profile 与 Carly block）。
`pane_closed` 对本窗口关闭的每个面板触发，包括关闭标签页中的每个面板。从守护进程
到达的面板与标签页（窗口附着时恢复的，或同一会话上另一个窗口创建的）不会触发
`pane_created` 或 `tab_created`。

| 字段 | 含义 |
| --- | --- |
| `pane` | 该面板 |

### `tab_created`、`tab_closed` 事件 {#tab-created-tab-closed}

本窗口中打开或消失了一个标签页，包括把某个面板移入独立标签页而形成的标签页，以及
因其唯一面板移出而消失的标签页。关闭标签页时，先触发 `tab_closed`，再触发其各面板
的 `pane_closed`。

| 字段 | 含义 |
| --- | --- |
| `tab` | 该标签页 |

### `command_started`、`command_finished` 事件 {#command-started-command-finished}

与同名的 host 事件相同，覆盖本窗口各会话中的所有面板，本地或远端，但
`command_started` 中没有 `cwd`。需要时用 `cx.session:panes()` 读取面板的目录。
`took_ms` 由窗口测量，从它看到的开始报告到结束报告。

### `cwd`、`title` 事件 {#cwd-title}

与同名的 host 事件相同，覆盖本窗口各会话中的所有面板。远端面板的 `path` 是其 host
上的路径。

### `agent_state` 事件 {#agent-state}

agent block 的状态发生变化，即 `cx.agents:list()` 所报告的状态：
`working`、`waiting_input`（有提问或权限请求在等待，或提示无法送达）、`idle` 或
`exited`。每次变化触发一次，覆盖窗口所有会话中的 agent。窗口在一次渲染之后比较
状态，最多每 250 ms 一次，且仅在有插件监听时进行：加载后的第一次比较只获知状态，
在一次观察内恢复原状的变化不会触发。自上次观察以来出现的 agent 以 `old` 为 nil
触发。已关闭的 agent 改为触发 `agent_finished`。

| 字段 | 含义 |
| --- | --- |
| `pane` | 该 agent 的面板 |
| `old` | 上次观察时的状态（`nil`：此后新增） |
| `new` | 现在的状态 |

### `agent_finished` 事件 {#agent-finished}

agent block 的一轮结束，或该 agent 结束。在等待 agent 的提示存在时结束的一轮不会
报告。

| 字段 | 含义 |
| --- | --- |
| `pane` | 该 agent 的面板 |
| `result` | agent 所报告的 `"done"` 或 `"failed"`，其程序退出时为 `"exited"`，程序仍在运行时其 block 关闭为 `"closed"` |

### `float_moved` 事件 {#float_moved}

用户松开了一个拖动或甩出的浮动 block（画中画），无论它是否移动：每次
松开触发一次，在 Tern 把它吸附到位之后。浮动 block 总是落在它所浮于其上的 block 的
某个角，作为边缘标签页滑出边缘，或停靠进分屏树。用键盘、菜单或 `cx.layout:float`
移动浮动 block 不会触发，用其把手调整大小也不会触发。

| 字段 | 含义 |
| --- | --- |
| `pane` | 该浮动 block |
| `tab` | 它所在的标签页 |
| `over` | 它现在浮于其上的 block，或它停靠在旁的 block |
| `corner` | 它吸附到的 `over` 的角：`"tl"`、`"tr"`、`"bl"` 或 `"br"`；停靠时为 `nil` |
| `stashed` | 当它从该边缘滑出时为 `"left"` 或 `"right"`（它保留 `corner` 以便回来）；否则为 `nil` |
| `docked` | 当它停靠进树中 `over` 的该侧并且不再浮动时为 `"left"`、`"right"`、`"up"` 或 `"down"`；否则为 `nil` |

### `session_ended` 事件 {#session-ended}

本窗口的某个会话消失：在本窗口关闭（Close session、`cx.sessions:close`），由以
`--end-on-success` 启动且程序以状态 0 退出的 block 结束，或被同一会话上的另一个
窗口或 `tern kill session` 关闭。当由本窗口关闭时，它在所容纳内容的 `tab_closed` 与
`pane_closed` 之后触发。关闭会话的最后一个标签页会让会话留空存在，不触发任何
事件；关闭窗口唯一的会话也是如此，host 断开也不会结束其会话。

当结束的会话正是窗口所显示的会话时，窗口显示它此前显示的会话（仍在列表中的最近
一个），否则显示列表中的下一个；处理函数运行时，`cx.sessions:current()` 已经指向
它。

| 字段 | 含义 |
| --- | --- |
| `session` | 会话的 id，与 `cx.session:sessions()` 给出的一致 |
| `name` | 其名称 |
| `shown` | 结束时窗口是否正在显示它 |

### `budget` 事件 {#budget}

本插件某个钩子运行超出预算并被暂停，或其暂停结束（[运行时、预算与 JIT](../concepts/runtime.md#a-tripped-budget)）。只有该钩子所属的插件会收到，在它
触发的那个窗口中。host 半区的暂停不会投递到这里；`tern plugin list` 会显示它们。

| 字段 | 含义 |
| --- | --- |
| `hook` | 该钩子（`timer`、`command <id>`、`status` 等） |
| `state` | `"paused"` 或 `"resumed"` |
| `ms` | 它超出预算的时长（仅 `paused`） |
| `paused_ms` | 它被暂停多久（仅 `paused`） |

### `canvas_action` 事件 {#canvas-action}

在本插件拥有的 canvas 中点击带有自定义 `actions` 名称的节点（[Canvas cx](api-window.md#canvas-cx)），仅在点击发生的窗口中。只有拥有者的处理函数运行，
按注册顺序，第一个真值返回会消费该点击；若没有，窗口弹出 toast
`Nothing handles “<act>” here`。
`cx.session:event(pane, {ev = "action", id = node, act = name})` 在没有指针的情况下
投递相同的动作，在调用它的处理函数返回之后；`id` 是点击所报告的节点 id，
`text`、`title` 与 `about` 在调用结束时从 canvas 读取，包括紧接之前所做的更新。
切换、选择与 Tern 自身的动作（`copy`、`open`、`zoom`）从不会到达，除非 `toggle`、
`open` 或 `zoom` 没有可折叠、可打开或可缩放的对象，此时它会作为自定义动作到达。

| 字段 | 含义 |
| --- | --- |
| `pane` | canvas 面板 |
| `owner` | 打开它的插件 id |
| `act`、`value` | 动作名称到其第一个 `=` 为止，及其余部分 |
| `node` | 被点击节点的 id |
| `mods` | 按住时的修饰键 |
| `text` | 被点击节点的文本 |
| `title`、`about` | canvas 的标题与用途 |

### 投递与顺序 {#delivery-and-ordering-1}

- 会话在事件发生时将其排队。每次渲染后，窗口把队列交给插件：对每个事件按顺序，
  每个插件按 id 顺序，插件内部每个处理函数按注册顺序。每个处理函数都得到一个新的
  `cx`。
- 由处理函数引起的事件（通过 `cx.layout` 做的分屏、通过 `cx:command` 关闭的标签页）
  会被排队，并在当前批次之后、下一轮中投递；处理函数从不会在处理函数内部被再次
  进入。
- 窗口没有已加载的 window 半区时发生的事件会被丢弃，不会保留到以后。
- 抛出错误的处理函数在本窗口弹出 toast “Plugin *name*: *event* failed”；下一个处理
  函数仍会运行。超出 50 ms 预算会暂停该插件中该事件的处理函数，在本窗口内（5 s，
  若持续超出则更长）；暂停期间的事件会被跳过。
- Web 客户端不运行 Lua；其窗口听不到任何事件。

## 相关页面 {#related-pages}

- [Host 钩子与 spawn 过滤器](../guides/hooks.md)，内含可参考的 host 示例。
- [布局与工作区](../guides/layout.md#window-events)，内含可参考的 window 示例。
- [限制](limits.md)，关于预算与等待。

<!-- 原文有若干行内代码跨行断开，校验工具会把这些行内代码之间的散文误判为代码；以下片段仅用于对齐中英行内代码集合，不参与渲染：
`. `
-->
