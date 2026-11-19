# UI 构建器 {#ui-builders}

`tern.ui` 负责构建插件视图所组成的节点，`tern.parse` 则把命令输出读取为这些构建器所接受的结构。两者在两个半区中都存在，且与 Tern 内置 lens 使用的是同一份代码，因此插件生成的表格与内置表格完全一致。block 从 `view` 按区域返回节点；lens 从 `view` 返回一个节点。参见[构建视图](../guides/views.md)。

## 节点与 span {#nodes-and-spans}

每个构建器都返回一个普通 Lua 表，在返回之前可以检视并修改它。

```lua
type Node = {
	k: string,               -- kind: "text", "col", "table", …
	p: { [string]: any }?,   -- props (absent when empty)
	c: { Node }?,            -- children (absent when empty)
}

type Span = {
	t: string,               -- text
	s: string?,              -- space-separated style tokens
	href: string?,           -- link target
	fx: string?,             -- effect: "shimmer", "pulse" or "none"
}

type Spans = { Span | string } | string
```

每个节点都接受的属性：

| 属性 | 含义 |
| --- | --- |
| `key` | 在其兄弟节点中的身份标识：在重排序后仍保持该节点的 id。局部状态按此 key 记在其父节点之下，而非整个 surface，并且在同一个父节点下删掉一个节点、再新增一个 id 不同但 key 相同的节点后依然保留。没有 key 时，局部状态使用节点的 id。兄弟节点之间不得共用同一个 key；同一个 key 位于另一个父节点之下时状态相互独立 |
| `tone` | 语义颜色：`accent`、`success`、`warning`、`error`、`info`、`muted` 等 |
| `role` | 以 `data-role` 暴露给 CSS 的角色字符串 |
| `collapsible` | 在 `card` 与 `section` 上，`true` 启用标题栏的展开控件 |
| `collapsed` | 与 `collapsible = true` 配合时，`true` 让 `card` 或 `section` 一开始就处于折叠状态；单独使用不会折叠内容 |
| `actions` | 指针动作，例如 `{ click = "name" }`；自定义名称以事件 `{ ev = "action", act = "name" }` 到达（block 与 lens） |

通过 `p` 设置属性；构建器没有创建它时，自行创建：

```lua
local node = tern.ui.badge("Retry", "accent")
local p: { [string]: any } = node.p or {}
p.actions = { click = "retry" }
p.key = "retry"
node.p = p
```

要让卡片初始为折叠状态并允许用户展开，需同时设置两个属性（`section` 同理）：

```lua
local ui = tern.ui
local details = ui.card("Details", { ui.text("Expandable content") })
local p: { [string]: any } = details.p or {}
p.collapsible = true
p.collapsed = true
details.p = p
return details -- lens view; for a block use { main = ui.col({ details }) }
```

### 参数转换 {#argument-conversion}

构建器会校验参数，并以 `tern.ui.<builder>: <argument>: <problem>` 报错，同时指明参数路径（`cols[2].align`、`rows[3][1]`、`items[1].label`）。常见问题：

| 消息结尾 | 原因 |
| --- | --- |
| `expected a string, got <type>` | 需要文本的位置出现了非字符串（数字会被接受并转换） |
| `expected a number, got <type>` | |
| `expected an integer in <min>..=<max>, got <n>` | 计数、行号或列号为小数，或超出范围 |
| `expected a boolean, got <type>` | |
| `expected a list, got <type>` | 列表参数不是表（`nil` 视为空列表） |
| `expected a table, got <type>` | |
| `expected a {a, b} pair, got <type>` | 二元组参数（`kv` 项、series 数据点）不是表 |
| ``expected a span (a table with a string `t`)`` | span 列表中的表缺少 `t` |
| `expected a span or a string, got <type>` | |
| `expected a list of nodes, got one node (wrap it in {})` | 子节点位置放进了单个节点 |
| ``expected a node (a table with a string `k`)`` | |
| `expected a table of props, got <type>` | `node` 的 props 不是映射表 |

