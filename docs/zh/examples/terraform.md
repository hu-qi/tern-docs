# Terraform 计划 {#terraform-plans}

`terraform` 把 `terraform plan` 与 `tofu plan` 的人类可读输出转成原生视图：摘要徽标、带源码片段的诊断信息，以及按动作分组的计划资源，其中破坏性分组排在最前。点击某个资源会复制它的地址。它是带自有样式表的命令 lens 的示例。

## 展示了什么 {#what-it-demonstrates}

| Surface | 半区 | 用于 |
| --- | --- | --- |
| `[[lenses]]` 的 `match` glob | 清单 | 认领 `terraform plan`、`tofu plan` 及其 `-chdir=` 形式 |
| 带 `open`、`line`、`finish`、`view` 的 `tern.lens.define` | Host | 逐行解析计划并将其绘制出来 |
| `ui.badge`、`ui.section`、`ui.diagnostic`、`ui.overflow` | Host | 摘要、分组、错误与警告、过长的分组 |
| 节点上的 `actions = { click = … }`、lens 的 `event` | Host | 点击时复制资源地址 |
| `EffectCx:copy`、`EffectCx:toast` | Host | 剪贴板与确认提示 |
| 清单中的 `role` 属性与 `styles` | 两者 | 按动作给行着色、标记破坏性计划 |

该插件没有 window 半区：它只需要 lens 视图及其 CSS。样式表仍由每个窗口加载，因为 CSS 属于窗口的职责。

## 安装 {#install}

```sh
tern plugin install github.com/stencil-hq/tern-sdk/plugins/examples/terraform
```

修改它时，可以改为克隆 SDK 并链接该文件夹，这样 Tern 每次保存都会重新加载它：

```sh
git clone https://github.com/stencil-hq/tern-sdk
tern plugin link tern-sdk/plugins/examples/terraform
```

lens 需要 shell 集成（它会上报每条命令行）与 `command_lenses` 设置，两者默认均已开启。在项目中运行 `terraform plan`；该 block 的 **Raw** 开关仍会显示原始输出。

## 设计 {#design}

### 认领什么，不认领什么 {#what-it-claims-and-what-it-leaves-alone}

lens 的认领是声明式的。面板的每个副本（守护进程、每个窗口、iOS、Web 客户端）都必须就哪些命令成为 lens block 达成一致，但只有 host 运行 Lua，因此这个决定由清单的 `match` glob 针对程序及其参数（以单个空格连接）作出。`open` 无法拒绝 glob 已匹配的命令；收窄 glob 是唯一的拒绝方式（参见[命令 lens](../guides/lenses.md)）。

| 模式 | 匹配 |
| --- | --- |
| `terraform plan`、`terraform plan *` | 普通计划，带或不带选项 |
| `terraform -chdir=* plan`、`terraform -chdir=* plan *` | 另一个目录的计划 |
| `tofu …` | OpenTofu 的同样四种形式 |

`terraform apply` 有意不被认领。没有 `-auto-approve` 时，它会打印计划，然后停在 `Enter a value:` 处等你输入 `yes`。读取一行不会开启那些让 Tern 中止 lens 并重放原始输出的终端模式（备用屏幕、鼠标或键盘模式），因此原生视图会持续盖住它正在提出的问题。计划只会为没有值的必填变量提问；`-input=false` 改为让它失败，lens 会把该失败显示为一条诊断。

有些计划不是给人看的：`terraform plan -json` 输出 JSON 流，`terraform plan -help` 打印用法。两者都不包含解析器能识别的任何内容，因此 `view` 返回 `nil`，而 `nil` 视图会让 block 继续显示原始输出。

### 逐行读取计划 {#reading-the-plan-line-by-line}

命令运行期间，每输出一行就会调用一次 `line`，视图最多每 250 ms 重绘一次，因此解析器是一个小状态机，从不回顾超过一行：

| 输出 | lens 记录的内容 |
| --- | --- |
| `<addr>: Refreshing state...` | 一个以 “N refreshed” 显示的计数 |
| `Note: Objects have changed outside of Terraform` | 进入漂移小节 |
| `Terraform will perform the following actions:` | 进入动作小节 |
| `  # <addr> will be created`（及其他后缀） | 一个资源及其动作 |
| `  # (because …)`、`  # (moved from …)` | 上方资源的一条备注 |
| `Changes to Outputs:` 与 `  + name` 行 | 输出变更 |
| `Plan: N to add, M to change, K to destroy.` | 摘要 |
| `No changes.` | 无变更状态 |
| `╷`、`│ Error: …`、`│ …`、`╵` | 一条诊断及其正文 |

