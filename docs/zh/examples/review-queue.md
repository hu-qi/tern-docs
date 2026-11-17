# 评审队列 {#review-queue}

`review-queue` 把等待评审的 pull request 放进一个 block：它每两分钟运行一次
GitHub CLI 的 `gh search prs --review-requested=@me`，并列出结果及其仓库、标题、
作者、时长和草稿状态。它既是由后台进程供给数据的长期存活 block 的示例，也是
用窗口命令打开 block 的示例。

## 展示了什么 {#what-it-demonstrates}

| Surface | 半区 | 用于 |
| --- | --- | --- |
| 带 `init`、`title`、`view`、`key`、`event`、`save` 的 `tern.block.define` | Host | Review Queue block |
| 带 `timeout_ms` 与 `env` 的 `tern.process.run` | Host | 在 worker 线程之外运行 `gh` |
| `tern.timer`、`TimerHandle:cancel`、`BlockCx:render`、`tern.pane.list` | Host | 每次 block 运行一条轮询链，在重启或关闭时退役 |
| `tern.json.decode` | Host | 读取 `gh` 的 JSON |
| 带 `selected`、`max` 与带 key 条目的 `ui.list` | Host | 列表、其光标与点击事件 |
| `ui.card`、`ui.md`、`ui.code`、badge 的 `actions` | Host | 带 Retry 与 Install 按钮的错误视图 |
| `BlockCx:open` | Host | 在浏览器中打开 pull request |
| `save` 与 `init` 的 `saved` | Host | 记住是否显示草稿 |
| `tern.command`、`tern.bind` | Window | “Open review queue” 及其快捷键 |
| `cx.session:panes()`、`cx.layout:focus`、`cx:new_block` | Window | 聚焦已打开的队列，或打开一个 |

## 安装 {#install}