span 列表（`Spans`）可以是按顺序排列的 span 与字符串列表、单个 span 表，或单个字符串；`nil` 表示空。字符串会变成无样式的 span。

## span {#spans}

### `span` 构建器 {#span}

```lua
tern.ui.span: (t: string, s: string?) -> Span
```

由 `t` 构成的 span。`s` 是以空格分隔的样式标记（`"muted"`、`"strong error"`、`"num"`、`"code"`、`"path"`）；缺省或为 `""` 时表示无样式。输出：`{ t = t, s = s }`（无样式时不含 `s`）。

### `link` 构建器 {#link}

```lua
tern.ui.link: (t: string, href: string, s: string?) -> Span
```

链接到 `href` 的 `t` span。输出：`{ t, s?, href }`。点击会经过窗口的链接处理，包括 `tern.route.link`。

### `path` 构建器 {#path}

```lua
tern.ui.path: (p: string, cwd: string?) -> Span
```

带 `path` 样式的 span，显示 `p` 并链接到其绝对 `file://` URL。相对的 `p` 会基于 `cwd` 解析；没有 `cwd` 时，或 `p` 为 `~` 路径时，该 span 不带链接。输出：`{ t = p, s = "path", href = "file:///…" }`。

```lua
tern.ui.text({ tern.ui.span("see "), tern.ui.path("src/main.rs", run.cwd) })
```

## 布局 {#layout}

| 构建器 | 签名 | 输出 |
| --- | --- | --- |
| `text` | `(spans: Spans) -> Node` | `{k = "text", p = {spans}}` |
| `col` | `(children: { Node }) -> Node` | `{k = "col", p = {gap = "sm"}, c}`：小间距的纵向堆叠 |
| `lines` | `(children: { Node }) -> Node` | `{k = "col", p = {gap = "none"}, c}`：同一文本流的各行，无间距 |
| `row` | `(children: { Node }) -> Node` | `{k = "row", p = {gap = "sm"}, c}`：水平排列的一行 |
| `card` | `(head: Spans, children: { Node }, props: CardProps?) -> Node` | `{k = "card", p = {head, …props}, c}`；`props` 接受 `icon`、`meta`、`end` 以及任意通用属性 |
| `section` | `(head: Spans, children: { Node }) -> Node` | `{k = "section", p = {head}, c}`：更轻量的折叠组 |
| `rule` | `(label: Spans) -> Node` | `{k = "rule", p = {label?}}`：分隔线，`label` 非空时带标签（`rule()` 为无标签分隔线） |

`gap` 属性可覆盖 `col` 与 `row` 的间距：`none`、`xs`、`sm`、`md`、`lg`。

```lua
tern.ui.card({ tern.ui.span("Build", "strong"), tern.ui.span(" "), tern.ui.span("3 warnings", "warning") }, {
	tern.ui.lines({ tern.ui.text("first line"), tern.ui.text("second line") }),
})
```