资源标题会与一张后缀表匹配（“will be created”、“will be updated in-place”、“must be replaced”、“is tainted, so must be replaced”、“will be read during apply” 等）。该表经过排序，使较长的后缀先于以其结尾的较短后缀被尝试，而 `(deposed object …)` 限定语会被拆分到该行的备注中。漂移小节中的标题使用另一张表（“has changed”、“has been deleted”），因为这些资源不属于计划将要执行的内容。

诊断是 Terraform 用 `╷`、`│` 与 `╵` 画出的方框。第一个 `│ Error: title` 或 `│ Warning: title` 行会开启一条诊断；`on main.tf line 12` 给出它的位置，其下的带编号行成为片段，之后的段落成为备注。Terraform 打印的路径相对于它运行所在的目录，因此 `open` 会保留 shell 的 `cwd`（或 `-chdir=` 目录），`ui.diagnostic` 据此解析路径，从而把该位置变成指向文件的链接。

`finish` 记录退出状态。使用 `-detailed-exitcode` 时，有变更的计划以 2 退出，因此只有 0 与 2 之外的状态才算计划失败。

### 视图 {#the-view}

顶行是作为徽标的摘要，每个徽标都带有其含义对应的色调：

| 徽标 | 色调 |
| --- | --- |
| “N to import” | `info` |
| “N to add” | `success` |
| “N to change” | `warning` |
| “N to destroy” | `error` |
| “No changes” | `success` |
| 命令运行期间的 “Planning” 以及按动作统计的运行中计数 | `pending`、`muted` |
| “Plan failed”、“N errors” | `error` |
| “N warnings” | `warning` |

其下是诊断，然后每个动作一个可折叠的 `ui.section`。顺序就是评审者阅读的顺序：Destroy、Replace、Update in place、Create，然后是更安静的 Import、Move、Forget 与 Read。每个 section 都有一个命名其动作的 `key`，因此在计划流式传入时，即使上方出现另一个分组，它的身份也不会漂移。apply 期间读取的数据源与漂移小节（“Changed outside Terraform”）默认折叠：它们解释计划，但不是计划所做的变更。超过 200 行的分组以 `ui.overflow` 结尾，即指向 Raw 的 “… N more” 行。

### 复制地址 {#copying-an-address}

每个资源行都是一个文本节点，其属性携带一个点击动作：

```lua
local p: { [string]: any } = node.p or {}
p.actions = { click = "copy-address=" .. r.addr }
node.p = p
```

点击会以 `{ev = "action", act = "copy-address", value = "<addr>"}` 的形式到达 lens 的 `event` 处理器。只有第一个 `=` 分隔动作名与其值，因此诸如 `terraform_data.item["a=b"]` 的地址会完整地出现在 `ev.value` 中。处理器直接使用该值，不做拆分或解码：

```lua
if ev.ev == "action" and ev.act == "copy-address" and type(ev.value) == "string" then
	cx:copy(ev.value)
	cx:toast("success", "Copied resource address", ev.value)
end
```

事件的 `EffectCx` 把复制与 toast 送达正在显示该面板的窗口。lens 状态保留在 host 工作线程上，每个插件最近 256 次捕获；点击较旧的 block 时，会先对其已保存的输出重放 `open`、`line` 与 `finish`，因此在守护进程重启后点击仍然有效。

### 通过 role 设置样式 {#styling-through-roles}

插件从不只按位置或只按 Tern 的内部类名设置样式。每条规则都限定在 lens block 的 role 上，即 `.sf-block[data-role='lens.plugin.terraform.plan']`，插件则在自己想要定位的节点上设置自己的 role：

| Role | 节点 | 样式 |
| --- | --- | --- |
| `terraform.plan` | 视图的根 | 无 |
| `terraform.plan.danger` | 有内容被销毁或替换时的根 | 沿左边缘的一条红线 |
| `terraform.<action>` | 每个资源行 | `--tc` 设为该动作的色调，供悬停高亮使用 |

颜色取自 Tern 的色调变量（`--sf-ok`、`--sf-warn`、`--sf-bad`、`--sf-info`、`--sf-muted`），因此浅色与深色主题都能跟随。该文件在清单的 `styles` 下列出，并作为全局样式表 `plugin:local:terraform:styles` 安装；参见 [Chrome 与样式](../guides/chrome.md)。

