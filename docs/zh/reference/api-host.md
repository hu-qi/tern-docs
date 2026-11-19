# Host 半区 API {#host-api}

host 上下文在每个插件的一个工作线程上运行 `host.luau`，该线程正是本机面板运行的位置：
在会话守护进程内部，或在没有守护进程为其面板提供服务时的某个窗口内部。它掌管插件
block、命令 lens、带 spawn 过滤器的 host 事件，以及向面板写入。每次进入它的调用都有
2 s 预算。工作线程所在的位置参见[架构](../concepts/architecture.md)，重载对运行中的
block 与 lens 有何影响参见[生命周期与重载](../concepts/lifecycle.md)。

处理函数通过 `cx` 发出的请求（渲染、保存、退出、frame、blob、toast、打开、复制），
以及通过 `tern.pane.write` 发出的请求，都会排队，并在处理函数返回后应用，因此不会有
处理函数在另一个处理函数内部运行。

## `tern.block.define` 定义 block {#ternblockdefine}

```lua
tern.block.define: (id: string, def: BlockDef<any>) -> ()
```

实现 block 类型 `id`，`plugin.toml` 必须在 `[[blocks]]` 表中声明它。block 的类型名为
`<plugin>.<id>`；其 surface 角色为 `plugin.<plugin>.<id>`。

| 参数 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `string` | 本插件某个 `[[blocks]]` 的 `id` |
| `def` | `BlockDef<S>` | 下文列出的处理函数 |

抛出：

- `tern.block.define: block "<id>" is not declared in plugin.toml`；
- ``tern.block.define: <id>: `init` must be a function``（`view` 同理）；
- `tern.block.define: <id>: unknown feature "<name>" (edit, undo)`。
- `tern.block.define: <id>: unknown font "<x>" (mono, sans)`。

用同一个 `id` 再次调用会替换此后启动的 block 的定义。清单中声明、但在入口结束时仍未
定义的 block 会使插件失败：
`block <id> is declared in plugin.toml but not defined with tern.block.define`。

### `BlockDef` 定义 {#blockdef}

```lua
type BlockDef<S> = {
	init: (cx: BlockCx, args: { string }, saved: any) -> S,
	view: (state: S, cx: BlockCx) -> BlockView,
	title: ((state: S) -> string?)?,
	key: ((state: S, key: Key, cx: BlockCx) -> boolean?)?,
	event: ((state: S, ev: UiEvent, cx: BlockCx) -> ())?,
	features: { "edit" | "undo" }?,
	font: ("sans" | "mono")?,
	resize: ((state: S, cols: number, rows: number, cx: BlockCx) -> ())?,
	save: ((state: S) -> any)?,
}

type BlockView = {
	main: Node?,
	dock: Node?,
	layer: Node?,
}
```

| 字段 | 必填 | 调用时机 | 钩子名称 |
| --- | --- | --- | --- |
| `init(cx, args, saved)` | 是 | block 启动时、重新加载后，以及守护进程重启后 | `<id>.init` |
| `view(state, cx)` | 是 | 每个处理函数之后，以及每次 `cx:render()` 之后 | `<id>.view` |
| `title(state)` | 否 | 每次 `view` 之后 | `<id>.title` |
| `key(state, key, cx)` | 否 | 每次按键与粘贴时；对没有改变任何内容的按键恰好返回 `false` | `<id>.key` |
| `event(state, ev, cx)` | 否 | 视图各节点产生的每个用户事件 | `<id>.event` |
| `resize(state, cols, rows, cx)` | 否 | 面板以单元格计的尺寸变化时（没有它时，block 仍会重新渲染） | `<id>.resize` |
| `save(state)` | 否 | 每个处理函数之后（`key` 返回 `false` 时除外），以及调用 `cx:save()` 时 | `<id>.save` |