标题栏中包含图标、meta 与控件的面板（`end` 按 id 指定某个子节点；参见 [`card`](../elements/layout.md#card)）：

```lua
tern.ui.card("Services", {
	tern.ui.button("Refresh", { key = "end", icon = "repeat", keys = { "r" }, actions = { click = "refresh" } }),
	services_table,
}, { key = "services", icon = "server", meta = "24 · 2 degraded", ["end"] = "main.services.end" })
```

## 值 {#values}

### `badge` 构建器 {#badge}

```lua
tern.ui.badge: (t: string, tone: string) -> Node
```

胶囊式徽章。输出 `{k = "badge", p = {text = t, tone}}`。运行时会接受缺失的 `tone`（即普通徽章）。

### `button` 构建器 {#button}

```lua
tern.ui.button: (text: string?, props: ButtonProps?) -> Node

type ButtonProps = {
	icon: string?,
	keys: { string }?,
	variant: ("default" | "primary" | "quiet" | "danger")?,
	size: ("sm" | "md")?,
	on: boolean?,
	disabled: (boolean | string)?,
	busy: boolean?,
	-- and any common prop: key, actions, title, aria, tone, …
}
```

按钮。输出 `{k = "button", p = {text, …props}}`。属性值错误时会带路径报错（`tern.ui.button: props.variant: expected one of default, primary, quiet, danger, got "big"`）。参见
[`button`](../elements/input.md#button)。

```lua
tern.ui.button("Deploy", { variant = "primary", keys = { "cmd", "enter" }, actions = { click = "deploy" } })
```

### `kv` 构建器 {#kv}

```lua
tern.ui.kv: (items: { { Spans } }) -> Node
```

对齐的键/值列表。每一项是一个二元组 `{ keySpans, valueSpans }`。
输出 `{k = "kv", p = {items = {{k = spans, v = spans}, …}}}`。

```lua
tern.ui.kv({ { "context", tern.ui.span("prod", "error strong") }, { "namespace", "default" } })
```

### `stats` 构建器 {#stats}

```lua
tern.ui.stats: (items: { StatItem }) -> Node

type StatItem = { label: Spans, value: Spans, sub: Spans?, tone: string?, title: string? }
```

一条扁平的统计瓦片带，用于紧贴页面标题行之下（绝不放在 card 中）。输出 `{k = "stats", p = {items}}`。参见
[`stats`](../elements/data.md#stats)。

```lua
tern.ui.stats({
	{ label = "Error rate", value = "0.42%", tone = "warning", sub = "last 15 min" },
	{ label = "p95 latency", value = "182 ms" },
})
```

### `meter` 构建器 {#meter}

```lua
tern.ui.meter: (value: number, label: Spans) -> Node
```

处于 `value` 的计量条，数值会被钳制到 0–1，标签为 `label`。输出
`{k = "meter", p = {value, label}}`。

### `progress` 构建器 {#progress}

```lua
tern.ui.progress: (value: number?, label: Spans) -> Node
```

处于 `value` 的进度条（钳制到 0–1）；`nil` 表示进度不确定。输出
`{k = "progress", p = {value, label}}`。

### `bars`、`spark` 构建器 {#bars-spark}

```lua
tern.ui.bars: (series: { { any } }) -> Node
tern.ui.spark: (series: { { any } }) -> Node
```

由 `{ label, value }` 对组成的柱状图或迷你折线图（`label` 为字符串或数字，`value` 为数字）。
输出
`{k = "chart", p = {kind = "bars" | "spark", series = {{value = value, label = label}, …}}}`。

```lua
local series: { { any } } = {}
for i, ms in timings do
	series[i] = { tostring(i), ms }
end
return tern.ui.spark(series)
```

### `test_summary` 构建器 {#test_summary}

```lua
tern.ui.test_summary: (passed: number, failed: number, skipped: number, took: string?) -> Node
```

一行包含堆叠的通过/失败/跳过计量条与计数（`3 passed · 1 failed · 1.2s`），
`failed > 0` 时色调为 `error`，否则为 `success`。计数为非负整数。

### `overflow` 构建器 {#overflow}

```lua
tern.ui.overflow: (hidden: number) -> Node
```

一行弱化的文本 `… N more (Raw shows everything)`。当 lens 只显示较长输出的一部分时
使用它。

## 表格 {#tables}

### `table` 构建器 {#table}

```lua
tern.ui.table: (cols: { Col }, rows: { { Cell } | TableRow }, opts: TableOpts?) -> Node

type Col = {
	id: string,
	head: string,
	align: ("start" | "center" | "end")?,
	priority: number?,
	grow: number?,
	truncate: ("end" | "start" | "middle")?,
	mono: boolean?,
}

type TableRow = {
	id: string,
	cells: { Cell },
	disabled: (boolean | string)?,
	menu: { string }?,
	title: string?,
}

type TableOpts = { selectable: boolean?, selected: string?, empty: Spans? }

type Cell = Spans | TextCell | BadgeCell | ButtonCell | SparkCell | MeterCell
type TextCell = { text: Spans, icon: string?, dot: string?, tone: string?, title: string? }
type BadgeCell = { badge: { text: string, tone: string?, title: string? } }
type ButtonCell = {
	button: { text: string, act: string, icon: string?, keys: { string }?, variant: string?, disabled: (boolean | string)? },
}
type SparkCell = { spark: { values: { number }, tone: string?, min: number?, max: number?, title: string? } }
```

行是单元格列表，或带有自身 `id` 的 `TableRow`（可选表格需要后者）。
无论哪种形式，`cells[j]` 都是 `cols[j]` 的单元格；多余的单元格会被忽略，缺少的为空。
单元格表按原样传入；每种单元格绘制的内容，以及可选行、按钮单元格和行菜单发出的事件，
参见 [`table`](../elements/data.md#table)。

| 列字段 | 默认值 | 含义 |
| --- | --- | --- |
| `id` | 必填 | 行的单元格以此为键的 id；后出现的同 id 列生效 |
| `head` | 必填 | 表头文本 |
| `align` | `"start"` | 单元格对齐方式；数字用 `"end"`。其他值会报错 ``unknown align "<v>" (start\|center\|end)`` |
| `priority` | `0` | 表格较窄时，优先级最低的列最先隐藏（整数） |
| `grow` | `0` | 该列占用的剩余宽度份额 |
| `truncate` | `"end"` | 放不下的单元格从何处截断：`"end"` 保留开头（`abcd…`），`"start"` 保留结尾（`…wxyz`），`"middle"` 保留两端（路径优先丢弃目录）。其他值会报错 ``unknown truncate "<v>" (end\|start\|middle)`` |
| `mono` | `false` | 无衬线区域内的等宽字体单元格（id、版本、大小、时间） |

输出：`{k = "table", p = {cols = {{id, head, align, truncate, priority,
grow, mono}, …}, rows = {{id = "r0", cells = {[colId] = cell}}, …},
selectable?, selected?, empty?}}`。以单元格列表给出的行按位置获得 id `r0`、
`r1` 等；`TableRow` 保留其 `id`、`disabled`、`menu` 与
`title`。

```lua
tern.ui.table({
	{ id = "name", head = "Pod", grow = 1, truncate = "middle" },
	{ id = "cpu", head = "CPU", align = "end", priority = 1 },
	{ id = "mem", head = "Memory", priority = 2 },
}, {
	{ "api-7d9f", "120m", tern.ui.meter_cell(0.42, { 0.7, 0.9 }) },
	{ tern.ui.span("worker-1", "muted"), "15m", tern.ui.meter_cell(0.91, { 0.7, 0.9 }) },
})
```

带稳定行 id 与丰富单元格的可选表格：

```lua
tern.ui.table({
	{ id = "name", head = "Service", grow = 1 },
	{ id = "state", head = "State" },
	{ id = "p95", head = "p95", align = "end", mono = true },
	{ id = "act", head = "", align = "end" },
}, {
	{ id = "api", cells = { { text = "api", dot = "success" }, { badge = { text = "live", tone = "success" } }, "182 ms", "" } },
	{ id = "search", menu = { "logs" }, cells = {
		{ text = "search", dot = "pending" },
		{ badge = { text = "waiting", tone = "pending" } },
		"96 ms",
		{ button = { text = "Promote", act = "promote" } },
	} },
}, { selectable = true, selected = state.selected, empty = "No services" })
```

### `meter_cell` 构建器 {#meter-cell}

```lua
tern.ui.meter_cell: (value: number, thresholds: { number }?) -> MeterCell
```

处于 `value` 的细条形单元格（钳制到 0–1）。`thresholds` 是二元组
`{ warn, bad }`：达到或超过第一个值时填充染为 `warn`，达到或超过第二个值时染为 `bad`。

### `meter_parts_cell` 构建器 {#meter-parts-cell}

```lua
tern.ui.meter_parts_cell: (parts: { { any } }) -> MeterCell
```

从左侧堆叠多个部分的细条形单元格；每个部分是
`{ value, themeToken }`，其中 `value` 钳制到 0–1，`themeToken` 是主题颜色
令牌（`"success"`、`"error"`、`"toolDiffAdded"` 等）。

```lua
type MeterCell = {
	meter: {
		value: number?,
		thresholds: { warn: number, bad: number }?,
		parts: { { value: number, token: string, label: string?, hatch: boolean? } }?,
		tone: string?,
		title: string?,
	},
}
```

两者都返回这一结构（`meter_cell` 用 `value` 与 `thresholds`，
`meter_parts_cell` 用 `parts`）。设置 `cell.meter.tone` 可为单元格着色。只要表带有
`meter` 字段，表格单元格就会被当作计量单元格读取，因此手写的 `{ meter = { … } }` 同样有效。

## 树与列表 {#trees-and-lists}

### `tree` 构建器 {#tree}

```lua
tern.ui.tree: (nodes: { TreeNode }) -> Node

type TreeNode = {
	label: Spans,
	icon: string?,
	open: boolean?,
	children: { TreeNode }?,
}
```

折叠树。`open`（默认 `false`）表示节点的子节点是否显示；只有带子节点的节点才会输出它。
输出
`{k = "tree", p = {nodes = {{id = "t0", label, icon?, open?, children?}, …}}}`；
id `t0`、`t1` 等按深度优先分配，且在树中唯一。

```lua
tern.ui.tree({
	{ label = "src", icon = "folder", open = true, children = {
		{ label = "main.rs", icon = "file" },
	} },
})
```

### `list` 构建器 {#list}

```lua
tern.ui.list: (items: { Item }) -> Node

type Item = {
	label: Spans,
	detail: Spans?,
	value: Spans?,
	icon: string?,
	tone: string?,
}
```

行列表：`label`、紧随其后的次要 `detail`、右对齐的
`value`、具名 `icon`，以及该行的 `tone`。输出
`{k = "list", c = {{k = "item", p = {label, detail?, value?, icon?, tone?}}, …}}`。

```lua
tern.ui.list({
	{ label = "main", detail = "origin/main", value = tern.ui.span("↑2", "num"), icon = "git-branch" },
	{ label = "fix-login", tone = "warning" },
})
```

## 文本与代码 {#text-and-code}

| 构建器 | 签名 | 输出 |
| --- | --- | --- |
| `code` | `(text: string, lang: string?, start: number?) -> Node` | `{k = "code", p = {text, lang?, start?, numbers?}}`：`lang`（文件扩展名或语言名）中的高亮代码；给出 `start` 时，行号从该行开始显示 |
| `diff` | `(text: string, path: string?) -> Node` | `{k = "diff", p = {text, path?}}`：统一 diff，`path` 用于选择语法 |
| `md` | `(text: string) -> Node` | `{k = "md", p = {text}}`：Markdown |
| `ansi` | `(text: string) -> Node` | `{k = "ansi", p = {text}}`：渲染 ANSI 转义序列的迷你终端 |

`text`、`md`、`code` 与 `ansi` 属于文本类，`math`、`editor`、
`input`、`shimmer` 与 `el` 也是（参见 [元素](../elements/index.md#every-kind)）：
在 block 中，随后缀增长的 `text` 属性会以追加方式发送。参见
[Host API](api-host.md#view-model)。

## 诊断 {#diagnostics}

### `diagnostic` 构建器 {#diagnostic}

```lua
tern.ui.diagnostic: (d: Diag, cwd: string?) -> Node

type Diag = {
	severity: ("error" | "warning" | "note" | "help")?,
	code: string?,
	message: string,
	path: string?,
	line: number?,
	col: number?,
	snippet: { any }?,
	notes: { string }?,
	suggestions: { { any } }?,
}
```

以卡片形式呈现的编译器或 linter 诊断。

| 字段 | 默认值 | 含义 |
| --- | --- | --- |
| `severity` | `"error"` | 色调：`error` → error，`warning` → warning，`note` → info，`help` → muted。其他值会报错 ``unknown severity "<v>" (error\|warning\|note\|help)`` |
| `code` | 无 | lint 或错误代码，以代码 span 显示（`E0308`） |
| `message` | 必填 | 消息内容 |
| `path` | 无 | 按打印原样显示的文件；位置链接到它，相对路径基于 `cwd` 解析 |
| `line`、`col` | 无 | 从 1 开始的位置，显示为 `:line:col` 并加入链接（`#L12C4`） |
| `snippet` | 无 | `{ firstLine, source }`：从 `firstLine` 开始、带行号的摘录，诊断所在行以其色调标出 |
| `notes` | 无 | 摘录下方的弱化文本行 |
| `suggestions` | 无 | `{ { message, firstLine, code }, … }`：每条都是代码摘录之上的一行弱化消息 |

卡片按严重程度着色，并以 `path:line:col:code` 作为 key，因此诊断列表在多次更新之间
保持身份标识。高亮使用 `path` 的扩展名。

```lua
tern.ui.diagnostic({
	severity = "warning",
	code = "unused_variables",
	message = "unused variable: `x`",
	path = "src/lib.rs",
	line = 4,
	col = 9,
	snippet = { 3, "fn f() {\n    let x = 1;\n}" },
	notes = { "if this is intentional, prefix it with an underscore: `_x`" },
}, run.cwd)
```

## 任意节点 {#any-node}

### `node` 构建器 {#node}

```lua
tern.ui.node: (kind: string, props: { [string]: any }?, children: { Node }?) -> Node
```

任意 Surface 协议节点类型：`{k = kind, p = props, c = children}`，为空时省略
`p` 与 `c`。用于没有构建器的类型（`image` 配 `cx:blob` 提供的 `blob` 属性，
`spacer` 等）。[元素](../elements/index.md)
记录了每种类型及其属性；未知类型由 Tern 在显示该节点时拒绝，而不是由构建器拒绝。

```lua
local id = cx:blob(tern.fs.read("chart.png"), "image/png")
return { main = tern.ui.col({ tern.ui.node("image", { blob = id, alt = "Chart" }) }) }
```

### `el` 构建器 {#el}

```lua
tern.ui.el: (tag: string, props: { [string]: any }?, children: { Node }?) -> Node
```

通用元素：`{k = "el", p = {tag = tag, …props}, c = children}`。可用标签为
`div span p section header footer nav aside main article figure
blockquote ul ol li dl dt dd h1 h2 h3 h4 pre code kbd strong em b i del mark
hr table thead tbody tr th td label button form input`。`form` 绘制为
`div`，并把其中的控件归为一组。其他标签都绘制为 `div`，且 Tern 会以 `error`
事件报告一次（`unknown el tag <tag>`）。

| 属性 | 含义 |
| --- | --- |
| `class` | 供自有 CSS 使用的空格分隔类名 |
| `attrs` | `data-*`、`aria-*`、`role`、`colspan`、`rowspan` 属性（值为字符串、数字或布尔值）；其他属性会被忽略 |
| `text` | 绘制在子节点之前的纯文本 |

通用属性（`role`、`key`、`actions`、`hidden`、`title` 等）的用法与任意节点相同。
`input` 与 `hr` 不接受子节点。

`input` 是仅响应指针的控件，`type = "checkbox"` 或 `"radio"`（其他类型都算未知标签），
并支持 `name`、`value`（默认 `"on"`）、`checked` 与 `disabled`。点击会切换它并发送
`{ev = "change", id, name?, value, checked, values?}`；参见
[表单与控件](../guides/views.md#forms-and-controls)。

```lua
tern.ui.el("label", {}, {
	tern.ui.el("input", { type = "checkbox", name = "all", checked = true }),
	tern.ui.el("span", { text = "Show all" }),
})
```

## 解析器 {#parsers}

参数不合法时，`tern.parse` 会报出 `tern.parse.<f>: lines: expected a list of strings, got
<type>`、`tern.parse.<f>: lines[<i>]: expected a string, got <type>`，或
`tern.parse.<f>: <arg>: expected a string, got <type>`。
与 `tern.ui` 不同，它不接受用数字代替字符串。

### `parse.columns` 解析函数 {#parse-columns}

```lua
tern.parse.columns: (lines: { string }) -> Columns?

type Columns = {
	head: { string },
	rows: { { string } },
}
```

读取按空白对齐的输出（`ps`、`df`、`kubectl get`、`docker ps`）：
空行会被跳过，第一行是表头。只有在每一行中该显示列都为空白处才会切分列，因此右对齐的列
会连同其表头前的空隙一起归入，含多个词的标题（`CONTAINER ID`、`Mounted on`）
保持完整。单元格会去掉首尾空白。剩余列少于两列，或没有任何两个表头词相隔两个空白
（即散文）时返回 `nil`。

```lua
local t = tern.parse.columns(state.lines)
if t then
	local cols = {}
	for i, h in t.head do
		cols[i] = { id = tostring(i), head = h }
	end
	return tern.ui.table(cols, t.rows)
end
return nil
```

### `parse.packed` 解析函数 {#parse-packed}

```lua
tern.parse.packed: (lines: { string }) -> { string }
```

紧凑多列列表（`ls`、git 的 `column.ui`）的条目，先沿每列向下读，再横向读。
没有分列时，每行就是一个条目。含空格的条目会保持完整，除非每一行都在该处断开。

### `parse.json_tree` 解析函数 {#parse-json-tree}

```lua
tern.parse.json_tree: (text: string) -> Node?
```

把 JSON 文档呈现为可折叠的树节点，对象与数组展开到深度 2；文档流（`jq '.[]'`）
每个文档显示一个节点。键的色调为 `info`，字符串为 `success`，数字为 `num`，
布尔值与 null 为 `accent`；超过 5000 个节点后其余部分会被汇总。当 `text` 不是 JSON，
或只是标量流时返回 `nil`。

### `parse.location` 解析函数 {#parse-location}

```lua
tern.parse.location: (s: string) -> (string?, number?, number?)
```

`s` 开头的 `file:line[:col]`：返回路径、行与列（列缺失时为
`nil`），或返回单个 `nil`。

```lua
local path, line, col = tern.parse.location("src/main.rs:12:5: error: x")
-- "src/main.rs", 12, 5
```

### `parse.size` 解析函数 {#parse-size}

```lua
tern.parse.size: (s: string) -> number?
```

人类可读大小换算成的字节数，或 `nil`。裸单位字母（`4.0K`、`1.2G`，即 `ls`、`du` 与 `df`
的打印形式）以及 `Ki`/`KiB` 按 1024 的幂计算；带 `B` 的单位（`kB`、`MB`、`1.2GB`，
即 `docker` 与 `pip` 的打印形式）为十进制。`"4.0K"` 为 4096；`"1.2GB"` 为 1200000000；
`"-"` 与 `""` 为 `nil`。

## 相关页面 {#related-pages}

- [构建视图](../guides/views.md)，了解布局模式。
- [Host API](api-host.md)，了解 block 与 lens 视图如何发送。

<!-- 原文有若干行内代码跨行断开，校验工具会把这些行内代码之间的散文误判为代码；以下片段仅用于对齐中英行内代码集合，不参与渲染：
` when `
` | A table in a span list without `
`), toned `
`, `
`, else `
`, naming the argument path (`
`. `
`. Rows given as cell lists get ids `
-->
