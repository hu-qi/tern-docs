# 长时间运行的命令 {#long-running-commands}

`longrun` 关注那些让你久等的命令。当一条命令行运行超过阈值（默认 15 秒）时，它会在命令结束时以 toast 报告结果，保留最近 50 条这类命令，并把它们与当前正在运行的命令一起列在旁边一个 “Slow Commands” block 中。它是同时使用两个半区实现同一功能、并共用一个模块的最小示例。

## 展示了什么 {#what-it-demonstrates}

| Surface | 半区 | 用于 |
| --- | --- | --- |
| `tern.on("command_started" / "command_finished" / "pane_exited")` | Host | 为每个面板的命令计时，包括没有任何窗口显示的面板 |
| `EffectCx:toast` | Host | “cargo build --release finished in 1m 12s” |
| `tern.kv` | Host | 历史记录与阈值，且只有一个写入者 |
| 带 `title`、`view`、`key`、`event` 的 `tern.block.define` | Host | Slow Commands block、其 dock 与其按键 |
| `tern.timer`、`BlockCx:render` | Host | 实时已用时间，仅在有命令运行时 |
| `tern.command`、`tern.bind` | Window | “Show slow commands” 及其快捷键 |
| `cx.session:panes()`、`cx.layout:focus`、`cx:new_block` | Window | 聚焦该 block，或打开它 |
| 窗口事件、`cx.session:focused()`、`cx.session:panes()` | Window | 依据当前快照刷新焦点与命令活跃状态 |
| `tern.chrome.status`、`tern.chrome.refresh`、`tern.timer` | Window | 一个状态段，显示聚焦面板的运行时长，每秒跳动一次 |
| `require("./common")` | 两者 | 共用的解析与格式化 |

## 安装 {#install}

```sh
tern plugin install github.com/stencil-hq/tern-sdk/plugins/examples/longrun
```

修改它时，可以改为克隆 SDK 并链接该文件夹，这样 Tern 每次保存都会重新加载它：

```sh
git clone https://github.com/stencil-hq/tern-sdk
tern plugin link tern-sdk/plugins/examples/longrun
```

这些计时来自 shell 集成的提示符标记，因此面板需要开启该集成（默认已开启）。运行 `sleep 20` 并等待 toast，然后按 `cmd+alt+shift+l`（macOS 之外为 `ctrl+alt+shift+l`）查看该 block。

## 设计 {#design}

### 为什么工作放在 host 上 {#why-the-work-is-on-the-host}

守护进程自己测量每条命令：当 shell 报告某条命令行结束时，守护进程会发出 `command_finished`，携带退出状态与 `took_ms`，即自匹配的 `command_started` 以来的时间。两个半区都能听到这些事件，而 `longrun` 有意把它们记录在 host 上：

| 关注点 | Host 半区 | Window 半区 |
| --- | --- | --- |
| 它能听到的面板 | 守护进程的每个面板，包括没有任何窗口显示的会话 | 仅其自身窗口的面板，且仅在窗口打开期间 |
| `tern.kv` 写入者 | 每个守护进程一个 VM | 每个窗口一个 VM，因此同一历史条目会按打开的窗口各写一次 |
| 命令所在目录 | `command_started` 携带 `cwd` | 事件上没有 `cwd` |

在窗口已关闭的会话中完成的构建仍会记入历史，而当该面板的 window key 对应的任一窗口打开时，toast 也会送达。window 半区只做需要窗口的部分：命令、快捷键与状态段。它为自己的面板听到同样的事件，而这正是该状态段所需的全部。

### 判定什么算慢 {#deciding-what-is-slow}

`command_finished` 把 `took_ms` 与阈值比较，阈值在每次事件时从 kv 的 `threshold_ms` 读取，因此 block 的 `+` 与 `-` 键会立即生效。少数程序被排除：编辑器、分页器、`ssh` 会话或 REPL 的运行时长恰好等于你使用它的时长，一条 “vim finished in 41m” 的 toast 只是噪音。`common.interactive` 找出命令行实际运行的程序（跳过 `VAR=value` 前缀，以及 `sudo`、`env`、`time` 之类的包装器），并与一个列表比对。解释器只有在不带脚本时才算交互式：`python` 是提示符，`python train.py` 是一项任务。