`features` 不是处理函数：它列出 block 所应用的 surface 协议特性，并由其 hello 声明。
`"edit"` 会在 block 的 `editor` 与 `input` 字段中开启
[原生编辑](../elements/input.md#native-editing-edit-and-undo)（前提是“设置 › 终端 ›
原生输入框编辑”处于开启状态）：单击会放置光标，拖拽或 ⇧ 加方向键会选中文本，改动会以
`edit` 事件的形式送到 `event`。`"undo"` 会把 ⌃Z（macOS 上为 ⌘Z）作为 `undo` 事件
而非按键发送。没有 `features` 时，每个按键都会到达 `key`，而在获得焦点的字段中单击
不会有任何效果。

`font` 也不是处理函数：`"sans"` 让 block 的各区域以 UI 字体绘制（默认的 `"mono"`
则使用终端字体），作用与 TSP surface 的
[`font`](../protocol/surfaces.md#open-and-close) 相同。应用应当使用它；参见
[设计视图](../guides/design.md#typography)。

`init` 会收到：

- `args`：启动参数，字符串数组（来自路由决策、`cx:new_block`、`launch` 表，或用
  “打开方式”打开文件时传入的路径）；
- `saved`：`save` 上次返回的值，从 JSON 解码而来；新 block 为 `nil`。

`init` 的返回值即 block 的状态，会传给其他每个处理函数。请就地修改它；除 `init`
之外的处理函数的返回值都不会被保留（`key` 的返回值只决定是否跟随一次渲染）。

`init` 抛出异常会结束该 block：错误文本（含 traceback）打印在面板中，面板以状态 1
退出，并以 toast 报告失败。

**每个处理函数之后**（`init`、`key`（除非它恰好返回 `false`）、`event`、`resize`，
以及一次 `cx:render()`），工作线程会：

1. 调用 `view`，并将结果与上次发送的视图做 diff；
2. 有变化时发送一帧变更；
3. 调用 `title`，当返回的字符串与上次发送的不同时发送该标题（`nil` 保留当前标题；
   在收到任何标题之前，面板显示清单中的 `title`）；
4. 调用 `save`，仅当其 JSON 与上次存储的值不同时，才把结果与该面板一起存储。

抛出异常的处理函数会被报告，且只丢失那一次调用：其后的渲染与保存仍会执行。

没有 `resize` 处理函数的 block 在尺寸变化时执行第 1 至第 3 步（`cx.cols` 与
`cx.rows` 已变化，因此 `view` 可能采用不同的布局）；状态没有变化，所以 `save`
不会运行。有处理函数时，先运行该处理函数，然后运行全部四步。

按键没有改变任何内容时，`key` 恰好返回 `false`：工作线程跳过渲染与保存。其他任何
返回值（`true`、`nil`、无返回值）都会渲染并保存。若 `key` 改变了状态却返回
`false`，视图会一直陈旧到下一次渲染，因此只对 block 不使用的按键返回 `false`。
返回值不会改变按键路由：按键到达 block 的方式与到达任何面板程序的方式相同，窗口的
键位映射先取走它绑定的按键，其余每个按键都会送到 block，无论 `key` 是否处理它。

### 视图模型 {#view-model}

每次调用 `view` 都返回各区域的完整树：`main`（block 的区域）、`dock`（其下方的一条
横带）与 `layer`（其上方）。返回 `nil` 或省略某个区域，该处就什么都不显示。

区域的根节点是容器，不是被绘制的节点：只显示它的 `role` 属性（作为区域元素上的
`data-role` 设置）及其子节点。请给每个区域一个 `tern.ui.col` 或 `tern.ui.row`
根节点；`main = tern.ui.text(…)` 什么都不显示，`main = tern.ui.col({ tern.ui.text(…) })`
才会显示文本。

工作线程会为每个节点分配 id：顶层是区域名，之后是 `<parent id>.<key>`，其中 `key`
是节点的 `p.key`（字符串或数字），否则是它在同级节点中的索引（从 0 开始）。带 key
的节点保持其 id，Tern 在重排后仍保留它们的视图状态（滚动位置、焦点、折叠状态）。
不带 key 的节点按位置匹配。

| 两次视图之间的变化 | 发送的操作 |
| --- | --- |
| id 与类型相同，属性不同 | 对变化的属性发送 `set`；被移除的属性以 `null` 表示 |
| 文本类节点（`text`、`md`、`code`、`ansi`、`math`、`editor`、`input`、`shimmer`）的 `text` 以追加后缀的方式变长 | `text … append`，带上新增的后缀 |
| 文本类节点的 `text` 以其他方式变化 | `text … replace` |
| id 相同，类型不同 | 先 `del` 再 `add` |
| 子节点被移除、新增或重排 | `del`、在下一个同级节点之前 `add`、按 id 移动 |

大于 64 KiB 的帧会被分片发送。

无法读取的视图会被报告为 `<id>.view` 失败，屏幕上保留上一次的视图：

| 问题 | 消息 |
| --- | --- |
| 不是表，也不是 `nil` | `view: expected {main?, dock?, layer?}, got …` |
| 出现三个区域之外的键 | `view: unknown region "<k>" (main, dock or layer)` |
| 某个节点不是表 | `<id>: a node must be a table, got …` |
| 节点缺少字符串类型的 `k` | ``<id>: a node needs a string `k` `` |
| `p` 不是表 | ``<id>: `p` must be a table, got …`` |
| `c` 不是列表 | ``<id>: `c` must be a list, got …`` |
| 两个同级节点 key 相同 | `<id>: duplicate child key "<key>"` |

用 [`tern.ui`](ui.md) 构建节点。参见[构建视图](../guides/views.md)。

### `Key` 按键 {#key}

```lua
type Key = {
	name: string,
	text: string?,
	ctrl: boolean,
	alt: boolean,
	shift: boolean,
	meta: boolean,
}
```

| 字段 | 含义 |
| --- | --- |
| `name` | 按键：一个小写字符（`"a"`、`"+"`、`"é"`）、`"space"`，或下文列出的具名键 |
| `text` | 该键输入的文本（当它输入内容时），如 Shift+A 对应 `"A"`、空格对应 `" "`；具名键与多数组合键没有该字段 |
| `ctrl`, `alt`, `shift`, `meta` | 按住的修饰键；`meta` 在 macOS 上是 Cmd，其他平台是 Super |

具名键：`enter`、`tab`、`backspace`、`escape`、`space`、`up`、`down`、
`left`、`right`、`home`、`end`、`begin`、`page_up`、`page_down`、`insert`、
`delete`、`menu`、`f1` … `f35`、`caps_lock`、`scroll_lock`、`num_lock`、
`print_screen`、`pause`。小键盘按键会报告它们所代表的字符。

粘贴会作为一个按键到达：`name = "paste"`，`text` 为粘贴的文本，且没有修饰键。
按键释放、单独的修饰键按下以及媒体键都不会传递。

### `UiEvent` 用户事件 {#uievent}

```lua
type UiEvent = {
	ev: string,
	[string]: any,
}
```

来自 block 各节点的用户事件。只有以下 `ev` 值会到达 `event`；surface 协议的其他
流量（ack、尺寸变化、主题与可见性变化）不会到达：

| `ev` | 发送时机 | 字段 |
| --- | --- | --- |
| `action` | 带自定义名称的指针动作被触发（`p.actions = { click = "inc" }`）、`button` 被点击，或表格的按钮单元格或行菜单项被选中 | `id`、`act`、`value`、`item`（表格行）、`mods` |
| `select` | 节点的 `select` 动作被执行 | `id`、`item` |
| `activate` | 节点的 `activate` 动作被执行（双击、Enter） | `id`、`item` |
| `toggle` | 可折叠节点被展开或收起（Tern 在本地翻转其状态） | `id`、`key`、`collapsed` |
| `focus` | 单击请求把按键交给 `editor` 或 `input` | `id` |
| `edit` | 编辑器中的原生编辑 | `id`、`from`、`to`、`text`、`cursor`、`len` |
| `undo` | 原生编辑下的 ⌃Z（macOS 上为 ⌘Z） | `id` |

`id` 是工作线程分配的节点 id（`main.0.2`，或对以 `rows` 为 key 的子节点为
`main.rows`；参见[视图模型](#view-model)）。载荷即 surface 协议的载荷
（[输入与事件](../protocol/input.md#events)）。Tern 只向 hello 中列出 `edit` 特性的
程序发送 `edit`，只向列出 `undo` 的发送 `undo`：block 只有在其 `BlockDef` 中带上
`features = { "edit", "undo" }` 时才会收到它们。

<!-- 原文此行内代码跨行断开（`features` 与 `BlockDef` 之间），按原文保留片段：` in its ` -->

### 示例 {#example}

```lua
tern.block.define("counter", {
	init = function(_cx, args, saved)
		return { count = if saved then saved.count else tonumber(args[1]) or 0 }
	end,
	title = function(state)
		return "Counter " .. state.count
	end,
	view = function(state, _cx)
		local plus = tern.ui.badge("+", "accent")
		local p: { [string]: any } = plus.p or {}
		p.actions = { click = "inc" }
		plus.p = p
		return { main = tern.ui.col({
			tern.ui.text({ tern.ui.span("Count: ", "muted"), tern.ui.span(tostring(state.count), "strong") }),
			plus,
		}) }
	end,
	key = function(state, key, _cx)
		if key.text == "+" then
			state.count += 1
		end
		return nil
	end,
	event = function(state, ev, _cx)
		if ev.ev == "action" and ev.act == "inc" then
			state.count += 1
		end
	end,
	save = function(state)
		return { count = state.count }
	end,
})
```

```toml
[[blocks]]
id = "counter"
title = "Counter"
```

## block 的 cx {#block-cx}

```lua
declare extern type BlockCx extends EffectCx with
	pane: number
	cwd: string?
	cols: number
	rows: number
	function render(self): ()
	function save(self): ()
	function exit(self, code: number): ()
	function frame(self, ops: { any }): ()
	function blob(self, bytes: string, mime: string): string
end
```

每个运行中的 block 各有一个 `cx`，传给 `init`、`view`、`key`、`event` 与
`resize`。定时器与进程回调可以保留它，但保留它既不会让 block 保持存活，也不会在
block 结束时取消异步工作。

block 结束后，绑定到 block 的请求（`render`、`save`、`exit`、`frame` 与
`blob`）在应用时若该面板中没有运行中的 block，就会被忽略。`blob` 仍会计算并返回
其 id；但它不会为已结束的 block 存储该 blob。这些检查基于面板，而不是被保留上下文的
生命周期令牌。

effect 则不同：block 结束后，`toast`、`open` 与 `copy` 仍可转发给显示该面板的
窗口。它们不受 block 是否存活的约束。应在可能时取消异步生产者，并在对其回调采取行动
前检查存活状态，尤其是应用 effect 之前。没有 block 关闭回调；
`tern.pane.list()` 检查的写法参见
[后台更新](../guides/blocks.md#updating-in-the-background)。当自己的代码调用
`cx:exit()` 时，也要保持一个本地的停止标志，因为请求只有在处理函数返回后才会应用。

| 成员 | 行为 |
| --- | --- |
| `cx.pane` | 面板在其 host 上的 id |
| `cx.cwd` | block 启动时面板的工作目录，或 `nil` |
| `cx.cols`, `cx.rows` | 面板当前以单元格计的尺寸（在 `resize` 运行前更新） |
| `cx:render()` | 排队一次渲染：`view`、标题、`save`，与处理函数之后相同。在定时器、进程或 fetch 回调中改变状态后使用它 |
| `cx:save()` | 排队 `save`，若结果有变化则立即存储 |
| `cx:exit(code?)` | 以退出状态 `code`（默认 `0`）结束 block：其 surface 关闭，面板的程序已退出 |
| `cx:frame(ops)` | 把 `ops`（原始 surface 协议帧操作的列表）作为一帧发送。抛出 `cx:frame: ops must be a list` |
| `cx:blob(bytes, mime)` | 把 `bytes` 作为类型为 `mime` 的 blob 发送，并返回其 id（字节的 SHA-256，小写十六进制），供 `image` 节点的 `blob` 属性使用。在 Tern 的 blob 缓存保存这些字节期间，该 id 在其他 block 中以及重启后（保存在已保存状态中）仍然有效，因此 block 无需再次发送它们 |
| `cx:toast`, `cx:open`, `cx:copy` | 与 [effect cx](#effect-cx) 上相同，作用于显示该面板的窗口 |

请求在当前处理函数返回后按顺序应用。若一次渲染又排队了另一次渲染，每个处理函数最多
重复 8 轮；超过后其余请求会被丢弃，并记录日志
`plugin keeps re-rendering; requests dropped`。

`cx:frame` 会绕过视图 diff：下一次渲染仍与上次 `view` 的结果做 diff，而不是与原始
操作所改变的内容比较。

```lua
init = function(cx, _args, _saved)
	local state = { lines = {} }
	tern.process.run({ "uptime" }, function(r)
		local live = false
		for _, pane in tern.pane.list() do
			if pane.pane == cx.pane then
				live = true
				break
			end
		end
		if not live then
			return
		end
		table.insert(state.lines, r.stdout)
		cx:render()
	end)
	return state
end,
```

## `tern.lens.define` 定义 lens {#ternlensdefine}

```lua
tern.lens.define: (id: string, def: LensDef<any>) -> ()
```

实现命令 lens `id`，`plugin.toml` 必须在 `[[lenses]]` 表中连同其 `match` glob
一起声明它。lens id 为 `plugin.<plugin>.<id>`，其 block 的角色为
`lens.plugin.<plugin>.<id>`。

| 参数 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `string` | 本插件某个 `[[lenses]]` 的 `id` |
| `def` | `LensDef<S>` | 下文列出的处理函数 |

抛出：

- `tern.lens.define: lens "<id>" is not declared in plugin.toml`；
- ``tern.lens.define: <id>: `open` must be a function``（`line`、`finish`、
  `view` 同理）。

清单中声明、但在入口结束时仍未定义的 lens 会使插件失败：
`lens <id> is declared in plugin.toml but not defined with tern.lens.define`。

### `LensDef` 定义 {#lensdef}

```lua
type LensDef<S> = {
	open: (run: LensRun, cx: EffectCx) -> S,
	line: (state: S, l: LensLine) -> (),
	finish: (state: S, status: number) -> (),
	view: (state: S) -> Node?,
	event: ((state: S, ev: UiEvent, cx: EffectCx) -> ())?,
}
```

| 字段 | 必填 | 调用时机 | 钩子名称 |
| --- | --- | --- | --- |
| `open(run, cx)` | 是 | 被认领的命令启动时；返回状态 | `<id>.open` |
| `line(state, l)` | 是 | 每行输出 | `<id>.line` |
| `finish(state, status)` | 是 | 命令结束时，带上其退出状态 | `<id>.finish` |
| `view(state)` | 是 | 输出到达期间（合并调用）、结束时、每个 `event` 之后 | `<id>.view` |
| `event(state, ev, cx)` | 否 | lens block 的视图产生的用户事件 | `<id>.event` |

命令是否获得该 lens，仅由清单的 `match` glob 决定，且在任何 Lua 运行之前就已确定，
因此 `open` 无法拒绝：模式一旦匹配，block 就已存在。应改为收窄 `match`。认领顺序
参见[命令 lens](../guides/lenses.md)与[清单参考](manifest.md#lenses)。

`view` 返回 `nil` 时，block 保持显示命令的原始输出；返回节点则用原生视图替换它。
命令运行期间，每个 block 的 `view` 最多每 250 ms 运行一次（仅在上次视图之后有行
到达时），然后在结束时运行一次。若 `open` 抛出异常，该捕获就没有状态，block 保持
其原始输出。

`finish` 总会收到数字形式的退出状态。未经 `finish` 就结束的捕获（中止、面板关闭）
不会收到 `finish`；其状态被丢弃。

### `LensRun` 命令信息 {#lensrun}

```lua
type LensRun = {
	line: string,
	typed: string,
	cwd: string?,
	program: string,
	args: { string },
}
```

| 字段 | 含义 |
| --- | --- |
| `line` | shell 报告的命令行（别名已展开），否则为键入的内容 |
| `typed` | 键入时的行 |
| `cwd` | shell 的工作目录（已知时） |
| `program` | 去掉目录后的程序名，已剥离包装程序（`sudo`、`doas`、`exec`、`time`、`nice`、`nohup`、`env`、`command`、`builtin`、`caffeinate`、`npx`、`bunx`、`pnpx`、`uvx`、`pipx`）与 `VAR=value` 前缀 |
| `args` | 其参数，已去引号、移除重定向 |

### `LensLine` 输出行 {#lensline}

```lua
type LensLine = {
	text: string,
	links: { LensLink },
}

type LensLink = {
	from: number,
	to: number,
	href: string,
}
```

| 字段 | 含义 |
| --- | --- |
| `text` | 该行的文本，不含转义序列 |
| `links` | 终端在该行找到的链接 |
| `links[i].from`, `links[i].to` | 链接在 `text` 中的首字节与末字节，从 1 开始且包含两端（`string.sub(l.text, link.from, link.to)`） |
| `links[i].href` | 链接目标 |

### lens 状态与重建 {#lens-state-and-rehydration}

工作线程为每个插件保留最近 256 次捕获的状态；超过后先丢弃已完成的捕获，并优先丢弃
最久未使用的。状态已不存在的 lens block（被丢弃，或因重载、守护进程重启而丢失）收到
用户事件时会重建状态：工作线程用插件的当前 `match` glob 匹配该 block 保存的命令行，
调用 `open`，把保存的原始输出按行送入 `line`（按其捕获时的宽度重新分行），命令已结束
则调用 `finish`，然后运行 `event`。若当前 glob 不再认领该行，事件会被丢弃。

### 示例 {#example-1}

```lua
tern.lens.define("grep", {
	open = function(run, _cx)
		return { cwd = run.cwd, rows = {} }
	end,
	line = function(state, l)
		local path, line = tern.parse.location(l.text)
		if path and line then
			table.insert(state.rows, {
				{ tern.ui.path(path, state.cwd), tern.ui.span(":" .. line) },
				{ tern.ui.span(l.text) },
			})
		end
	end,
	finish = function(_state, _status) end,
	view = function(state)
		if #state.rows == 0 then
			return nil
		end
		return tern.ui.table({
			{ id = "at", head = "Where" },
			{ id = "text", head = "Line", grow = 1 },
		}, state.rows)
	end,
})
```

```toml
[[lenses]]
id = "grep"
match = ["rg TODO*", "grep * TODO *"]
```

## effect cx {#effect-cx}

```lua
declare extern type EffectCx with
	function toast(self, level: ToastLevel, text: string, sub: string?): ()
	function open(self, target: string): ()
	function copy(self, text: string): ()
end
```

lens 的 `open`、`event` 以及 host 事件处理函数所使用的 `cx`。它的请求会发往相关
面板所在的窗口：该面板 window key 对应的每个窗口（实际上就是显示其会话的每个窗口）。
该 `cx` 只持有其目标，因此可以保留并稍后使用。

| 方法 | 行为 |
| --- | --- |
| `cx:toast(level, text, sub?)` | 显示一个 toast。`"success"` 为成功；`"error"`、`"warn"` 与 `"warning"` 显示为错误；其他任何级别显示为信息 |
| `cx:open(target)` | 在每个接收窗口中打开路径或 URL，行为等同于在面板中点击链接，因此该窗口的 `tern.route.link` 与 `tern.route.open` 处理函数会生效 |
| `cx:copy(text)` | 把 `text` 放入每个接收窗口的剪贴板 |

这些方法都不会抛出异常。没有窗口连接时，请求会被丢弃。

## `tern.on` 事件订阅 {#ternon}

```lua
tern.on: (name: string, fn: (...any) -> ...any) -> ()
```

把 `fn` 订阅到 host 事件 `name`。同一插件的处理函数按注册顺序运行；每个插件的
工作线程运行自己的处理函数，因此不同插件的处理函数并发运行，且顺序未定义。

| 事件 | 处理函数 | 载荷 |
| --- | --- | --- |
| `spawn` | `(spec: SpawnSpec) -> SpawnSpec?` | 见下文 |
| `command_started` | `(ev, cx: EffectCx)` | `{pane, line, cwd?}` |
| `command_finished` | `(ev, cx: EffectCx)` | `{pane, line, status, took_ms}` |
| `cwd` | `(ev, cx: EffectCx)` | `{pane, path}` |
| `title` | `(ev, cx: EffectCx)` | `{pane, title}` |
| `pane_exited` | `(ev, cx: EffectCx)` | `{pane, status}` |

抛出 `tern.on: unknown host event "<name>" (spawn, command_started,
command_finished, cwd, title, pane_exited)`。

每个处理函数的钩子名称即事件名。[事件](events.md#host-events)给出了每个事件的字段
与触发时机。

### spawn 过滤器 {#the-spawn-filter}

```lua
type SpawnSpec = {
	program: string,
	args: { string },
	cwd: string?,
	env: { [string]: string },
}
```

`spawn` 处理函数会在本机每个 shell 面板启动前同步运行（对插件 block 从不运行）。
它收到 spec，并返回一个替代使用的 spec，或返回 `nil` 表示不做更改。

| 字段 | 含义 |
| --- | --- |
| `program` | 要运行的程序 |
| `args` | 其参数 |
| `cwd` | 工作目录 |
| `env` | Tern 在继承环境之上设置的变量 |

返回的表会逐字段替换 spec：

- 缺少 `program` 或 `args`：保留原值；
- 缺少 `cwd`：过滤器不设置目录，面板仍在其本来的位置启动；不是目录的 `cwd` 会被
  忽略（守护进程会展开开头的 `~`）；
- `env`：结果中的 `env` 就是完整的变量集合。其中缺少的键会被移除；原先没有的键会被
  添加（按名称排序）。结果中没有 `env` 时会移除全部变量。

应修改收到的 spec 后返回，而不是返回一个新的部分表。

插件按 id 顺序运行，每个插件看到前一个插件的结果。面板为每个插件最多等待 50 ms；
较慢的插件的结果会被丢弃（面板照常启动），并记录日志
`plugin spawn filter took over 50 ms; skipped`。同一插件内的多个 `spawn` 处理函数
在该插件的 50 ms 内按注册顺序运行。

<!-- 原文此行内代码跨行断开（日志消息与 `spawn` 之间），按原文保留片段：`. Several ` -->

`spawn` 处理函数返回表或 `nil` 之外的内容时会被报告：
`spawn must return a spec table or nil, got <type>`。其失败会以 toast 形式发到
每个窗口。

```lua
tern.on("spawn", function(spec)
	spec.env.EDITOR = "nvim"
	return spec
end)
```

## `tern.pane` 面板 {#ternpane}

### `tern.pane.write` 写入 {#tern-pane-write}

```lua
tern.pane.write: (pane: number, text: string) -> ()
```

把 `text` 写入面板 `pane` 的 pty，如同键入。以 `"\r"` 结尾即可执行 shell 命令。
写入会排队，并在处理函数返回后应用；未知的面板会被忽略。面板不存在时不会抛出任何
异常。

```lua
tern.on("cwd", function(ev, _cx)
	if ev.path:match("/node_modules$") then
		tern.pane.write(ev.pane, "cd ..\r")
	end
end)
```

### `tern.pane.list` 列举 {#tern-pane-list}

```lua
tern.pane.list: () -> { PaneInfo }

type PaneInfo = {
	pane: number,
	cwd: string?,
	program: string,
	title: string,
	busy: boolean,
}
```

本机上程序尚未退出的每个面板，按其归属方最后一次报告的内容。block 自身的面板在其
`init` 运行前就已列入。

| 字段 | 含义 |
| --- | --- |
| `pane` | 本机上的面板 id（`tern.pane.write` 与事件载荷使用的 id） |
| `cwd` | 其工作目录 |
| `program` | 其程序名；插件 block 则为 block 类型名 |
| `title` | 其标题 |
| `busy` | shell 集成是否报告有命令正在运行；退出后为 `false` |

## 相关页面 {#related-pages}

- 逐步讲解参见 [block](../guides/blocks.md) 与[命令 lens](../guides/lenses.md)。
- [host 钩子与 spawn 过滤器](../guides/hooks.md)。
- [事件](events.md) 与[限制](limits.md)。

