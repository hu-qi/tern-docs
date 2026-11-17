# Block {#blocks}

插件 block 是一种面板，其程序就是你的 Lua 代码。它像 shell 一样存在于会话守护进程的面板
表中，因此每个窗口、iOS 应用与 Web 客户端都能显示它，且它在窗口关闭、插件重载与守护进程
重启后依然存在。本页介绍 block 如何定义、渲染，如何被按键、事件与后台工作驱动，如何保存
与恢复，以及如何打开。

## block 是什么 {#what-a-block-is}

block 类型在清单中声明，在 host 半区实现。每个运行中的 block 就是 host 上的一个面板，包含：

- **state**，即 `init` 返回的值，保存在插件的工作线程上；
- **视图**，即 `view` 返回的节点树，由工作线程做差异比较，并以 Surface 协议帧发送给面板；
- **保存值**，即 `save` 返回的内容，由守护进程与面板一同保存。

窗口不为 block 保留任何 Lua 代码。它们绘制面板发来的帧，并回传按键与指针事件，与对待任何
绘制原生 surface 的程序完全相同。这也是为什么在插件半区从未运行过的窗口（例如 Web
客户端）中，block 依然可用。

## 声明与定义 {#declaring-and-defining}

```toml
[[blocks]]
id = "list"
title = "Checklist"
```

block 的 kind 是 `<plugin>.<id>`，例如插件 `checklist` 的 `checklist.list`。`title` 用作
命令面板中 “New Checklist block” 一行的文字，并在你的 `title` 处理函数给出标题之前充当面板
标题。可选键 `icon`、`files` 与 `palette` 见[清单参考](../reference/manifest.md)。

`host.luau` 用 `tern.block.define(id, def)` 实现它：

| 字段 | 必填 | 调用时机 |
| --- | --- | --- |
| `init(cx, args, saved) -> state` | 是 | block 启动时，以及重载或守护进程重启后重新启动时 |
| `view(state, cx) -> {main?, dock?, layer?}` | 是 | 每次处理函数之后，以及每次 `cx:render()` 之后 |
| `title(state) -> string?` | 否 | 每次 `view` 之后 |
| `key(state, key, cx) -> boolean?` | 否 | 面板拥有焦点时的每次按键与粘贴；对没有改变任何内容的按键必须返回严格的 `false` |
| `event(state, ev, cx)` | 否 | 有人对视图的节点执行操作时 |
| `resize(state, cols, rows, cx)` | 否 | 面板的单元格尺寸变化时；没有它，block 会自行重新渲染 |
| `save(state) -> any` | 否 | 每次处理函数之后（返回 `false` 的 `key` 除外），以及调用 `cx:save()` 时 |