该 block 在运行面板的机器（即守护进程所在的 host）上运行 `gh`，因此请在那里安装
[GitHub CLI](https://cli.github.com) 并用 `gh auth login` 登录。然后：

```sh
tern plugin install github.com/stencil-hq/tern-sdk/plugins/examples/review-queue
```

修改它时，可以改为克隆 SDK 并链接该文件夹，这样 Tern 每次保存都会重新加载它：

```sh
git clone https://github.com/stencil-hq/tern-sdk
tern plugin link tern-sdk/plugins/examples/review-queue
```

按 `alt+shift+cmd+r`，或从命令面板运行 **Open review queue**。

## 设计 {#design}

### 不阻塞地运行 `gh` {#running-gh-without-blocking}

每次调用 host 插件都在其 worker 上按 2 秒预算运行，而一次 GitHub 搜索可能比这更久。
`tern.process.run` 在线程池上启动程序并立即返回；其回调随后在 worker 上带着结果运行。
block 在第一个结果到达之前显示进度条。每个回调先检查其状态是否仍属于该 block 的
当前运行，然后以 `state.cx:render()` 结束，因为 Tern 只在处理器之后才自行重新运行
`view`。

```lua
tern.process.run(argv, opts, function(result: ProcessResult, _)
	done(result)
end)
```

对于由守护进程启动的程序，这些选项很重要：

| 选项 | 原因 |
| --- | --- |
| `timeout_ms = 30000` | 挂起的网络调用以 `timed_out` 结束，而不是让 block 永远停留在 “refreshing” 状态 |
| `GH_PROMPT_DISABLED=1` | `gh` 不会在它并不拥有的终端上等待回答 |
| `GH_NO_UPDATE_NOTIFIER=1`、`NO_COLOR=1` | stderr 保持为 block 可以显示的纯错误消息 |

由 launchd 或 systemd 启动的守护进程通常只有很短的 `PATH`。block 先按名称尝试
`gh`，然后尝试磁盘上存在的常见安装位置
（`/opt/homebrew/bin`、`/usr/local/bin`、Linuxbrew、`/usr/bin`）。程序无法启动时
`tern.process.run` 会抛出错误，因此每次尝试都在 `pcall` 下运行，只有当全部尝试
都失败时，block 才报告缺少 `gh`。

### 轮询与停止 {#polling-and-stopping}

`init` 把自身状态注册到以面板 ID 为键的 `running` 表中，启动第一次刷新，并保存
一个 2 分钟的 `tern.timer` 句柄。重启会保留同一个面板 ID，因此仅凭面板存在并不
构成生命周期检查：状态对象还必须与 `running[state.cx.pane]` 相等。

替换用的 `init` 在注册新状态之前先让旧状态退役：它只取消旧状态的定时器并释放其
PR 列表。每次刷新、进程回调与定时器回调都会检查该状态身份。过期的回调无法更新
列表、无法渲染、无法发起另一次请求，也无法重新装载定时器；它不能移除或取消
替代者的状态或定时器。

插件 block 没有关闭回调，因此仍在运行的回调还会检查 `tern.pane.list()`。面板消失
时会让其状态退役并取消待执行的定时器。若没有待处理的进程，该清理发生在下一个
2 分钟 tick 时。在该 API 中，已经启动的进程没有取消句柄：它们会运行结束或触发
既有的 30 秒超时，其过期结果会被忽略。

定时器在刷新并装载下一个定时器之前先清除自身句柄，从而为每次当前运行只保留一个
待执行的定时器。`loading` 标志防止手动刷新（`r`、Retry）在已有 `gh` 运行时再启动
一个。

### 区分不同的失败 {#telling-failures-apart}

一次失败的运行会变成一个 `Problem`，其类型为三种之一，每种都有自己的标题与建议：

| 类型 | 判定依据 | 视图显示的内容 |
| --- | --- | --- |
| `missing` | 没有任何候选 `gh` 能被启动 | “GitHub CLI not found”，并带 Install guide 按钮 |
| `auth` | 退出状态 4（`gh` 的 “authentication required”），或 stderr 中提到 `gh auth login`、`GH_TOKEN` 或 HTTP 401 | “GitHub CLI not signed in”：运行 `gh auth login`，然后按 `r` |
| `failed` | 其他任何情况，包括超时或 JSON 不是列表 | “Could not load review requests”，并附上 stderr 的开头几行 |

在首次成功加载之前，该问题会以卡片形式占满整个 block，卡片带有 Retry（对
`missing` 还有 Install guide）按钮。列表成功加载过一次之后，后续失败会保留屏幕上
的最后一个列表，并把该问题加到 dock 中，因为在短暂故障期间，带警告的旧数据比
错误页面更有用。

### 列表 {#the-list}

`ui.list` 绘制各行；随后 block 为每个条目设置形如 `owner/repo#number` 的 `key`，
并为列表本身设置 key `queue`。节点 ID 由 key 构造，因此无论列表在下一次轮询时
如何重排，每行的 ID 都是 `main.queue.<owner/repo#number>`。列表的 `selected` 属性
指定的就是该 ID，其 `select`（单击）与 `activate`（双击）事件在 `ev.item` 中携带的
也是该 ID，因此光标跟随的是某个 pull request，而不是某个位置。当被选中的 pull
request 消失时，光标移到第一行。

block 的绘制方式有两个细节会影响视图：

- 区域绘制的是 `view` 返回节点的子节点，而不是该节点本身。若直接把列表作为 `main`
  返回，它会丢失选中状态与事件，因此 `main` 始终是包裹列表、卡片或进度条的
  `ui.col({ … })`。
- 只有当列表自己滚动时，它才会让选中行保持在视野内，而它一旦具有 `max` 高度便会
  自行滚动。block 依据 `cx.rows` 设置 `max = { lines = … }`。它不需要 `resize`
  处理器：面板尺寸变化时 Tern 会再次运行 `view`，高度随之更新。

各行在标签中把仓库与编号放在标题之前，并把作者与时长放在右对齐的值中。列表项的
`detail` 只能占用标签留下的空间，因此过长的标题会遮住放在那里的任何内容。草稿以
`draft` 标记开头，并使用 muted 色调。

`age` 列需要 pull request 的创建时间，形式为 Unix 时间。`gh` 以 UTC 打印 ISO 8601，
而 `os.time` 传入表时读取的是本地时间，因此 `epoch` 用 days-from-civil 算法换算日期。

### 按键与保存状态 {#keys-and-saved-state}

| 按键 | 动作 |
| --- | --- |
| `↑`/`↓`、`k`/`j` | 移动 |
| `PageUp`/`PageDown`、`Home`/`End`、`g`/`G` | 跳转 |
| `Enter`、`o` | 打开该 pull request（`cx:open(url)`） |
| `r` | 立即刷新 |
| `d` | 显示或隐藏草稿 |

处理器忽略按住 Ctrl、Alt 或 Cmd 的按键，并对不使用的按键返回 `false`，因此这些
按键不产生渲染与保存开销；它处理的每个按键都返回 `true`。

是否显示草稿是该 block 唯一保存的状态：`save` 返回 `{drafts = …}`，重启后 `init`
从 `saved` 读回它。Tern 在每个处理器之后运行 `save`，只在结果发生变化时才存储，
因此 block 从不自己调用 `cx:save()`。

### window 半区 {#the-window-half}

window 半区添加一个命令面板命令并为它绑定快捷键：

```lua
tern.command({ id = "open", title = "Open review queue", icon = "merge", run = open_queue })
tern.bind("alt+shift+cmd+r", "plugin.review-queue.open")
```

每个打开的队列都会轮询 GitHub，因此 `open_queue` 先在 `cx.session:panes()` 中查找
标题为 “Review Queue…” 的面板并聚焦它。否则由
`cx:new_block("review-queue.queue", nil, "beside")` 在聚焦面板旁边打开一个。
当承载该窗口面板的 host 上没有这种 block 类型时（插件安装在窗口所在机器上，但
未安装在它所附着的远程 host 上），`new_block` 返回 `nil`，该命令会以 toast 说明
这一点。若某个插件绑定的组合键已被键盘预设占用，该绑定会被略过并在日志中给出
警告；参见[命令、按键与覆盖](../guides/commands.md)。

## 限制 {#limits}

- 搜索最多请求 100 条结果（`--limit=100`）。
- 新的评审请求会在下一次轮询时出现，最多延迟两分钟，或按 `r` 立即出现。
- 每个打开的队列各自轮询；该命令保证每个窗口只有一个队列，但其他窗口可以打开
  自己的队列。

## 代码 {#code}

`plugin.toml`:

```toml
schema = 1
id = "review-queue"
name = "Review Queue"
version = "1.0.0"
description = "Pull requests waiting for your review, from the GitHub CLI."
icon = "merge"
host = "host.luau"
window = "window.luau"

[[blocks]]
id = "queue"
title = "Review Queue"
```

`host.luau`:

```lua
--!strict
-- The `queue` block: open pull requests that request your review, read from
-- `gh search prs` and refreshed every two minutes.
--
-- Keys: ↑/↓ (or k/j) move, Home/End jump, Enter (or o) opens the pull
-- request, r refreshes, d shows or hides drafts.

local ui = tern.ui

local POLL_MS = 2 * 60 * 1000
local GH_TIMEOUT_MS = 30 * 1000
local INSTALL_URL = "https://cli.github.com"

local SEARCH = {
	"search",
	"prs",
	"--review-requested=@me",
	"--state=open",
	"--limit=100",
	"--json=number,title,url,repository,author,createdAt,isDraft",
}

-- `gh` by name first, then where package managers put it: a daemon started
-- by launchd or systemd often has a PATH without those directories.
local GH = {
	"gh",
	"/opt/homebrew/bin/gh",
	"/usr/local/bin/gh",
	"/home/linuxbrew/.linuxbrew/bin/gh",
	"/usr/bin/gh",
}

type Pr = {
	key: string,
	repo: string,
	number: number,
	title: string,
	author: string,
	url: string,
	created: number,
	draft: boolean,
}

-- Why the list could not be loaded: `missing` (no gh), `auth` (gh is not
-- signed in) or `failed` (anything else).
type Problem = { kind: string, text: string, detail: string? }

type State = {
	cx: BlockCx,
	prs: { Pr }?,
	shown: { Pr },
	cursor: string?,
	drafts: boolean,
	loading: boolean,
	fetched: number?,
	problem: Problem?,
	timer: TimerHandle?,
}

-- A pane ID survives Restart; the state object identifies this block run.
local running: { [number]: State } = {}

local function retire(state: State)
	if running[state.cx.pane] == state then
		running[state.cx.pane] = nil
	end
	if state.timer then
		state.timer:cancel()
		state.timer = nil
	end
	-- A pending process may retain its callback until the 30-second timeout.
	-- Release the old list now; its callback must not populate it again.
	state.loading = false
	state.prs = nil
	state.shown = {}
	state.cursor = nil
	state.problem = nil
	state.fetched = nil
end

-- Seconds since the epoch of an ISO 8601 UTC time (`2026-09-30T14:03:11Z`),
-- by the days-from-civil algorithm: `os.time` with a table reads local time.
local function epoch(iso: string): number?
	local y, m, d, hh, mm, ss = string.match(iso, "^(%d+)-(%d+)-(%d+)T(%d+):(%d+):(%d+)")
	if not (y and m and d and hh and mm and ss) then
		return nil
	end
	local year, month, day = tonumber(y) :: number, tonumber(m) :: number, tonumber(d) :: number
	if month <= 2 then
		year -= 1
	end
	local era = year // 400
	local yoe = year - era * 400
	local doy = (153 * (if month > 2 then month - 3 else month + 9) + 2) // 5 + day - 1
	local doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
	local days = era * 146097 + doe - 719468
	return days * 86400 + (tonumber(hh) :: number) * 3600 + (tonumber(mm) :: number) * 60 + (tonumber(ss) :: number)
end

-- How long ago `t` was, compactly: `12m`, `5h`, `3d`.
local function age(t: number): string
	local s = math.max(0, os.time() - t)
	if s < 3600 then
		return math.max(1, s // 60) .. "m"
	elseif s < 86400 then
		return s // 3600 .. "h"
	end
	return s // 86400 .. "d"
end

-- Check this run first, not just its pane: Restart reuses the pane ID.
-- Blocks have no close hook, so callbacks also retire a disappeared pane.
local function alive(state: State): boolean
	if running[state.cx.pane] ~= state then
		return false
	end
	for _, p in tern.pane.list() do
		if p.pane == state.cx.pane then
			return true
		end
	end
	retire(state)
	return false
end

-- The pull requests the list shows, oldest first, and a cursor on one of them.
local function refilter(state: State)
	local shown: { Pr } = {}
	local prs: { Pr } = state.prs or {}
	for _, pr in prs do
		if state.drafts or not pr.draft then
			table.insert(shown, pr)
		end
	end
	table.sort(shown, function(a, b)
		return a.created < b.created
	end)
	state.shown = shown
	local found = false
	for _, pr in shown do
		found = found or pr.key == state.cursor
	end
	if not found then
		state.cursor = if shown[1] then shown[1].key else nil
	end
end

local function index_of(state: State): number
	for i, pr in state.shown do
		if pr.key == state.cursor then
			return i
		end
	end
	return 0
end

local function first_lines(text: string, n: number): string
	local out = {}
	for line in string.gmatch(text, "[^\n]+") do
		table.insert(out, line)
		if #out == n then
			break
		end
	end
	return table.concat(out, "\n")
end

-- What a failed `gh` run means.
local function problem_of(result: ProcessResult): Problem
	if result.timed_out then
		return { kind = "failed", text = "gh did not answer within 30 seconds." }
	end
	local err = result.stderr
	local auth = result.status == 4
		or string.find(err, "gh auth login", 1, true) ~= nil
		or string.find(err, "GH_TOKEN", 1, true) ~= nil
		or string.find(err, "HTTP 401", 1, true) ~= nil
	if auth then
		return { kind = "auth", text = "The GitHub CLI is not signed in.", detail = first_lines(err, 3) }
	end
	return {
		kind = "failed",
		text = "gh exited with status " .. result.status .. ".",
		detail = first_lines(err, 8),
	}
end

-- The pull requests in `gh`'s JSON, or nil when it isn't the expected list.
local function parse(stdout: string): { Pr }?
	local ok, data = pcall(tern.json.decode, stdout)
	if not ok or type(data) ~= "table" then
		return nil
	end
	local prs: { Pr } = {}
	for _, item in data do
		local repo = if type(item.repository) == "table" then item.repository.nameWithOwner else nil
		local number = tonumber(item.number)
		if type(repo) == "string" and number and type(item.url) == "string" then
			table.insert(prs, {
				key = repo .. "#" .. number,
				repo = repo,
				number = number,
				title = tostring(item.title or ""),
				author = if type(item.author) == "table" then tostring(item.author.login) else "?",
				url = item.url,
				created = epoch(tostring(item.createdAt or "")) or os.time(),
				draft = item.isDraft == true,
			})
		end
	end
	return prs
end

-- Starts `gh` with `args`, trying each place it may be installed; the spawn
-- error of the last attempt when none starts.
local function run_gh(args: { string }, done: (ProcessResult) -> ()): string?
	local last = "gh is not on this machine's PATH"
	for _, gh in GH do
		if gh == "gh" or tern.fs.exists(gh) then
			local argv: { string } = { gh }
			for _, a in args do
				table.insert(argv, a)
			end
			local opts: ProcessOptions = {
				timeout_ms = GH_TIMEOUT_MS,
				env = { GH_PROMPT_DISABLED = "1", GH_NO_UPDATE_NOTIFIER = "1", NO_COLOR = "1" },
			}
			local ok, err = pcall(function()
				tern.process.run(argv, opts, function(result: ProcessResult, _)
					done(result)
				end)
			end)
			if ok then
				return nil
			end
			last = tostring(err)
		end
	end
	return last
end

-- Loads the list in the background; the callback re-renders the block.
local function refresh(state: State)
	if not alive(state) or state.loading then
		return
	end
	state.loading = true
	local spawn_error = run_gh(SEARCH, function(result)
		if not alive(state) then
			return
		end
		state.loading = false
		if result.status ~= 0 then
			state.problem = problem_of(result)
		else
			local prs = parse(result.stdout)
			if prs then
				state.prs = prs
				state.problem = nil
				state.fetched = os.time()
				refilter(state)
			else
				state.problem = {
					kind = "failed",
					text = "gh printed something other than a list of pull requests.",
					detail = first_lines(result.stdout, 4),
				}
			end
		end
		state.cx:render()
	end)
	if spawn_error then
		state.loading = false
		state.problem = { kind = "missing", text = "Tern could not start the GitHub CLI.", detail = spawn_error }
	end
end

-- One pending timer per live run, canceled explicitly when it is replaced.
local function poll(state: State)
	if not alive(state) or state.timer then
		return
	end
	state.timer = tern.timer(POLL_MS, function()
		if not alive(state) then
			return
		end
		state.timer = nil
		refresh(state)
		state.cx:render()
		poll(state)
	end)
end

local function button(label: string, act: string, tone: string): Node
	local node = ui.badge(label, tone)
	local p: { [string]: any } = node.p or {}
	p.actions = { click = act }
	node.p = p
	return node
end

-- The full-pane view of a problem when there is no list to show.
local function problem_view(problem: Problem): Node
	local heads = {
		missing = "GitHub CLI not found",
		auth = "GitHub CLI not signed in",
		failed = "Could not load review requests",
	}
	local help = {
		missing = "Review Queue runs `gh search prs` on the machine that runs your panes. "
			.. "Install the GitHub CLI there, then press **r**.",
		auth = "Run `gh auth login` in a shell on this machine, then press **r**.",
		failed = "Press **r** to try again.",
	}
	local children: { Node } = { ui.md(problem.text .. " " .. (help[problem.kind] or "")) }
	if problem.detail and problem.detail ~= "" then
		table.insert(children, ui.code(problem.detail))
	end
	local buttons: { Node } = { button("Retry", "retry", "accent") }
	if problem.kind == "missing" then
		table.insert(buttons, button("Install guide", "install", "neutral"))
	end
	table.insert(children, ui.row(buttons))
	local card = ui.card({ ui.span(heads[problem.kind] or "Review Queue", "strong") }, children)
	local p: { [string]: any } = card.p or {}
	p.tone = "error"
	card.p = p
	return card
end

-- The list is keyed `queue`: its id is `main.queue` and each row's
-- `main.queue.<owner/repo#number>`, the ids `selected` and its events use.
local LIST_ID = "main.queue."

-- How many rows the list shows before it scrolls itself. A list with a
-- `max` height keeps its selected row in view; without one, `main` scrolls
-- and the cursor can leave the screen. List rows are about a third taller
-- than the pane's cells, and the dock takes about four cells.
local function list_lines(cx: BlockCx): number
	return math.max(4, math.floor((cx.rows - 4) * 0.72))
end

local function list_view(state: State): Node
	local items: { Item } = {}
	for _, pr in state.shown do
		-- A long title would squeeze out a `detail`, so the repository leads
		-- the label and the author sits in the right-aligned value.
		local label: { Span | string } = {}
		if pr.draft then
			table.insert(label, ui.span("draft  ", "warning"))
		end
		table.insert(label, ui.span(pr.repo .. "#" .. pr.number .. "  ", "muted"))
		table.insert(label, ui.span(pr.title))
		table.insert(items, {
			label = label,
			value = { ui.span("@" .. pr.author .. "  ", "muted"), ui.span(age(pr.created), "muted num") },
			icon = "merge",
			tone = if pr.draft then "muted" else nil,
		})
	end
	local list = ui.list(items)
	local kids = list.c or {}
	for i, pr in state.shown do
		local p: { [string]: any } = kids[i].p or {}
		p.key = pr.key
		kids[i].p = p
	end
	local p: { [string]: any } = list.p or {}
	p.key = "queue"
	p.selected = if state.cursor then LIST_ID .. state.cursor else nil
	p.empty = { ui.span("No pull requests are waiting for your review.", "muted") }
	p.max = { lines = list_lines(state.cx) }
	list.p = p
	return list
end

-- The dock: counts, freshness, a refresh problem, the keys.
local function dock_view(state: State): Node
	local total = if state.prs then #state.prs else 0
	local hidden = total - #state.shown
	local status: { Span | string } = { ui.span(#state.shown .. " to review", "strong") }
	if hidden > 0 then
		table.insert(status, ui.span("  " .. hidden .. " drafts hidden", "muted"))
	end
	if state.loading then
		table.insert(status, ui.span("  refreshing…", "muted"))
	elseif state.fetched then
		table.insert(status, ui.span("  updated " .. os.date("%H:%M", state.fetched), "muted"))
	end
	local lines: { Node } = { ui.text(status) }
	local problem = state.problem
	if problem then
		table.insert(lines, ui.text({ ui.span(problem.text, "warning"), ui.span("  showing the last list", "muted") }))
	end
	table.insert(
		lines,
		ui.text({
			ui.span("↑↓ move  ⏎ open  r refresh  d " .. (if state.drafts then "hide" else "show") .. " drafts", "dim"),
		})
	)
	return ui.col({ ui.lines(lines) })
end

local function open_selected(state: State, cx: BlockCx)
	local pr = state.shown[index_of(state)]
	if pr then
		cx:open(pr.url)
	end
end

local function move(state: State, to: number)
	local pr = state.shown[math.clamp(to, 1, math.max(1, #state.shown))]
	if pr then
		state.cursor = pr.key
	end
end

tern.block.define("queue", {
	init = function(cx: BlockCx, _args: { string }, saved: any): State
		local previous = running[cx.pane]
		if previous then
			retire(previous)
		end
		local state: State = {
			cx = cx,
			prs = nil,
			shown = {},
			cursor = nil,
			drafts = type(saved) == "table" and saved.drafts == true,
			loading = false,
			fetched = nil,
			problem = nil,
			timer = nil,
		}
		running[cx.pane] = state
		refresh(state)
		poll(state)
		return state
	end,

	title = function(state: State): string?
		if state.prs then
			return "Review Queue (" .. #state.shown .. ")"
		end
		return "Review Queue"
	end,

	view = function(state: State, _cx: BlockCx): BlockView
		local main: Node
		if state.prs then
			main = list_view(state)
		elseif state.problem then
			main = problem_view(state.problem)
		else
			main = ui.progress(nil, "Loading review requests…")
		end
		-- A region draws its root node's children, not the root itself (a
		-- list there would lose its selection and events), so the view
		-- sits inside a column.
		return { main = ui.col({ main }), dock = if state.prs then dock_view(state) else nil }
	end,

	key = function(state: State, key: Key, cx: BlockCx): boolean?
		if key.ctrl or key.alt or key.meta then
			return false
		end
		local i = index_of(state)
		local k = key.text or key.name
		if key.name == "up" or k == "k" then
			move(state, i - 1)
		elseif key.name == "down" or k == "j" then
			move(state, i + 1)
		elseif key.name == "page_up" then
			move(state, i - 10)
		elseif key.name == "page_down" then
			move(state, i + 10)
		elseif key.name == "home" or k == "g" then
			move(state, 1)
		elseif key.name == "end" or k == "G" then
			move(state, #state.shown)
		elseif key.name == "enter" or k == "o" then
			open_selected(state, cx)
		elseif k == "r" then
			refresh(state)
		elseif k == "d" then
			state.drafts = not state.drafts
			refilter(state)
		else
			return false
		end
		return true
	end,

	event = function(state: State, ev: UiEvent, cx: BlockCx)
		if ev.ev == "action" and ev.act == "retry" then
			refresh(state)
		elseif ev.ev == "action" and ev.act == "install" then
			cx:open(INSTALL_URL)
		elseif (ev.ev == "select" or ev.ev == "activate") and type(ev.item) == "string" then
			state.cursor = string.sub(ev.item, #LIST_ID + 1)
			if ev.ev == "activate" then
				open_selected(state, cx)
			end
		end
	end,

	save = function(state: State): any
		return { drafts = state.drafts }
	end,
})
```

`window.luau`:

```lua
--!strict
-- The window half: a palette command and a key bind that open the queue, or
-- focus the one already open in this window.

local KIND = "review-queue.queue"

local function open_queue(cx: WindowCx)
	-- One queue per window is enough: each open block polls GitHub.
	for _, pane in cx.session:panes() do
		if string.sub(pane.title, 1, #"Review Queue") == "Review Queue" then
			cx.layout:focus(pane.pane)
			return
		end
	end
	if cx:new_block(KIND, nil, "beside") == nil then
		cx:toast("error", "Review Queue is not loaded on this host", "Install the plugin where your panes run.")
	end
end

tern.command({
	id = "open",
	title = "Open review queue",
	icon = "merge",
	run = open_queue,
})

tern.bind("alt+shift+cmd+r", "plugin.review-queue.open")
```