## 限制 {#limits}

- 解析器读取的是 Terraform 的人类可读输出，而这不是稳定的接口；未来的版本若改写某个标题，该资源就会被漏掉（摘要行仍会计入它）。
- 资源仅按动作分组，不按模块分组。
- 停在 `var.name Enter a value:` 提示处的计划会隐藏该提示，直到切换到 Raw；请使用 `-input=false` 或 `.tfvars` 文件运行计划。
- 单个动作中超过 200 个资源的计划只显示前 200 个，并给出指向 Raw 的提示。

## 代码 {#code}

`plugin.toml`：

```toml
schema = 1
id = "terraform"
name = "Terraform"
version = "1.0.0"
description = "Reads terraform and tofu plans as summary badges and resources grouped by action."
icon = "stack"
host = "host.luau"
styles = ["terraform.css"]

[[lenses]]
id = "plan"
match = [
	"terraform plan",
	"terraform plan *",
	"terraform -chdir=* plan",
	"terraform -chdir=* plan *",
	"tofu plan",
	"tofu plan *",
	"tofu -chdir=* plan",
	"tofu -chdir=* plan *",
]
```

`host.luau`：

```lua
--!strict
-- The `plan` lens: Terraform's (and OpenTofu's) human-readable plan output
-- as summary badges, diagnostics and resources grouped by action. Clicking a
-- resource copies its address.

local ui = tern.ui

-- Rows shown per group before the rest fold into "… N more".
local GROUP_ROWS = 200

-- The diagnostic box Terraform draws around errors and warnings.
local BOX_SIDE = "│"
local BOX_END = "╵"

type Resource = { addr: string, action: string, note: string? }
type Output = { sym: string, name: string }
type Diagnostic = {
	severity: string,
	title: string,
	path: string?,
	line: number?,
	snippet: { any }?,
	notes: { string },
	para: string?,
}
type State = {
	base: string?,
	tool: string,
	section: string,
	resources: { Resource },
	drift: { Resource },
	outputs: { Output },
	summary: { [string]: number }?,
	nochanges: boolean,
	refreshed: number,
	diags: { Diagnostic },
	open: Diagnostic?,
	header: boolean,
	status: number?,
}

-- Resource headers (`# <addr> <suffix>`), longest suffix first where one
-- ends another.
local ACTIONS = {
	{ " is tainted, so must be replaced", "replace" },
	{ " will be replaced, as requested", "replace" },
	{ " must be replaced", "replace" },
	{ " will be created", "create" },
	{ " will be updated in-place", "update" },
	{ " will be destroyed", "destroy" },
	{ " will be read during apply", "read" },
	{ " will be imported", "import" },
	{ " will no longer be managed by Terraform", "forget" },
	{ " will no longer be managed by OpenTofu", "forget" },
}

-- Headers of the "Objects have changed outside of Terraform" section.
local DRIFT = {
	{ " has been deleted", "deleted" },
	{ " has changed", "changed" },
}

-- Groups in the order a reviewer reads them: what is lost first.
local GROUPS = {
	{ action = "destroy", title = "Destroy", sym = "-", style = "error" },
	{ action = "replace", title = "Replace", sym = "-/+", style = "warning" },
	{ action = "update", title = "Update in place", sym = "~", style = "warning" },
	{ action = "create", title = "Create", sym = "+", style = "success" },
	{ action = "import", title = "Import", sym = "<-", style = "info" },
	{ action = "move", title = "Move", sym = "->", style = "muted" },
	{ action = "forget", title = "Forget", sym = "/", style = "muted" },
	{ action = "read", title = "Read during apply", sym = "<=", style = "info" },
}

