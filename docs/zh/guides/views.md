# 构建视图 {#building-views}

block 与 lens 的视图是由普通 Lua 表构成的树，用于描述原生 UI 节点：表格、列表、卡片、图表、代码。`tern.ui` 用与 Tern 内置 lens 相同的函数构建它们，因此插件生成的表格在外观与行为上都与内置的一致。本页介绍节点模型、构建器、让节点可交互、色调与样式，以及用于读取命令输出的 `tern.parse`。

## 节点 {#nodes}

视图是一棵节点树，采用 Tern Surface 协议（TSP）的线路格式：

```lua
type Node = {
	k: string,              -- kind: "text", "col", "table", "badge", …
	p: { [string]: any }?,  -- props
	c: { Node }?,           -- children
}
```

构建器返回的就是这些表，别无其他，因此你可以在把树交回之前查看、修改与组合它们。文本由 span 构成：`{ t = "text", s = "style tokens", href = "link" }`。span 列表（`Spans`）是 span 与字符串组成的列表、单个 span，或单个字符串。

```lua
local ui = tern.ui

local node = ui.card({ ui.span("Build", "strong") }, {
	ui.kv({
		{ "Target", { ui.span("aarch64-apple-darwin", "code") } },
		{ "Took", { ui.span("41.2s", "num") } },
	}),
	ui.progress(0.6, "linking"),
})
-- node = { k = "card", p = { head = { … } }, c = { { k = "kv", … }, { k = "progress", … } } }
```

接收这棵树的对象有所不同：

| | block 的 `view` | lens 的 `view` |
| --- | --- | --- |
| 返回 | `{main?, dock?, layer?}`，每个区域一棵树 | 一个节点，或为原始输出返回 `nil` |
| 区域根 | 仅作为其子节点绘制；请使用容器 | 节点按原样绘制 |
| 更新 | 按节点 id 与上一个视图做差异比较 | 按位置与上一个视图做差异比较 |
| 节点 id | `main.<key or index>…`，配合 `p.key` 保持稳定 | 由 Tern 依据每个节点的位置分配 |