时长按人们的说法书写：十秒以内为 `8.4s`，此外还有 `42s`、`1m 12s`、`2h 5m`。失败时以错误色调弹出 toast，并把退出状态放在次要行的开头。

### 历史记录 {#the-history}

历史记录是一个 Lua 数组，在 host 半区加载时从 kv 读取一次，此后每次变更都整体写回。每条记录保存命令行、其目录、`took_ms`、退出状态，并在末尾保存 `os.time()`，因此 block 对今天的时间显示 “14:02”，其他日期则显示 “Mar 03 14:02”。最新的记录排在最前，数组被裁剪到 50 条，从而让 `kv.json` 保持小巧：kv 每次 `set` 都会重写整个文件。

`cwd` 来自钩子为该面板看到的 `command_started`。若插件是在命令运行途中加载的，就没有这个值，此时改用 `tern.pane.list()` 提供的面板当前目录。

### block 与其时钟 {#the-block-and-its-clock}

Slow Commands block 有两部分：“Running now”，即至少已运行一秒的命令及其已用时间；以及历史表格。它的标题会统计历史数量（“Slow Commands (12)”）。

已用时间必须不断变化，但 Tern 只在以下情形之后才运行 block 的 `view`：它的某个处理器（`init`、`key`、`event`、`resize`）、其面板的尺寸变化，或一次 `cx:render()` 调用。host 会保留每个已打开 block 在 `init` 时取得的 `BlockCx`（block 的 `cx` 比接收它的那次调用存活更久），而 `schedule()` 仅在至少一个 block 打开且至少一条命令正在运行时，才设置一个一秒的 `tern.timer`。定时器重新渲染这些 block，并再次为自己安排调度。最后一条命令结束时，完成或 shell 退出会立即取消该 tick；下一次 tick 会清除已关闭的 block，若没有剩余则停止。没有命令在运行时，`longrun` 不运行定时器。

历史与阈值的变更也会调用 `refresh()`：在某个 block 中清空历史会更新其他每个已打开 block 的历史与计数；更改阈值会更新它们所有的标签，即使没有命令运行、也没有定时器被调度。每个视图都会把自己的选中项约束在当前历史范围之内。

插件 block 没有关闭回调。`prune()` 会丢弃面板已不在 `tern.pane.list()` 中的 block，但只在两秒之后，因为 `init` 可能在守护进程列出新面板之前就已运行。