除处理函数外，定义还规定 block 如何绘制（用于原生编辑的 `features` 见
[Host API](../reference/api-host.md#blockdef)）：

| 字段 | 默认值 | 含义 |
| --- | --- | --- |
| `font` | `"mono"` | `"sans"` 会用 UI 字体绘制 block，与 Tern 自带应用一致，并通过 span token 与 `mono` 表格列让 id、路径和数字保持等宽（参见[设计视图](design.md#typography)与 [Surface](../protocol/surfaces.md#open-and-close)）。除 `"sans"` 或 `"mono"` 之外的值会在定义 block 时使插件失败：`tern.block.define: <id>: unknown font "<x>" (mono, sans)` |

声明了 block 但在 `host.luau` 加载结束时仍未定义，会使插件失败。每次调用都受 host 的 2 秒
预算限制。

## block 的 `cx` {#the-block-cx}

除 `title` 与 `save` 外，每个处理函数都会收到 block 的 `cx`。每个运行中的 block 各有一份，
因此定时器和进程回调可以持有它，但持有它既不能维持 block 存活，也不能取消后台工作。block
结束后，若该面板中没有 block 在运行，`render`、`save`、`exit`、`frame` 与 `blob` 请求在生效
时会被忽略（`blob` 仍返回其计算出的 id）。这些检查基于面板，而不是持有上下文的生命周期
令牌。`toast`、`open` 与 `copy` 不受 block 存活状态限制，block 结束后仍能影响窗口。

| 成员 | 含义 |
| --- | --- |
| `cx.pane` | 面板在其 host 上的 id |
| `cx.cwd` | block 启动时面板的工作目录，或 `nil` |
| `cx.cols`, `cx.rows` | 面板的单元格尺寸，在 `resize` 运行前更新 |
| `cx:render()` | 重新渲染：`view`、标题与 `save`，与处理函数之后相同 |
| `cx:save()` | 运行 `save`，若结果有变化则立即保存 |
| `cx:exit(code)` | 以退出状态 `code` 结束 block |
| `cx:frame(ops)` | 发送原始的 Surface 协议帧操作 |
| `cx:blob(bytes, mime)` | 发送字节（例如 `"image/png"`），并返回供 `image` 节点的 `blob` 属性使用的 blob id |
| `cx:toast(level, text, sub?)` | 在显示该面板的窗口中弹出 toast |
| `cx:open(target)` | 经由这些窗口的路由打开路径或 URL |
| `cx:copy(text)` | 复制到这些窗口的剪贴板 |

通过 `cx` 发出的请求会排队，并在当前处理函数返回后按顺序生效，因此不会有处理函数嵌套运行。

## 渲染周期 {#the-render-cycle}

你不需要自己发送视图。每次处理函数（`init`、返回非 `false` 的 `key`、`event`、`resize`）
之后，以及每次 `cx:render()` 之后，工作线程会：

1. 调用 `view`，并把结果与上次发送的视图做差异比较；
2. 若有变化，发送一帧包含这些变化的内容；
3. 调用 `title`，标题有变化则发送；
4. 调用 `save`，若其 JSON 有变化则保存结果。

没有 `resize` 处理函数的 block 在尺寸变化时执行第 1 到第 3 步：视图可以读取 `cx.cols` 与
`cx.rows`，但没有任何代码改动需要保存的 state。

所以模型是：在处理函数中改动 `state`，返回，视图随之更新。抛错的处理函数会丢掉本次调用，
以 toast 形式报告 “Plugin *name*: list.key failed”，其后的渲染仍会执行。抛错或返回格式错误
内容的 `view` 也会以同样方式报告，屏幕上保留最后一次正确的视图。

## 区域、节点 id 与键 {#regions-node-ids-and-keys}

`view` 最多返回三个区域：

| 区域 | 位置 |
| --- | --- |
| `main` | block 的区域 |
| `dock` | 其下方的条带 |
| `layer` | 覆盖其上的图层，用于表单与浮层。在其中绘制的内容会接收点击；其余部分把点击放行给 `main` |

省略的区域不显示任何内容。每个区域的根节点就是该区域本身：Tern 把它的子节点绘制到面板中，
并把根节点的 `role` 属性应用到区域元素上，但不绘制根节点自身的内容。请让每个区域的根节点
都是容器，例如 `ui.col({ … })`；只写 `main = ui.text(…)` 不会显示任何内容。

工作线程为每个节点命名，以便对视图做差异比较。区域的根节点以区域名命名（`main`），每个
子节点名为 `<parent id>.<key>`，其中 `key` 是子节点的 `p.key`（字符串或数字，若有），否则
是它在同级节点中从 0 开始的索引：

```text
main                 ui.col({ listing })
main.items           the list, p.key = "items"
main.items.i7        an item, p.key = "i7"
main.items.i3        an item, p.key = "i3"
dock.0               the dock's first child, unkeyed
```

在两个视图之间，id 与种类都相同的节点只收到发生变化的属性；文本以追加后缀方式变长的文本
节点会收到一次追加；种类变化会替换该节点；消失、出现或移动的子节点按 id 分别被删除、添加
和移动。

对于任何可能被重排、插入或删除的内容，键都很重要。不使用键时，列表的第三项始终是
`main.items.2`，无论它显示什么，因此删除第一项会让每个 id 都发生位移：每一行都会被重写，
Tern 的视图状态（滚动位置、焦点、某个分区的折叠状态）会留在旧位置上，而不是跟随该项。
若以稳定值（例如条目 id）作为键，行无论移动到何处都保持其 id 与视图状态，差异比较只会移动
它。两个同级节点使用相同的键是错误（`main.items: duplicate child key "i3"`），该视图会被
拒绝。

id 也是视图引用自身节点的方式：列表的 `selected` 属性保存选中项的 id，事件通过 `ev.id`
报告被操作的节点。

## 按键与粘贴 {#keys-and-paste}

当 block 的面板拥有焦点时，按键会像到达任何程序那样到达它：窗口的快捷键绑定先取走它们
绑定的键，其余所有按键交给 `key`：

```lua
key = { name = "j", text = "j", ctrl = false, alt = false, shift = false, meta = false }
```

`name` 是按键：小写字符（`"a"`、`"+"`）或具名键（`"enter"`、`"tab"`、`"backspace"`、
`"escape"`、`"space"`、`"up"`、`"down"`、`"left"`、`"right"`、`"home"`、`"end"`、
`"page_up"`、`"page_down"`、`"delete"`、`"f1"` 到 `"f35"` 等）。`text` 是该键输入的文本
（若它会输入内容）。`meta` 在 macOS 上对应 Cmd。完整列表见
[Host API](../reference/api-host.md#key)。

粘贴以一次调用到达，`name = "paste"`，`text` 保存粘贴的文本，其中包含换行。

`key` 的返回值决定是否随后渲染。按键没有改变任何内容时，返回严格的 `false`：工作线程会
跳过渲染与保存，因此 block 忽略的按键不产生 `view` 调用。其他任何返回值（`true`，或者完全
不返回）都会渲染并保存。处理函数若改动了 state 却返回 `false`，视图（以及保存的 state）
会滞后，直到有其他东西触发渲染，因此凡会改动内容的分支都应返回 `true`（或不返回），只对
确实不用的按键返回 `false`。返回值不会改变按键的路由：`key` 忽略的按键不会转发到其他地方。

面板尺寸变化时，`cx.cols` 与 `cx.rows` 随之改变，block 会重新渲染，因此按 `cx.cols` 布局的
`view` 无需 `resize` 处理函数即可跟随面板。若有 `resize` 处理函数，它先运行（以便按新尺寸
重新计算），随后 block 渲染并保存；没有它则只渲染。

## 来自视图的事件 {#events-from-the-view}

带 `actions` 属性的节点在被点击时发送事件。若在节点上设置
`p.actions = { click = "check=7" }`，`event` 会收到：

```lua
ev = { ev = "action", id = "main.items.i7", act = "check", value = "7" }
```

名称在第一个 `=` 处拆分为 `act` 与 `value`；若有修饰键，`mods` 会列出按住的修饰键。`event`
还会收到有相应请求的节点发出的 `select`、`activate` 与 `toggle` 事件，以及复选框和单选
按钮发出的 `change` 事件（[表单与控件](views.md#forms-and-controls)）。完整列表与内置动作
名称见[构建视图](views.md#actions-and-events)。

## 在后台更新 {#updating-in-the-background}

处理函数在 block 发生事件时运行。若想按自己的节奏更新视图（轮询、进程结束），可在定时器、
进程或 fetch 回调中改动 `state` 并调用 `cx:render()`。host 侧的定时器、进程与 fetch 回调
不会收到 `cx`，因此要在闭包中保留 `init` 得到的 block `cx`。

block 没有 “closed” 处理函数，因此后台工作必须自行察觉 block 已经消失。`tern.pane.list()`
列出 host 上程序尚未退出的面板，其中包含 block；发现 block 的面板不在列表中时就停止。
尽可能取消生产者，并在完成回调中再次检查，然后再更新 state 或发送效果。若你的代码用
`cx:exit()` 结束 block，还要在排队退出之前设置本地的停止标志：在处理函数返回之前，面板
列表不会反映已排队的请求。

下面的 block 每两秒把启动参数作为命令运行一次，并显示输出：

```lua
--!strict
local ui = tern.ui

type WatchState = { argv: { string }, out: string, status: number?, at: number }

local EVERY_MS = 2000

-- Whether pane `pane` still runs (a block that ended is gone from the list).
local function running(pane: number): boolean
	for _, p in tern.pane.list() do
		if p.pane == pane then
			return true
		end
	end
	return false
end

local watch: BlockDef<WatchState> = {
	init = function(cx, args, _saved)
		local state: WatchState = { argv = args, out = "", status = nil, at = 0 }
		local function tick()
			if not running(cx.pane) then
				return
			end
			tern.process.run(state.argv, { cwd = cx.cwd, timeout_ms = 10000 }, function(r)
				if not running(cx.pane) then
					return
				end
				state.out, state.status, state.at = r.stdout .. r.stderr, r.status, tern.now()
				cx:render()
				tern.timer(EVERY_MS, function()
					if running(cx.pane) then
						tick()
					end
				end)
			end)
		end
		if #args > 0 then
			tick()
		end
		return state
	end,
	title = function(state)
		return if #state.argv > 0 then "watch " .. table.concat(state.argv, " ") else nil
	end,
	view = function(state, _cx)
		if #state.argv == 0 then
			return { main = ui.col({ ui.text({ ui.span("Pass the command to run as arguments", "muted") }) }) }
		end
		return {
			main = ui.col({ ui.ansi(state.out) }),
			dock = ui.row({ ui.text({
				ui.span(if state.status == 0 then "ok" else "exit " .. tostring(state.status), if state.status == 0 then "success" else "error"),
				ui.span(" · every " .. EVERY_MS // 1000 .. "s", "muted"),
			}) }),
		}
	end,
}

tern.block.define("watch", watch)
```

存活检查在每次启动进程之前、在其完成回调中，以及在定时器安排下一次运行之前进行。block
自身的面板在 `init` 运行之前就已列入列表，因此 `init` 中的同一检查也能通过。进程本身运行在
线程池上，工作线程在此期间仍可处理按键和其他 block。重载会停止旧的工作线程（包括定时器），
block 新的 `init` 会重新启动循环。

## 保存与恢复 {#saving-and-restoring}

block 会在两种情况下重新启动：插件重载会把运行中的 block 迁移到新的工作线程，守护进程
重启则会随会话其余部分一起恢复它们。这两种情况都会再次调用 `init`，传入相同的 `args` 以及
`saved`（`save` 最后返回的值，已从 JSON 解码）。除此之外不会延续任何内容：旧运行的 state
表、定时器与进程都已消失，守护进程重启后 block 会从一个空白屏幕开始。

因此，任何需要延续的内容都要经过 `save`：

- `save` 返回可转为 JSON 的值：表、字符串、数字、布尔值、`tern.json.null`。它在每次处理
  函数之后运行；守护进程只在其 JSON 变化时才保存该值，因此返回相同的值开销很小。
- 可能为空的列表要用 `tern.json.array(t)` 包裹，否则空列表会被编码为 `{}`。解码后的数组
  会还原为 Lua 数组。
- 在 `init` 中，两者都存在时优先使用 `saved` 而不是 `args`；`args` 是启动参数，每次都会
  传入。
- 派生数据与临时数据（选中项、滚动位置、缓存）不要放进 `save`，或用默认值恢复它们。

抛错的 `init` 会结束 block：其错误会打印在面板中，面板以状态 1 退出。

## 打开 block {#opening-blocks}

| 来源 | 方式 | `args` | 位置 |
| --- | --- | --- | --- |
| 命令面板 | “New *title* block”，适用于当前 host 上 `palette` 不为 `false` 的每个 Ready block 类型 | 无 | 聚焦面板旁，或按命令面板的放置修饰键指定 |
| 文件菜单 | 文件面板与文件 block 菜单中的 “Open with *title*”，适用于 `files` glob 匹配该文件名的 block 类型 | `{ path }` | 聚焦面板旁，位于文件所在文件夹 |
| 路由 | `tern.route.open` 或 `tern.route.link` 返回 `{ block = "checklist.list", args = { … } }` | 按给定值 | 原本打开操作会去的位置 |
| window 处理函数 | 命令、绑定或事件中的 `cx:new_block("checklist.list", args?, how?)`；返回该面板 | 按给定值 | `how`，与 `cx:open` 相同 |
| 布局 | 作为 `cx.layout:new_tab`、`:split` 或工作区叶节点的 `launch` 使用的 `{ block = "checklist.list", args = { … } }` | 按给定值 | 该标签页或分屏 |

kind 写作 `<plugin>.<block>`，不带 `plugin.` 前缀。窗口必须在其 host 的目录中看到该 kind：
插件失败或被禁用的 host 上的 block 类型不会打开。参见[路由打开与链接](routing.md)与
[布局与工作区](layout.md)。

## 标题与退出 {#titles-and-exit}

`title(state)` 为面板命名（block 聚焦时也为标签页命名）。它在每次 `view` 之后运行；字符串
不同才会发送，`nil` 则保持当前标题。在任何标题之前，面板显示清单中的 `title`。

`cx:exit(code)` 结束 block：它从工作线程中移除，面板的程序视为以该状态退出，重载也不会重新
启动它。此后该面板的行为与任何程序已退出的面板相同。适用于会自行完成的 block，例如走完
最后一步的向导。

## 完整示例：一份清单 {#worked-example-a-checklist}

一份清单：从启动参数开始，把粘贴的行作为新条目，用 `j`/`k` 或方向键移动，用空格、回车或
点击切换状态，用 `d` 删除，并在重载与重启后依然保留内容。

`plugin.toml`：

```toml
schema = 1
id = "checklist"
name = "Checklist"
version = "0.1.0"
description = "A checklist pane that survives restarts."
host = "host.luau"

[[blocks]]
id = "list"
title = "Checklist"
```

`host.luau`：

```lua
--!strict
-- Block `checklist.list`: launch arguments become items; j/k (or the
-- arrows) move, space toggles, d deletes, pasted lines are added, clicks
-- toggle. Items keep their ids, so reorders and deletes keep view state.

local ui = tern.ui

type Entry = { id: number, text: string, done: boolean }
type State = { items: { Entry }, sel: number, seq: number }

local function add(state: State, text: string)
	local trimmed = string.match(text, "^%s*(.-)%s*$") or ""
	if trimmed ~= "" then
		state.seq += 1
		table.insert(state.items, { id = state.seq, text = trimmed, done = false })
	end
end

local function clickable(node: Node, act: string): Node
	local p: { [string]: any } = node.p or {}
	p.actions = { click = act }
	node.p = p
	return node
end

local function counts(state: State): (number, number)
	local done = 0
	for _, item in state.items do
		if item.done then
			done += 1
		end
	end
	return done, #state.items
end

local list: BlockDef<State> = {
	init = function(_cx, args, saved)
		if saved then
			return { items = saved.items or {}, sel = 1, seq = saved.seq or 0 }
		end
		local state: State = { items = {}, sel = 1, seq = 0 }
		for _, arg in args do
			add(state, arg)
		end
		return state
	end,

	title = function(state)
		local done, total = counts(state)
		return string.format("Checklist %d/%d", done, total)
	end,

	view = function(state, _cx)
		local rows: { Entry } = state.items
		local items = {}
		for i, item in rows do
			items[i] = {
				label = if item.done then { ui.span(item.text, "del muted") } else item.text,
				icon = if item.done then "check" else nil,
			}
		end
		local listing = ui.list(items)
		local children: { Node } = listing.c or {}
		for i, child in children do
			clickable(child, "check=" .. rows[i].id)
			local p: { [string]: any } = child.p or {}
			p.key = "i" .. rows[i].id
		end
		local current = rows[state.sel]
		listing.p = {
			key = "items",
			selected = if current then "main.items.i" .. current.id else nil,
			empty = { ui.span("Paste lines to add items", "muted") },
		}
		local done, total = counts(state)
		return {
			main = ui.col({ listing }),
			dock = ui.col({
				ui.row({
					ui.text({ ui.span(string.format("%d of %d done", done, total), "muted") }),
					clickable(ui.badge("Clear done", "accent"), "clear"),
				}),
			}),
		}
	end,

	key = function(state, key, _cx)
		local n = #state.items
		if key.name == "paste" then
			for line in string.gmatch(key.text or "", "[^\r\n]+") do
				add(state, line)
			end
		elseif key.name == "j" or key.name == "down" then
			state.sel = math.min(state.sel + 1, math.max(n, 1))
		elseif key.name == "k" or key.name == "up" then
			state.sel = math.max(state.sel - 1, 1)
		elseif key.name == "space" or key.name == "enter" then
			local item = state.items[state.sel]
			if item then
				item.done = not item.done
			end
		elseif key.name == "d" or key.name == "backspace" then
			table.remove(state.items, state.sel)
			state.sel = math.max(math.min(state.sel, #state.items), 1)
		else
			return false
		end
		return true
	end,

	event = function(state, ev, _cx)
		if ev.ev ~= "action" then
			return
		end
		if ev.act == "check" then
			for i, item in state.items do
				if tostring(item.id) == ev.value then
					item.done = not item.done
					state.sel = i
				end
			end
		elseif ev.act == "clear" then
			local kept = {}
			for _, item in state.items do
				if not item.done then
					table.insert(kept, item)
				end
			end
			state.items = kept
			state.sel = 1
		end
	end,

	save = function(state)
		return { items = tern.json.array(state.items), seq = state.seq }
	end,
}

tern.block.define("list", list)
```

它如何使用前面的各部分：

- **稳定的键。** 每个条目都有一个来自 `seq` 的 id，`seq` 只增不减且会被保存，因此 `i7` 在
  删除、重载或重启前后都指同一个条目。列表的 `selected` 属性用节点 id
  `main.items.i<id>` 指认选中项，这由键决定：列表在 `main` 下以 `items` 为键。
- **动作携带目标。** 点击发送 `check=<id>`，因此 `event` 通过 `ev.value` 而不是位置查找
  条目。
- **区域。** `main` 与 `dock` 的根节点都是 `col`；dock 的 `row` 位于其根节点内部，使计数
  与按钮对齐。
- **保存的内容。** 条目与 `seq` 会被保存；选中项不保存，重启后从第一个条目开始。
  `tern.json.array` 让空列表仍编码为 JSON 数组。
- **打开方式。** 命令面板中的 “New Checklist block” 会打开一个空列表。window 半区可以用
  `cx:new_block("checklist.list", { "Write tests", "Update docs" })` 打开一个已备好内容的
  列表。

## 相关页面 {#related-pages}

- [Host API](../reference/api-host.md#ternblockdefine)：每个字段、操作与消息。
- [构建视图](views.md)：构建器、动作、色调与 CSS。
- [生命周期与重载](../concepts/lifecycle.md)：哪些内容在何时重启。
- [文件、进程与存储](io.md)：定时器、进程与 `tern.kv`。