id 与键参见 [block](blocks.md#regions-node-ids-and-keys)，lens 视图参见[命令 lens](lenses.md#views-while-the-command-runs)。

## 构建器 {#builders}

每个构建器都会检查自己的参数，参数错误时抛出 `tern.ui.<builder>: <argument>: <problem>`。每个构建器的确切输出见 [UI 构建器](../reference/ui.md)。

| 用途 | 构建器 |
| --- | --- |
| span | `span(t, s?)`, `link(t, href, s?)`, `path(p, cwd?)` |
| 文本 | `text(spans)` |
| 布局 | `col(children)`（有间隙）、`lines(children)`（无间隙）、`row(children)`、`card(head, children, props?)`、`section(head, children)`、`rule(label)` |
| 操作 | `button(text, props?)` |
| 值 | `badge(t, tone)`、`kv({ {key, value}, … })`、`stats({ {label, value, sub?}, … })`、`meter(value, label)`、`progress(value?, label)` |
| 表格 | `table(cols, rows, opts?)`、`meter_cell(value, {warn, bad}?)`、`meter_parts_cell({ {value, token}, … })` |
| 树与列表 | `tree({ {label, icon?, open?, children?}, … })`、`list({ {label, detail?, value?, icon?, tone?}, … })` |
| 文本与代码 | `code(text, lang?, start?)`、`diff(text, path?)`、`md(text)`、`ansi(text)` |
| 图表 | `bars({ {label, value}, … })`、`spark({ {label, value}, … })` |
| 结果 | `diagnostic(d, cwd?)`、`test_summary(passed, failed, skipped, took?)`、`overflow(hidden)` |
| 其他一切 | `node(kind, props?, children?)` |

有几项需要超出其签名的说明：

- **`table(cols, rows, opts?)`。** 每一列为 `{id, head, align?,
  priority?, grow?, truncate?, mono?}`. `rows[i][j]` 是
  `cols[j]` 的单元格：一个 span 列表、一个 meter 单元格，或 text、badge、button、spark 单元格；以 `{id, cells, disabled?, menu?, title?}` 形式给出的行会保留其 id。面板过窄时，`priority` 最低的列最先隐藏；`grow` 分配多余宽度；`truncate` 指明长单元格在何处截断（`"end"`、`"start"`、`"middle"`）。`opts`（`selectable`、`selected`、`empty`）让行可被挑选（参见[数据](../elements/data.md#table)）。
- **`path(p, cwd?)`。** 链接到文件的路径 span。相对路径按 `cwd` 解析（在 lens 中传入 `run.cwd`，在 block 中传入 `cx.cwd`）；没有 `cwd` 时该 span 不会被链接。
- **`ansi(text)`。** 一个小型终端，显示带转义序列的文本，用于你不解析的输出。
- **`overflow(hidden)`。** 那行弱化的 “… N more”。内置 lens 最多显示 5,000 行并以它结尾；请以同样的方式为你的视图设上限。

`node` 可以触达 Surface 协议定义的每一种类型，包括没有构建器覆盖的那些：

```lua
ui.node("spinner", { style = "dots", label = { ui.span("Fetching", "muted") } })
ui.node("kbd", { keys = { "ctrl", "o" } })
ui.node("elapsed", { age = 1500, format = "short" })
```

[元素](../elements/index.md) 记录了每一种类型、其属性、事件与样式钩子。

## 每个节点都接受的属性 {#props-every-node-takes}

| 属性 | 含义 |
| --- | --- |
| `key` | block 视图中同一层级内的身份（参见 [block](blocks.md#regions-node-ids-and-keys)）。局部状态按该键在同一父节点之下记忆，而非整个 Surface 范围，即使删除该节点并以新 id 重新添加也如此；没有键时使用节点的 id |
| `tone` | 节点 chrome 的语义颜色（见下） |
| `role` | 你自己的名称，以 `data-role` 暴露给 CSS |
| `collapsible` | 在 `card` 与 `section` 上，`true` 会启用标题栏的展开控件 |
| `collapsed` | 与 `collapsible = true` 一起使用时，`true` 使该 `card` 或 `section` 初始为折叠；单独使用不会折叠内容 |
| `actions` | 指针操作的效果：`{ click = "name", dblclick = "name", menu = { … } }` |

节点没有属性时，构建器会省略 `p`，而声明把 `p` 标为可选，因此在 `--!strict` 下请通过局部变量设置属性：

```lua
local ui = tern.ui
local function with(node: Node, props: { [string]: any }): Node
	local p: { [string]: any } = node.p or {}
	for k, v in props do
		p[k] = v
	end
	node.p = p
	return node
end

local retry = with(ui.badge("Retry", "accent"), { actions = { click = "retry" }, key = "retry" })
local details = with(ui.card("Details", { ui.text("Expandable content") }), {
	collapsible = true,
	collapsed = true,
})
return ui.col({ retry, details }) -- lens view; for a block wrap in { main = ... }
```

## 操作与事件 {#actions-and-events}

`actions` 把指针手势映射到操作名称。有些名称属于 Tern 自身，会在窗口中运行而不会到达你的代码；其他任何名称都属于你，并作为事件到达。

| 操作 | 发生什么 | 事件 |
| --- | --- | --- |
| `toggle` | Tern 打开或关闭该可折叠节点 | `{ev = "toggle", id, key, collapsed}` |
| `copy` | Tern 复制节点的文本（有 `href` 时复制它） | 无 |
| `open` | Tern 打开节点的 `href` 或 `path` | 无 |
| `zoom` | Tern 放大显示 `image` 节点 | 无 |
| `select` | 由你的代码决定 | `{ev = "select", id, item}` |
| `activate` | 由你的代码决定（双击） | `{ev = "activate", id, item}` |
| 其他任何名称 | 由你的代码决定 | `{ev = "action", id, act, value?, item?, mods?, checked?}` |

对 `list` 中某个条目的 `select` 与 `activate`，`id` 是该列表，`item` 是该条目；对 `selectable` 表格中的行，`id` 是该表格，`item` 是该行的 `id`；其他情况下两者都是该节点。表格的按钮单元格与行菜单会发送 `action`，其中 `item` 为该行（参见[数据](../elements/data.md#table)）。[`button`](../elements/input.md#button) 会以其 `actions.click` 发送 `action`，没有该字段时则 `act = "click"`。

当 `toggle`、`open` 或 `zoom` 没有可作用的对象时（节点不可折叠、没有 `href` 或 `path`、不是 `image`），Tern 会像处理其他名称一样，把它作为 `{ev = "action", id, act}` 发送。

自定义操作的事件由其名称构造：

```lua
p.actions = { click = "sort=name" }
-- a shift-click sends:
-- { ev = "action", id = "main.0.1", act = "sort", value = "name", mods = { "shift" } }
```

- `act` 是名称中第一个 `=` 之前的部分；`value` 是其余部分，仅当名称含 `=` 时才存在。请把操作的目标（某个条目 id、某一列）放在那里，这样处理器就不依赖位置。
- `mods` 列出按住的修饰键（`"shift"`、`"ctrl"`、`"alt"`、`"meta"`），没有按住任何修饰键时缺失。
- `id` 是节点的 id：在 block 中，是 worker 赋予它的 id；在 lens 中，是 Tern 为该视图编造的 id。

`menu` 按顺序列出右键菜单提供的内容，其后是 Tern 的 Copy，除非列表本身包含 `copy`（菜单含图标、键或分隔符时，它出现在分隔符之后）。字符串是按其名称命名的操作（`open-file` 读作 Open file），`"-"` 是分隔符，`{ header = "…" }` 是弱化的分节标题。条目对象接受 [`menu`](../elements/lists.md#menu) 行的字段：`id`（操作）、`label`、`icon`、`keys`（仅显示；绑定由你负责）、`detail`（在此作为其提示文字）、`checked` 用于勾选行、`radio` 为单选行指定分组、`disabled`（字符串为原因）、`danger`，以及用于子菜单的 `items`。选择某行会像点击一样运行其 `id`，但不带 `mods`；勾选行或单选行的事件还会携带 `checked`，即该行的新状态。

```lua
p.actions = { menu = {
	{ header = "deploy.log" },
	{ id = "open", label = "Open", icon = "file", keys = "enter" },
	{ id = "follow", label = "Follow output", checked = state.follow },
	"-",
	{ id = "sort=name", label = "By name", radio = "sort", checked = state.sort == "name" },
	{ id = "sort=time", label = "By time", radio = "sort", checked = state.sort == "time" },
	"-",
	{ id = "export", label = "Export", icon = "export", items = { "export=json", "export=csv" } },
	{ id = "trash", label = "Move to Trash", icon = "trash", danger = true, disabled = state.locked and "Locked" or false },
} }
-- choosing Follow output while it is checked sends:
-- { ev = "action", id = "main.0.1", act = "follow", checked = false }
```

block 的 `event(state, ev, cx)` 接收 `action`、`select`、`activate`、`change` 与 `toggle` 事件（以及来自编辑器节点的 `focus`）。lens 的 `event` 以同样的方式接收其视图的事件。两者中，Tern 都会在处理器之后重新渲染：block 运行其渲染周期，lens 运行 `view`。

`toggle` 无需处理：Tern 已经翻转了该节点。由于 block 的视图会被差异比较，视图中保持不变的 `collapsed` 属性不会撤销用户的选择。只有当你希望该状态在重启后保留时，才记录 `ev.collapsed`。

## 表单与控件 {#forms-and-controls}

`tern.ui.el` 绘制普通元素（`div`、`label`、`button`、`form` 等）与两种控件：`type = "checkbox"` 或 `"radio"` 的 `input`。控件仅响应指针：点击会在窗口中立即翻转它们，不等待你的代码，并发送 `change` 事件。按键仍归你处理。控件在 block 中可用；在 lens 视图里它们不会翻转（参见 [HTML 元素](../elements/el.md)）。

```lua
local ui = tern.ui
view = function(state, _cx)
	local function size(v)
		return ui.el("label", { class = "opt" }, {
			ui.el("input", { type = "radio", name = "size", value = v, checked = state.size == v }),
			ui.el("span", { text = v }),
		})
	end
	return { main = ui.col({
		ui.el("form", { class = "order" }, {
			size("small"), size("large"),
			ui.el("label", { class = "opt" }, {
				ui.el("input", { type = "checkbox", name = "gift", checked = state.gift }),
				ui.el("span", { text = "Gift wrap" }),
			}),
			ui.button("Order", { variant = "primary", actions = { click = "order" } }),
		}),
	}) }
end,
event = function(state, ev, _cx)
	if ev.ev == "change" then
		-- { ev = "change", id, name = "size", value = "large", checked = true, values = {…} }
	elseif ev.ev == "action" and ev.act == "order" then
		state.size, state.gift = ev.values.size, ev.values.gift
	end
end,
```

来自 `el` 表单内某个节点的每个 `action`、`select`、`activate` 与 `change` 事件都携带 `values`：该表单在那一刻处于启用状态的具名控件。单选组给出其被选中的 `value`（未选中时为 nil），单个复选框给出布尔值，共用同一名称的多个复选框则给出选中项值的数组。因此按钮的处理器无需跟踪每次 `change` 就能读取整个表单。[`button`](../elements/input.md#button) 类型在表单之外也是操作入口：Tern 的外观、键帽、`busy` 与 `disabled` 原因，且无需 CSS（参见[设计视图](design.md#buttons)）。单选按钮在其表单内按 `name` 分组。点击 `label` 会翻转其中的第一个控件。在视图中设置 `checked` 会覆盖用户的选择；保持不变则会保留它。

用清单的 `styles`、该 block 的 Surface 以及你自己的类来为表单设置样式；被选中的控件匹配 `:checked`，被禁用的匹配 `:disabled`：

```css
[data-surface='plugin.shop.order'] .opt {
	padding: 2px 6px;
}

[data-surface='plugin.shop.order'] .opt :checked {
	outline: 1px solid currentColor;
}
```

## 色调与 span 样式 {#tones-and-span-styles}

节点的 `tone` 从主题中为其 chrome 着色（badge 的胶囊、card 的边缘、列表行）：`neutral`、`accent`、`info`、`success`、`warning`、`error`、`pending`、`muted`、`user`。

span 的 `s` 是以空格分隔的 token 列表：

| token | 效果 |
| --- | --- |
| `accent`, `success`, `warning`, `error`, `info`, `pending`, `muted`, `dim` | 颜色 |
| `strong`, `em` | 字重、斜体 |
| `title` | 页面的标题，置于其标题行 |
| `code`, `mono` | 代码颜色、等宽字体 |
| `num`, `path`, `key`, `link` | 数字、路径、键与链接的颜色 |
| `ins`, `del` | 新增与删除的文本，如同 diff 中 |
| `mark` | 高亮，如同搜索匹配 |

完整列表，以及 omp 的主题 token 与各自的作用，见[文本与代码](../elements/text.md)。

未知 token 会被忽略。色调与 token 命名的是角色，而非颜色：具体颜色由当前主题提供，因此视图在浅色与深色主题下都能正确呈现，无需你干预。

## 用 CSS 设置样式 {#styling-with-css}

插件可以通过清单的 `styles` 或 `tern.css` 添加全局 CSS（参见 [chrome 与样式](chrome.md#global-css)）。插件样式表在 Tern 自身的样式表之后应用，作用于该机器上的每个窗口。视图节点可用的钩子如下：

| 元素 | 选择器 |
| --- | --- |
| 类型为 `k` 的节点 | `.sf-<k>`：`.sf-table`、`.sf-badge`、`.sf-card`、`.sf-item` |
| 带 `role` 属性的节点 | `[data-role='<role>']` |
| 带 `tone` 的节点 | `[data-tone='<tone>']` |
| span token | `.sf-t-<token>`：`.sf-t-num`、`.sf-t-del` |
| 插件 block 的各区域 | `.sf-main[data-surface='plugin.<plugin>.<block>']`，以及 `.sf-dock` 与 `.sf-layer` |
| lens block | `.sf-block[data-role='lens.plugin.<plugin>.<lens>']` |

block 的类型是其区域元素上的 `data-surface` 属性，而不是 `data-role`。区域根节点上的 role 会落到区域元素本身，因此带 `p.role = "checklist.main"` 的 `main = ui.col({ … })` 会以 `.sf-main[data-role='checklist.main']` 设置样式。

请在你的插件 id 之下为节点指定 role 并据此设置样式；Tern 的类描述的是结构，可能在不同版本之间变化。

```css
/* checklist.css, listed in plugin.toml as styles = ["checklist.css"] */
.sf-main[data-surface='plugin.checklist.list'] .sf-item .sf-t-del {
	opacity: 0.6;
}

.sf-block[data-role='lens.plugin.disk.du'] .sf-table {
	font-variant-numeric: tabular-nums;
}
```

## 读取命令输出：`tern.parse` {#reading-command-output-tern-parse}

`tern.parse` 存放内置 lens 用于许多命令共有形状的读取器。它们在两个半区中都可用。

| 函数 | 读取内容 |
| --- | --- |
| `columns(lines) -> {head, rows}?` | 按空白对齐的表格，其第一个非空行是表头（`docker ps`、`kubectl get`、`ps aux`、`df`）。列在每行都为空白处切分，因此右对齐的数字与多词表头（`Mounted on`）保持完整。散文或未对齐的文本行返回 `nil` |
| `packed(lines) -> {string}` | `ls` 风格输出中被排入多列的条目 |
| `json_tree(text) -> Node?` | 一个 JSON 文档，或它们的流，作为可折叠树；不是 JSON 时返回 `nil` |
| `location(s) -> (path?, line?, col?)` | `s` 开头的 `file:line[:col]`，如同编译器与 `grep -n` 打印的那样 |
| `size(s) -> number?` | 人类可读大小对应的字节数：`4.0K` 与 `1.2Gi` 按 1024 计，`1.2GB` 与 `512kB` 按 1000 计，`512` 与 `512B` 是字节 |

`columns` 需要整张表才能找出列边界，因此在 `line` 中收集行，在 `view` 中解析。这个 lens 把 `df` 显示为表格，并为每个百分比单元格配一个 meter：

```toml
[[lenses]]
id = "df"
match = ["df", "df *"]
```

```lua
--!strict
local ui = tern.ui

type DfState = { lines: { string } }

local function percent(cell: string): number?
	local n = string.match(cell, "^(%d+)%%$")
	return if n then tonumber(n) else nil
end

local df: LensDef<DfState> = {
	open = function(_run, _cx)
		return { lines = {} }
	end,
	line = function(state, l)
		table.insert(state.lines, l.text)
	end,
	finish = function(_state, _status) end,
	view = function(state)
		local t = tern.parse.columns(state.lines)
		if not t then
			return nil
		end
		local cols: { Col } = {}
		for j, head in t.head do
			cols[j] = { id = "c" .. j, head = head, align = if j > 1 and j < #t.head then "end" else nil }
		end
		local rows: { { Cell } } = {}
		for i, cells in t.rows do
			local row: { Cell } = {}
			for j, cell in cells do
				local pct = percent(cell)
				row[j] = if pct then ui.meter_cell(pct / 100, { 0.8, 0.95 }) else cell
			end
			rows[i] = row
		end
		return ui.table(cols, rows)
	end,
}

tern.lens.define("df", df)
```

表头决定各列，因此同一段代码既能读取 macOS 的 `df -h`（含 `Capacity`、`iused` 与 `%iused`），也能读取 Linux 的（含 `Use%`）。meter 在 80% 时变为警告色，在 95% 时变为错误色。无法构成表格的行会让 `columns` 返回 `nil`，此时 lens 回退到原始输出。

## 相关页面 {#related-pages}

- [UI 构建器](../reference/ui.md)：每个构建器的确切输出与参数错误。
- [元素](../elements/index.md)：每种节点类型、其属性、事件与 DOM。
- [视图样式](../styles/index.md)：每个样式钩子、CSS 变量与受支持的 CSS 特性。
- [block](blocks.md) 与[命令 lens](lenses.md)：视图放在哪里。
- [chrome 与样式](chrome.md)：样式表、层叠、状态段。