按键遵循列表约定：`↑`/`↓` 或 `j`/`k` 选择，`Enter` 复制选中的命令行，`c` 清空历史，`+`/`-` 以五秒为单位更改阈值。dock 重复这些按键，并提供 Copy 与 Clear 两个 badge，其 `actions.click` 名称会以 `{ev = "action", act = ...}` 的形式到达 block 的 `event` 处理器。Copy badge 的动作是 `copy_line` 而不是 `copy`：`copy` 是 Tern 自有的[操作](../guides/views.md#actions-and-events)之一，它会复制 badge 自身的文本，永远不会到达插件。`key` 处理器对它处理的每个按键返回 `true`，其余返回 `false`：精确的 `false` 告诉 Tern 该按键没有改变任何内容，因此跳过渲染与保存。

### 打开该 block {#opening-the-block}

“Show slow commands” 先在本窗口中查找标题以 “Slow Commands” 开头的面板并聚焦它；否则由 `cx:new_block("longrun.slow", nil, "tab")` 打开一个。当该面板所在 host 上没有已加载的插件定义该类型时（例如窗口附着到未安装 `longrun` 的远程 host），`new_block` 返回 `nil`，此时该命令以 toast 提示这一点，而不是静默失败。

清单为该 block 设置 `palette = false`，因此命令面板只显示该命令，而不会多出一行 “New Slow Commands block”。

### 会持续跳动的状态段 {#a-status-segment-that-ticks}

当聚焦面板正在运行命令时，状态行会显示其程序以及已运行的时长，如 “cargo · 1m 12s”，并持续累加；点击它会运行 `plugin.longrun.show`，从而打开该 block。

window 半区根据窗口的 `command_started` 与 `command_finished` 事件维护自己的 `running` 表：程序（经 `common.program`，因此 `FOO=1 cargo build` 显示为 `cargo`）以及起始时刻的 `tern.now()`。与历史记录一样，交互式程序被排除在外。它在每个相关的窗口事件（包括 `command_started`）上用 `cx.session:focused()` 刷新焦点，而不依赖某个启动事件。插件重新加载可能保留同一个聚焦面板而不发出 `window_start` 或 `focus`；下一条命令仍会启动计时。

状态格式化器以 `{pane, cwd, program, title, busy}` 调用，Tern 按输入缓存其答案，但运行时长取决于时钟，而时钟并不属于输入的一部分。该状态段通过以下方式保持最新：

- `schedule()` 在聚焦面板有已观测到的运行中命令时，恰好设置一个一秒的 `tern.timer`。回调收到新的 `WindowCx`；它刷新焦点并检查 `cx.session:panes()`，丢弃已不存在的面板或 `busy` 快照为 false 的运行。随后即使运行已结束，它也会调用 `tern.chrome.refresh()`，清除上一段缓存内容，并且仅在聚焦的命令仍然活跃时才再次调度。
- 未提供下一个提示符标记就退出的 shell 可能不发出窗口 `command_finished`。它的快照仍会变为空闲。下一次 tick 会检测到这一点并停止；当 `busy` 输入变化时，格式化器也会立即隐藏空闲面板的状态段。即使程序与标题未变，这也有效。
- 命令完成、面板关闭与焦点变化会核对快照，并立即取消任何不再需要的 tick。命令开始/结束与面板关闭会使 chrome 失效，因此先前运行的缓存时间绝不会显示出来。聚焦一个已观测到的运行中面板会重新启动它的计时。

上下文绝不会跨回调保留。只有活跃的聚焦命令才会驱动快照检查：空闲窗口不运行定时器，重新加载之后也是如此；同一套快照也适用于远程面板。

在命令的第一秒内，格式化器不返回任何内容，因此快速命令不会闪现状态段；一分钟以内它写出整秒（`42s`），之后则采用 `common.duration` 的 `1m 12s` 与 `2h 5m`。相关规则见 [chrome 与样式](../guides/chrome.md#refreshing)。

## 限制 {#limits}

- 没有 shell 集成的面板不报告命令，因此不会有任何计时。
- 状态段只对 window 半区看到其启动的命令计时：窗口打开或插件重新加载时已在运行的命令，在下一条命令之前不显示状态段。
- 历史与阈值属于守护进程所在的机器（`<state>/plugin-data/longrun/kv.json`）。

## 代码 {#code}

`plugin.toml`：

```toml
schema = 1
id = "longrun"
name = "Long-Running Commands"
version = "0.1.0"
description = "Toasts when a slow command finishes and lists recent slow commands."
icon = "clock"
host = "host.luau"
window = "window.luau"

[[blocks]]
id = "slow"
title = "Slow Commands"
# The window half's "Show slow commands" command opens it.
palette = false
```

`common.luau`，由两个半区共用 require：

```lua
--!strict
-- Helpers both halves of longrun require: reading a command line's program
-- and writing durations the way people say them.

local common = {}

-- Words that run another program: the program is the next word.
local WRAPPERS: { [string]: boolean } = {
	sudo = true,
	env = true,
	time = true,
	nice = true,
	nohup = true,
	command = true,
	exec = true,
	caffeinate = true,
}

-- Programs that stay open until you leave them. Their run time measures how
-- long you used them, not how long you waited, so they are never "slow".
common.INTERACTIVE = {
	vi = true,
	vim = true,
	nvim = true,
	hx = true,
	nano = true,
	emacs = true,
	less = true,
	more = true,
	man = true,
	ssh = true,
	mosh = true,
	tmux = true,
	screen = true,
	top = true,
	htop = true,
	btop = true,
	watch = true,
	fzf = true,
	lazygit = true,
	tig = true,
	ipython = true,
	psql = true,
	mysql = true,
	sqlite3 = true,
	["redis-cli"] = true,
	omp = true,
}

-- Interpreters that are a prompt when run bare and a job when given a
-- script: `python` waits for you, `python train.py` makes you wait.
local REPLS: { [string]: boolean } = {
	python = true,
	python3 = true,
	node = true,
	irb = true,
	lua = true,
}

-- The program a command line runs (the first word that is not a
-- `VAR=value` prefix, a wrapper or a wrapper's flag, without its
-- directory), and whether more words follow it.
function common.program(line: string): (string?, boolean)
	local at = 1
	while true do
		local from, to, word = string.find(line, "(%S+)", at)
		if from == nil then
			return nil, false
		end
		local w = word :: string
		local assignment = string.find(w, "^[%a_][%w_]*=") ~= nil
		local flag = string.sub(w, 1, 1) == "-"
		if not assignment and not flag and not WRAPPERS[w] then
			local rest = string.sub(line, (to :: number) + 1)
			return string.match(w, "([^/]+)$"), string.find(rest, "%S") ~= nil
		end
		at = (to :: number) + 1
	end
end

-- Whether `line` runs a program you use rather than wait for: one
-- `INTERACTIVE` lists, or a bare interpreter.
function common.interactive(line: string): boolean
	local program, args = common.program(line)
	if program == nil then
		return false
	end
	return common.INTERACTIVE[program] == true or (REPLS[program] == true and not args)
end

-- `ms` as "8.4s", "42s", "1m 12s" or "2h 5m".
function common.duration(ms: number): string
	if ms < 10000 then
		return string.format("%.1fs", ms / 1000)
	end
	local seconds = math.floor(ms / 1000)
	if seconds < 60 then
		return string.format("%ds", seconds)
	end
	local minutes = seconds // 60
	if minutes < 60 then
		return string.format("%dm %ds", minutes, seconds % 60)
	end
	return string.format("%dh %dm", minutes // 60, minutes % 60)
end

-- `path` with the home directory written `~`.
function common.tilde(path: string, home: string?): string
	if home and home ~= "" then
		if path == home then
			return "~"
		end
		if string.sub(path, 1, #home + 1) == home .. "/" then
			return "~" .. string.sub(path, #home + 1)
		end
	end
	return path
end

-- `text` cut to `max` characters, the last one an ellipsis.
function common.clip(text: string, max: number): string
	local length = utf8.len(text)
	if length == nil then -- not UTF-8: count bytes
		return if #text <= max then text else string.sub(text, 1, max - 1) .. "…"
	end
	if length <= max then
		return text
	end
	local cut = utf8.offset(text, max) or (#text + 1)
	return string.sub(text, 1, cut - 1) .. "…"
end

return common
```

`host.luau`：

```lua
--!strict
-- longrun, host half: a `command_finished` hook that toasts when a command
-- took longer than the threshold and keeps the last 50 such commands in
-- `tern.kv`, and the "Slow Commands" block that lists them beside the
-- commands running right now.

local common = require("./common")
local ui = tern.ui

local DEFAULT_THRESHOLD_MS = 15000
local STEP_MS = 5000
local KEEP = 50
local HOME = tern.getenv("HOME")

-- A finished slow command, as stored under kv `history` (newest first).
type Record = {
	line: string,
	cwd: string?,
	took_ms: number,
	status: number,
	at: number, -- os.time() when it finished
}

-- A command a shell is running now.
type Run = {
	line: string,
	cwd: string?,
	started: number, -- tern.now() when it started
}

-- An open Slow Commands block.
type Open = {
	cx: BlockCx,
	since: number,
}

type State = {
	selected: number,
}

local function threshold(): number
	local value = tern.kv.get("threshold_ms")
	return if type(value) == "number" and value > 0 then value else DEFAULT_THRESHOLD_MS
end

-- The history, read once; every change writes it back.
local slow: { Record } = tern.kv.get("history") or {}
-- Commands running now, by pane.
local running: { [number]: Run } = {}
-- Open blocks, by pane.
local blocks: { [number]: Open } = {}
-- The pending re-render tick, while one is scheduled.
local tick: TimerHandle? = nil

local function cwd_of(pane: number): string?
	for _, info in tern.pane.list() do
		if info.pane == pane then
			return info.cwd
		end
	end
	return nil
end

-- Drops blocks whose pane is gone. A block registers in `init`, which can
-- run before the daemon lists its pane, so young entries are kept.
local function prune()
	local live: { [number]: boolean } = {}
	for _, info in tern.pane.list() do
		live[info.pane] = true
	end
	local now = tern.now()
	for pane, open in blocks do
		if not live[pane] and now - open.since > 2000 then
			blocks[pane] = nil
		end
	end
end

-- Re-renders every open block.
local function refresh()
	prune()
	for _, open in blocks do
		open.cx:render()
	end
end

-- Ticks once a second while a block is open and a command runs, so the
-- elapsed times move; stops by itself when either is no longer true.
local function schedule()
	if next(running) == nil or next(blocks) == nil then
		if tick ~= nil then
			tick:cancel()
			tick = nil
		end
		return
	end
	if tick ~= nil then
		return
	end
	tick = tern.timer(1000, function()
		tick = nil
		refresh()
		schedule()
	end)
end

local function remember(record: Record)
	table.insert(slow, 1, record)
	while #slow > KEEP do
		table.remove(slow)
	end
	tern.kv.set("history", slow)
end

tern.on("command_started", function(ev: CommandStartedEvent, _cx: EffectCx)
	running[ev.pane] = { line = ev.line, cwd = ev.cwd, started = tern.now() }
	schedule()
end)

tern.on("command_finished", function(ev: CommandFinishedEvent, cx: EffectCx)
	local run = running[ev.pane]
	running[ev.pane] = nil
	if ev.took_ms >= threshold() and not common.interactive(ev.line) then
		local cwd = if run then run.cwd else cwd_of(ev.pane)
		remember({ line = ev.line, cwd = cwd, took_ms = ev.took_ms, status = ev.status, at = os.time() })
		local line = common.clip(ev.line, 60)
		local took = common.duration(ev.took_ms)
		local where = if cwd then common.tilde(cwd, HOME) else nil
		if ev.status == 0 then
			cx:toast("success", string.format("%s finished in %s", line, took), where)
		else
			local sub = string.format("exit %d", ev.status) .. (if where then " · " .. where else "")
			cx:toast("error", string.format("%s failed after %s", line, took), sub)
		end
	end
	refresh()
	schedule()
end)

tern.on("pane_exited", function(ev: PaneExitedEvent, _cx: EffectCx)
	running[ev.pane] = nil
	refresh()
	schedule()
end)

-- Block views.

local function badge(text: string, tone: string, action: string): Node
	local node = ui.badge(text, tone)
	local props: { [string]: any } = node.p or {}
	props.actions = { click = action }
	node.p = props
	return node
end

local function when(at: number): string
	if os.date("%Y-%m-%d", at) == os.date("%Y-%m-%d") then
		return os.date("%H:%M", at)
	end
	return os.date("%b %d %H:%M", at)
end

local function running_view(): Node?
	local now = tern.now()
	local runs: { Run } = {}
	for _, run in running do
		-- Under a second is noise; interactive programs aren't waits.
		if now - run.started >= 1000 and not common.interactive(run.line) then
			table.insert(runs, run)
		end
	end
	if #runs == 0 then
		return nil
	end
	table.sort(runs, function(a: Run, b: Run)
		return a.started < b.started
	end)
	local rows = {}
	for _, run in runs do
		table.insert(rows, {
			{ ui.span(run.line, "mono") },
			{ ui.span(if run.cwd then common.tilde(run.cwd, HOME) else "", "muted") },
			{ ui.span(common.duration(now - run.started), "num accent") },
		})
	end
	local cols: { Col } = {
		{ id = "command", head = "Command", grow = 1 },
		{ id = "cwd", head = "Directory", truncate = "start", priority = -1 },
		{ id = "elapsed", head = "Running", align = "end" },
	}
	return ui.section("Running now", { ui.table(cols, rows) })
end

local function history_view(state: State): Node
	if #slow == 0 then
		return ui.text({
			ui.span(string.format("No command has taken %s or longer yet.", common.duration(threshold())), "muted"),
		})
	end
	local rows = {}
	for i, record in slow do
		local mark = if i == state.selected then ui.span("›", "accent strong") else ""
		local status = if record.status == 0
			then ui.span("ok", "success")
			else ui.span(string.format("exit %d", record.status), "error")
		table.insert(rows, {
			{ mark },
			{ ui.span(record.line, if i == state.selected then "mono strong" else "mono") },
			{ ui.span(if record.cwd then common.tilde(record.cwd, HOME) else "", "muted") },
			{ ui.span(common.duration(record.took_ms), "num") },
			{ status },
			{ ui.span(when(record.at), "muted num") },
		})
	end
	local cols: { Col } = {
		{ id = "mark", head = "" },
		{ id = "command", head = "Command", grow = 1 },
		{ id = "cwd", head = "Directory", truncate = "start", priority = -1 },
		{ id = "took", head = "Took", align = "end" },
		{ id = "status", head = "Status" },
		{ id = "when", head = "When", align = "end", priority = -2 },
	}
	return ui.table(cols, rows)
end

local function dock(): Node
	return ui.row({
		ui.text({
			ui.span("↑↓", "strong"),
			ui.span(" select  ", "muted"),
			ui.span("⏎", "strong"),
			ui.span(" copy  ", "muted"),
			ui.span("c", "strong"),
			ui.span(" clear  ", "muted"),
			ui.span("+ −", "strong"),
			ui.span(string.format(" threshold %s", common.duration(threshold())), "muted"),
		}),
		-- Not "copy": that is Tern's own action and would copy the badge's text.
		badge("Copy", "accent", "copy_line"),
		badge("Clear", "muted", "clear"),
	})
end

local function copy(state: State, cx: BlockCx)
	local record = slow[state.selected]
	if record then
		cx:copy(record.line)
		cx:toast("info", "Copied", common.clip(record.line, 60))
	end
end

local function clear(state: State)
	table.clear(slow)
	tern.kv.set("history", nil)
	state.selected = 1
	refresh()
end

local function nudge(delta: number)
	local value = math.max(STEP_MS, threshold() + delta)
	tern.kv.set("threshold_ms", value)
	refresh()
end

tern.block.define("slow", {
	init = function(cx: BlockCx, _args: { string }, _saved: any): State
		blocks[cx.pane] = { cx = cx, since = tern.now() }
		schedule()
		return { selected = 1 }
	end,
	title = function(_state: State): string?
		return if #slow > 0 then string.format("Slow Commands (%d)", #slow) else "Slow Commands"
	end,
	view = function(state: State, _cx: BlockCx): BlockView
		state.selected = math.clamp(state.selected, 1, math.max(1, #slow))
		local parts: { Node } = {}
		local now = running_view()
		if now then
			table.insert(parts, now)
		end
		table.insert(parts, history_view(state))
		return { main = ui.col(parts), dock = dock() }
	end,
	key = function(state: State, key: Key, cx: BlockCx): boolean?
		local press = key.text or key.name
		if key.name == "up" or press == "k" then
			state.selected = math.max(1, state.selected - 1)
		elseif key.name == "down" or press == "j" then
			state.selected = math.min(math.max(1, #slow), state.selected + 1)
		elseif key.name == "enter" then
			copy(state, cx)
		elseif press == "c" then
			clear(state)
		elseif press == "+" or press == "=" then
			nudge(STEP_MS)
		elseif press == "-" then
			nudge(-STEP_MS)
		else
			return false
		end
		return true
	end,
	event = function(state: State, ev: UiEvent, cx: BlockCx)
		if ev.ev ~= "action" then
			return
		end
		if ev.act == "copy_line" then
			copy(state, cx)
		elseif ev.act == "clear" then
			clear(state)
		end
	end,
})
```

`window.luau`：

```lua
--!strict
-- longrun, window half: the "Show slow commands" command and its key, and a
-- status line segment with the focused pane's running command and how long
-- it has been running, ticking once a second.

local common = require("./common")

local BLOCK = "longrun.slow"
local ACTION = "plugin.longrun.show"
-- The segment appears once a command has run this long, so quick commands
-- don't flash it.
local SHOW_AFTER_MS = 1000

-- A command running in one of this window's panes.
type Run = {
	program: string,
	started: number, -- tern.now() when it started
}

-- Commands running now, by pane. Only commands this window half saw start:
-- one already running when the plugin loaded has no entry.
local running: { [number]: Run } = {}
-- The focused pane, refreshed from the current session on events and ticks.
local focused: number? = nil
-- The pending tick, while one is scheduled.
local tick: TimerHandle? = nil

local function show(cx: WindowCx)
	-- Focus a Slow Commands block this window already shows, else open one.
	for _, pane in cx.session:panes() do
		if string.find(pane.title, "^Slow Commands") then
			cx.layout:focus(pane.pane)
			return
		end
	end
	if cx:new_block(BLOCK, nil, "tab") == nil then
		cx:toast("error", "Slow Commands is unavailable", "The longrun host half isn't loaded on this host.")
	end
end

tern.command({
	id = "show",
	title = "Show slow commands",
	icon = "clock",
	run = show,
})

tern.bind(if tern.runtime.os == "macos" then "cmd+alt+shift+l" else "ctrl+alt+shift+l", ACTION)

-- A reload need not emit window_start or focus. Every event and timer gets
-- a fresh context; never retain one. Snapshots also detect shell exits that
-- supplied no command_finished prompt mark.
local function reconcile(cx: WindowCx)
	focused = cx.session:focused()
	local busy: { [number]: boolean } = {}
	for _, pane in cx.session:panes() do
		busy[pane.pane] = pane.busy == true
	end
	for pane in running do
		if not busy[pane] then
			running[pane] = nil
		end
	end
end

-- Exactly one timer while the focused pane has an observed running command.
local function schedule()
	if focused == nil or running[focused :: number] == nil then
		if tick ~= nil then
			tick:cancel()
			tick = nil
		end
		return
	end
	if tick ~= nil then
		return
	end
	tick = tern.timer(1000, function(cx: WindowCx?)
		tick = nil
		reconcile(cx :: WindowCx)
		-- Refresh even when reconciliation removed the run, to erase its
		-- last cached segment before stopping the clock.
		tern.chrome.refresh()
		schedule()
	end)
end

tern.on("window_start", function(cx: WindowCx)
	reconcile(cx)
	schedule()
end)

tern.on("focus", function(_ev: FocusEvent, cx: WindowCx)
	reconcile(cx)
	schedule()
end)

tern.on("command_started", function(ev: CommandStartedEvent, cx: WindowCx)
	reconcile(cx)
	if not common.interactive(ev.line) then
		running[ev.pane] = { program = common.program(ev.line) or ev.line, started = tern.now() }
	end
	-- Drop any cached answer from an earlier run with the same input.
	tern.chrome.refresh()
	schedule()
end)

tern.on("command_finished", function(ev: CommandFinishedEvent, cx: WindowCx)
	running[ev.pane] = nil
	reconcile(cx)
	tern.chrome.refresh()
	schedule()
end)

tern.on("pane_closed", function(ev: PaneEvent, cx: WindowCx)
	running[ev.pane] = nil
	reconcile(cx)
	tern.chrome.refresh()
	schedule()
end)

-- Whole seconds under a minute, then as `common.duration` writes them.
local function elapsed(ms: number): string
	if ms < 60000 then
		return string.format("%ds", ms // 1000)
	end
	return common.duration(ms)
end

-- The formatter's answer depends on the clock, which is not part of its
-- input ({pane, cwd, program, title, busy}), so Tern would keep showing its first
-- answer: the timer above calls `tern.chrome.refresh()` to drop it.
tern.chrome.status(function(pane: PaneInfo): { StatusSegment }?
	-- busy changes the formatter input even if program/title happen to stay
	-- identical (for example a command that runs the login shell itself).
	if not pane.busy then
		running[pane.pane] = nil
		schedule()
		return nil
	end
	local run = running[pane.pane]
	if run == nil then
		return nil
	end
	local ms = tern.now() - run.started
	if ms < SHOW_AFTER_MS then
		return nil
	end
	return {
		{
			text = string.format("%s · %s", run.program, elapsed(ms)),
			icon = "clock",
			tone = "muted",
			command = ACTION,
		},
	}
end)
```