local function starts(s: string, prefix: string): boolean
	return string.sub(s, 1, #prefix) == prefix
end

local function ends(s: string, suffix: string): boolean
	return #s >= #suffix and string.sub(s, -#suffix) == suffix
end

-- The directory relative paths in diagnostics resolve against: the shell's
-- working directory, or the `-chdir=` one.
local function base_dir(run: LensRun): string?
	for _, arg in run.args do
		local dir = string.match(arg, "^%-chdir=(.+)$")
		if dir then
			if starts(dir, "/") or run.cwd == nil then
				return dir
			end
			return run.cwd .. "/" .. dir
		end
	end
	return run.cwd
end

-- The resource a `# …` header line announces, if it is one.
local function header(body: string, section: string): Resource?
	if section == "drift" then
		for _, pair in DRIFT do
			if ends(body, pair[1]) then
				return { addr = string.sub(body, 1, #body - #pair[1]), action = pair[2] }
			end
		end
		return nil
	end
	local from, to = string.match(body, "^(.-) has moved to (.+)$")
	if from and to then
		return { addr = to, action = "move", note = "moved from " .. from }
	end
	for _, pair in ACTIONS do
		if ends(body, pair[1]) then
			local addr = string.sub(body, 1, #body - #pair[1])
			local base, deposed = string.match(addr, "^(.-) %((deposed object %w+)%)$")
			if base and deposed then
				return { addr = base, action = pair[2], note = deposed }
			end
			return { addr = addr, action = pair[2] }
		end
	end
	return nil
end

-- Ends the paragraph a diagnostic is collecting.
local function flush(d: Diagnostic)
	if d.para then
		table.insert(d.notes, d.para)
		d.para = nil
	end
end

-- One line from inside a diagnostic box.
local function absorb(d: Diagnostic, body: string)
	local path, line = string.match(body, "^%s*on (.-) line (%d+)")
	if path and line and d.path == nil then
		d.path = path
		d.line = tonumber(line)
		return
	end
	local num, src = string.match(body, "^%s*(%d+): ?(.*)$")
	if num and src and d.path and #d.notes == 0 and d.para == nil then
		local snippet = d.snippet
		if snippet then
			snippet[2] ..= "\n" .. src
		else
			d.snippet = { tonumber(num) :: any, src }
		end
		return
	end
	local text = string.match(body, "^%s*(.-)%s*$") or ""
	if text == "" then
		flush(d)
	elseif starts(text, "├") then
		return -- the rule above value annotations
	elseif starts(text, BOX_SIDE) then
		flush(d)
		table.insert(d.notes, (string.gsub(string.sub(text, #BOX_SIDE + 1), "^%s+", "")))
	else
		d.para = if d.para then d.para .. " " .. text else text
	end
end

local function close(state: State)
	local open = state.open
	if open then
		flush(open)
		state.open = nil
	end
end

-- A clickable resource row: its symbol, address and note.
local function resource_row(r: Resource, sym: string, style: string): Node
	local spans: { Span | string } = { ui.span(sym, style .. " strong"), " ", ui.span(r.addr, "mono") }
	if r.note then
		table.insert(spans, ui.span("  " .. r.note, "muted"))
	end
	local node = ui.text(spans)
	local p: { [string]: any } = node.p or {}
	p.role = "terraform." .. r.action
	p.title = "Copy address"
	p.actions = { click = "copy-address=" .. r.addr }
	node.p = p
	return node
end

-- A collapsible group of rows, keyed so its collapsed state survives updates.
local function group(key: string, head: Spans, rows: { Node }, total: number, collapsed: boolean): Node
	if total > #rows then
		table.insert(rows, ui.overflow(total - #rows))
	end
	local node = ui.section(head, rows)
	local p: { [string]: any } = node.p or {}
	p.key = key
	p.collapsible = true
	p.collapsed = collapsed
	node.p = p
	return node
end

local function counts(state: State): { [string]: number }
	local n: { [string]: number } = {}
	for _, r in state.resources do
		n[r.action] = (n[r.action] or 0) + 1
	end
	return n
end

local function badges(state: State): { Node }
	local out: { Node } = {}
	local errors, warnings = 0, 0
	for _, d in state.diags do
		if d.severity == "error" then
			errors += 1
		else
			warnings += 1
		end
	end
	local summary = state.summary
	if summary then
		local any = false
		for _, b in
			{
				{ "import", "to import", "info" },
				{ "add", "to add", "success" },
				{ "change", "to change", "warning" },
				{ "destroy", "to destroy", "error" },
				{ "forget", "to forget", "muted" },
			}
		do
			local n = summary[b[1]] or 0
			if n > 0 then
				any = true
				table.insert(out, ui.badge(n .. " " .. b[2], b[3]))
			end
		end
		if not any then
			table.insert(out, ui.badge("No resource changes", "muted"))
		end
	elseif state.nochanges then
		table.insert(out, ui.badge("No changes", "success"))
	elseif state.status == nil then
		table.insert(out, ui.badge("Planning", "pending"))
		local n = counts(state)
		for _, g in GROUPS do
			if n[g.action] then
				table.insert(out, ui.badge(n[g.action] .. " " .. string.lower(g.title), "muted"))
			end
		end
	elseif state.status ~= 0 and state.status ~= 2 then
		-- `-detailed-exitcode` exits 2 for a plan with changes, 1 for an error.
		table.insert(out, ui.badge("Plan failed", "error"))
	end
	if #state.outputs > 0 then
		local label = if #state.outputs == 1 then " output change" else " output changes"
		table.insert(out, ui.badge(#state.outputs .. label, "info"))
	end
	if errors > 0 then
		table.insert(out, ui.badge(errors .. (if errors == 1 then " error" else " errors"), "error"))
	end
	if warnings > 0 then
		table.insert(out, ui.badge(warnings .. (if warnings == 1 then " warning" else " warnings"), "warning"))
	end
	if state.refreshed > 0 then
		table.insert(out, ui.text({ ui.span(state.refreshed .. " refreshed", "muted") }))
	end
	return out
end

local function view(state: State): Node?
	local empty = #state.resources == 0
		and #state.drift == 0
		and #state.outputs == 0
		and #state.diags == 0
		and state.summary == nil
		and not state.nochanges
	if empty then
		return nil -- not a plan we can read (`-json`, `-help`): raw output
	end

	local children: { Node } = { ui.row(badges(state)) }
	for _, d in state.diags do
		table.insert(
			children,
			ui.diagnostic({
				severity = d.severity :: any,
				message = d.title,
				path = d.path,
				line = d.line,
				snippet = d.snippet,
				notes = d.notes,
			}, state.base)
		)
	end

	local danger = false
	for _, g in GROUPS do
		local rows: { Node } = {}
		local total = 0
		for _, r in state.resources do
			if r.action == g.action then
				total += 1
				if total <= GROUP_ROWS then
					table.insert(rows, resource_row(r, g.sym, g.style))
				end
			end
		end
		if total > 0 then
			danger = danger or g.action == "destroy" or g.action == "replace"
			local head = { ui.span(g.title, "strong " .. g.style), ui.span("  " .. total, "muted num") }
			table.insert(children, group(g.action, head, rows, total, g.action == "read"))
		end
	end

	if #state.drift > 0 then
		local rows: { Node } = {}
		for i, r in state.drift do
			if i > GROUP_ROWS then
				break
			end
			table.insert(rows, resource_row(r, "!", "muted"))
		end
		local head = {
			ui.span("Changed outside " .. state.tool, "strong muted"),
			ui.span("  " .. #state.drift, "muted num"),
		}
		table.insert(children, group("drift", head, rows, #state.drift, true))
	end

	if #state.outputs > 0 then
		local rows: { Node } = {}
		for _, o in state.outputs do
			local style = if o.sym == "+" then "success" elseif o.sym == "-" then "error" else "warning"
			local spans: { Span | string } = { ui.span(o.sym, style .. " strong"), " ", ui.span(o.name, "mono") }
			table.insert(rows, ui.text(spans))
		end
		local head = { ui.span("Outputs", "strong"), ui.span("  " .. #state.outputs, "muted num") }
		table.insert(children, group("outputs", head, rows, #state.outputs, false))
	end

	local root = ui.col(children)
	local p: { [string]: any } = root.p or {}
	p.role = if danger then "terraform.plan.danger" else "terraform.plan"
	root.p = p
	return root
end

tern.lens.define("plan", {
	open = function(run: LensRun, _cx: EffectCx): State
		return {
			base = base_dir(run),
			tool = if run.program == "tofu" then "OpenTofu" else "Terraform",
			section = "",
			resources = {},
			drift = {},
			outputs = {},
			summary = nil,
			nochanges = false,
			refreshed = 0,
			diags = {},
			open = nil,
			header = false,
			status = nil,
		}
	end,

	line = function(state: State, l: LensLine)
		local text = l.text

		-- Diagnostics: `╷`, then `│ Error: title` and its body, then `╵`.
		if starts(text, BOX_SIDE) then
			local body = string.gsub(string.sub(text, #BOX_SIDE + 1), "^ ", "")
			local severity, title = string.match(body, "^(%a+): (.+)$")
			if (severity == "Error" or severity == "Warning") and title then
				close(state)
				local d: Diagnostic = { severity = string.lower(severity), title = title, notes = {} }
				table.insert(state.diags, d)
				state.open = d
			elseif state.open then
				absorb(state.open, body)
			end
			return
		end
		if starts(text, BOX_END) then
			close(state)
			return
		end
		local bare_sev, bare_title = string.match(text, "^(%a+): (.+)$")
		if (bare_sev == "Error" or bare_sev == "Warning") and bare_title then
			-- Without the box (older releases): the title alone.
			table.insert(state.diags, { severity = string.lower(bare_sev), title = bare_title, notes = {} })
			return
		end

		-- Section markers.
		if starts(text, "Note: Objects have changed outside of ") then
			state.section = "drift"
		elseif string.find(text, "^%a+ will perform the following actions:") then
			state.section = "actions"
		elseif text == "Changes to Outputs:" then
			state.section = "outputs"
			return
		end

		-- Resource headers and the `# (because …)` notes right under them.
		local body = string.match(text, "^%s*# (.+)$")
		if body then
			local note = string.match(body, "^%((.*)%)$")
			local last = state.resources[#state.resources]
			if note then
				if state.header and last and last.note == nil then
					last.note = note
				end
				return
			end
			local r = header(body, state.section)
			if r then
				table.insert(if state.section == "drift" then state.drift else state.resources, r)
				state.header = state.section ~= "drift"
				return
			end
		end
		state.header = false

		if state.section == "outputs" then
			local sym, name = string.match(text, "^  ([%+~%-]) ([%w_%-]+)")
			if sym and name then
				table.insert(state.outputs, { sym = sym, name = name })
			elseif text ~= "" and not starts(text, " ") then
				state.section = ""
			end
		end

		local plan = string.match(text, "^Plan: (.+)$")
		if plan then
			local summary: { [string]: number } = {}
			for n, what in string.gmatch(plan, "(%d+) to (%a+)") do
				if n and what then
					summary[what] = tonumber(n) or 0
				end
			end
			state.summary = summary
		elseif starts(text, "No changes.") then
			state.nochanges = true
		elseif string.find(text, ": Refreshing state...", 1, true) then
			state.refreshed += 1
		end
	end,

	finish = function(state: State, status: number?)
		close(state)
		state.status = status
	end,

	view = view,

	event = function(_state: State, ev: UiEvent, cx: EffectCx)
		if ev.ev ~= "action" or ev.act ~= "copy-address" or type(ev.value) ~= "string" then
			return
		end
		cx:copy(ev.value)
		cx:toast("success", "Copied resource address", ev.value)
	end,
})
```

`terraform.css`：

```css
/* The terraform plan lens. Every rule is scoped by the lens block's role, so
   the sheet touches nothing else; colors come from Tern's tone variables, so
   light and dark themes both follow. */

/* A plan that destroys or replaces something: a red rule down its view. */
.sf-block[data-role='lens.plugin.terraform.plan'] [data-role='terraform.plan.danger'] {
	box-shadow: inset 2px 0 0 rgb(from var(--sf-bad) r g b/70%);
	padding-left: 10px;
}

/* Resource rows take their action's color as --tc. */
.sf-block[data-role='lens.plugin.terraform.plan'] .sf-text[data-role^='terraform.'] {
	--tc: var(--sf-muted);
	border-radius: 4px;
	padding: 0 4px;
}
.sf-block[data-role='lens.plugin.terraform.plan'] .sf-text[data-role='terraform.create'] {
	--tc: var(--sf-ok);
}
.sf-block[data-role='lens.plugin.terraform.plan'] .sf-text[data-role='terraform.update'],
.sf-block[data-role='lens.plugin.terraform.plan'] .sf-text[data-role='terraform.replace'] {
	--tc: var(--sf-warn);
}
.sf-block[data-role='lens.plugin.terraform.plan'] .sf-text[data-role='terraform.destroy'] {
	--tc: var(--sf-bad);
}
.sf-block[data-role='lens.plugin.terraform.plan'] .sf-text[data-role='terraform.read'],
.sf-block[data-role='lens.plugin.terraform.plan'] .sf-text[data-role='terraform.import'] {
	--tc: var(--sf-info);
}

/* A click copies the address: say so on hover. */
.sf-block[data-role='lens.plugin.terraform.plan'] .sf-text[data-role^='terraform.']:hover {
	background: rgb(from var(--tc) r g b/12%);
	box-shadow: inset 2px 0 0 var(--tc);
}
```
