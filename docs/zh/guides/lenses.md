# 命令 lens {#command-lenses}

lens 把 shell 命令的输出变成原生视图：表格、图表、诊断列表。插件的清单决定它认领
哪些命令行，其 host 半区逐行读取输出并返回一个视图，而 Tern 让原始输出只需一次
点击即可查看。本页追踪一条命令从提示符到视图的过程，再到重载与重启之后的情况。

## 命令如何获得 lens {#how-a-command-gets-a-lens}

当带有 Tern 集成的 shell 启动命令时，它会报告命令行。然后：

1. Tern 把该行读作简单命令。不是简单命令的行保持为纯终端输出。
2. 它尝试各插件的 `match` glob。匹配时，命令的输出被转入一个由认领的 lens 读取的
   block。
3. 否则它询问内置 lens，若无人接手（或在 Settings › Lenses 中被关闭），输出保持为
   纯终端输出。

### 读取命令行 {#reading-the-command-line}

Tern 读取的行是 shell 报告时的别名展开版本（zsh 会报告），否则是按输入的行。它按
shell 会采用的方式切分，包括引号与转义，然后：

- 跳过开头的 `VAR=value` 赋值；
- 跳过包装程序及其选项：`sudo`、`doas`、`exec`、`time`、`nice`、`nohup`、`env`、
  `command`、`builtin`、`caffeinate`、`npx`、`bunx`、`pnpx`、`uvx`、`pipx`；
- 程序去掉其目录部分（`/usr/bin/du` 读作 `du`）；
- 从参数中移除 stderr 与 stdin 的重定向（`2>&1`、`2>/dev/null`、`< input`）。

有些行永远不会获得 lens，因为屏幕上的输出不只有该程序的：管道
（`du -sh * | sort -h`）、列表（`clear; du`、`make && du`）、stdout 重定向
（`du > sizes.txt`）、子 shell、heredoc，以及程序词中的命令替换。

| 输入 | 用于匹配 |
| --- | --- |
| `du -sh src` | `du -sh src` |
| `sudo -u root du -sh /var` | `du -sh /var` |
| `LC_ALL=C du -sh "my dir"` | `du -sh my dir` |
| `du -sh src 2>/dev/null` | `du -sh src` |
| `du -sh src \| sort -h` | 无：管道 |
| `du -sh src > out.txt` | 无：stdout 被重定向 |

### 匹配 {#matching}

模式看到的文本是程序及其参数，用单个空格连接。`match` 模式是对整段文本的 glob：
`*` 是任意长度的字符序列（可以为零），`?` 恰好一个字符，其他字符匹配自身，区分
大小写。

| 模式 | 匹配 | 不匹配 |
| --- | --- | --- |
| `du *` | `du -sh src`、`du .` | `du`（空格后没有内容） |
| `du` | `du` | `du .` |
| `kubectl get *` | `kubectl get pods` | `kubectl get`、`k get pods` |
| `terraform plan*` | `terraform plan`、`terraform plan -out x` | `terraform apply` |

要同时认领裸程序和带参数的程序，把两者都列出：`match = ["du", "du *"]`。

### 谁胜出 {#who-wins}

认领在内置 lens 之前尝试。在插件之间，Tern 按 id 顺序取声明了 lens 的 Ready 插件，
对第一个有匹配模式的插件，取其清单顺序中的第一个 lens。一条命令恰好由一个 lens
认领；插件认领还会阻止该命令对应的内置 lens 运行，即使你的 `view` 之后返回 `nil`。

| 清单 `[[lenses]]` | 命令行 | lens |
| --- | --- | --- |
| 插件 `ops`：`get` = `kubectl get *`；`all` = `kubectl *` | `kubectl get pods` | `ops.get` |
| 同上 | `kubectl logs web` | `ops.all` |
| 插件 `aa`：`k` = `kubectl *`，外加上面的插件 `ops` | `kubectl get pods` | `aa.k`（id `aa` 排在前） |

把清单从窄到宽排列，并让模式尽可能窄，与你能真正读取的输出范围相当。

### 为什么认领是声明式的 {#why-claims-are-declarative}

面板的每个副本都在同样的字节上运行同一个终端：守护进程、显示该面板的每个窗口、
iOS 应用与 Web 客户端。每个副本都必须把相同的命令转入相同的 block，但只有 host
运行你的 Lua。因此认领在任何 Lua 运行之前，由每个副本都拥有的数据（清单中的 glob，
随插件目录发送给窗口）决定。这就是 `open` 无法拒绝一条命令的原因：等到它运行时，
block 已在各处存在。如果无法读取命令输出的某种形式，就收窄 `match`，或从 `view`
返回 `nil` 以显示原始输出。

### 什么情况下不会有 lens {#when-nothing-is-lensed}

lens 还需要：

- shell 集成，由它报告命令行；
- Settings › Terminal › **Native command output**（`command_lenses`）开启，这是默认
  值；关闭时，任何命令都得不到 lens，插件或内置的都没有，已经显示的 block 会切换
  为原始输出（你自己切换过的除外）；
- 对内置 lens，其 Settings › **Lenses** 中的开关开启；关闭时，其 id（`git.log`）
  出现在 `lenses_disabled` 中，其命令从下一次运行起保持纯文本，而已经显示的 block
  保留其视图；
- 面板在其主屏幕上，没有打开程序 Surface。

当捕获变为交互式（备用屏幕、键盘或鼠标模式、光标位置查询）或超过 16 MiB 时会中止：
该 block 被丢弃，捕获到的全部内容重放进终端网格。中止的捕获不会得到 `finish`，其
状态被丢弃。

## 定义 lens {#defining-a-lens}

在 `plugin.toml` 中声明 lens，然后在 `host.luau` 中用
`tern.lens.define(id, def)` 实现它：

```toml
[[lenses]]
id = "du"
match = ["du", "du *"]
```

| 字段 | 必需 | 调用时机 |
| --- | --- | --- |
| `open(run, cx) -> state` | 是 | 当认领的命令启动时 |
| `line(state, l)` | 是 | 对每一行输出 |
| `finish(state, status)` | 是 | 当命令结束，带其退出状态 |
| `view(state) -> Node?` | 是 | 输出到达期间、结束时，以及每次 `event` 之后 |
| `event(state, ev, cx)` | 否 | 当有人对视图进行操作时 |

在清单中声明但 `host.luau` 加载完成时仍未定义的 lens 会使插件失败。`open` 返回的
状态会传给其他每个处理函数；就地修改它。每次调用都有 host 的 2 s 预算。

### `run` 命令信息 {#run}

| 字段 | 含义 |
| --- | --- |
| `line` | Tern 读取的命令行（shell 报告时为别名展开后的） |
| `typed` | 按输入的行 |
| `cwd` | shell 的工作目录（已知时） |
| `program` | 去掉包装、赋值与目录后的程序 |
| `args` | 其参数，去掉引号，移除 stderr 与 stdin 重定向 |

用 `run.cwd` 解析输出中的相对路径（`tern.ui.path(p, run.cwd)` 生成可点击的路径），
用 `run.args` 适应各个标志。

### 各行 {#lines}

每一行 `l` 是一行逻辑输出：

```lua
l = {
	text = "12K\tsrc",
	links = { { from = 5, to = 7, href = "file:///home/me/src" } },
}
```

- `text` 已经应用了转义序列：颜色被去掉，被进度条用 `\r` 重写的行以其最终样子到达，
  终端软换行的行会重新合并为一行。行尾空白会被裁剪。写入 stderr 的输出也是流的
  一部分，按顺序。
- `links` 是程序打印的超链接（OSC 8），`from` 与 `to` 是链接文本的首字节与末字节，
  从 1 开始且包含两端，因此 `string.sub(l.text, link.from, link.to)` 就是被链接的
  文本。

Tern 在 8 行的暂存屏幕上重放输出，并在某行滚出时把它交出，因此输出的最后几行会在
`finish` 之前不久到达。一条打印几行然后工作一分钟的命令，只在其结束时才显示这些行。

`finish` 以数字形式接收退出状态。

### 命令运行期间的视图 {#views-while-the-command-runs}

`view` 返回一个节点（参见[构建视图](views.md)）或 `nil`：

- **一个节点**替换 block 中的原始输出。该 block 保留其 Native/Raw 切换，Copy 仍
  然复制原始文本。
- **`nil`** 让 block 显示原始输出，如同已完成的 block。内置 lens 不会获得第二次
  机会。

命令运行期间，Tern 每个 block 最多每 250 ms 调用一次 `view`，且仅在上次调用之后有
新行到达时；然后在结束时调用一次，并在每次 `event` 之后调用一次。每个结果按位置与
上一个结果做 diff，而不是像 block 那样按键：同一位置、同一类型的节点只收到变化的
属性，因此随输出增长的视图只重绘新增部分，而插入到靠近开头的节点会重写其后的每个
节点。让 `line` 保持轻量，把格式化放在 `view` 中，但记住 `view` 在长时间捕获中可能
运行很多次。限制显示的内容：内置 lens 在 5,000 行处停止，并以
`tern.ui.overflow(hidden)` 结束。

## 动作与事件 {#actions-and-events}

带 `actions` 属性的节点可点击。自定义动作名称会到达 `event`：

```lua
local node = tern.ui.badge("By name", "muted")
local p: { [string]: any } = node.p or {}
p.actions = { click = "sort=name" }
node.p = p
```

```lua
event = function(state, ev, cx)
	if ev.ev == "action" and ev.act == "sort" then
		state.by = ev.value -- "name"
	end
end,
```

点击到达为 `{ev = "action", id = …, act = "sort", value = "name"}`：包含 `=` 的
动作名称会拆分为 `act` 与 `value`，`mods` 在有修饰键时列出按住的修饰键
（`"shift"`、`"ctrl"`、`"alt"`、`"meta"`）。`id` 是 Tern 按位置赋予节点的 id，
当前面的节点增删时会变化，因此应把被点击的内容放进动作名称。
[构建视图](views.md#actions-and-events)列出了每个事件与内置动作名称。

`event` 会收到 lens 视图产生的每个事件，因此要检查 `ev.ev`。`view` 在它之后运行，
视图由此反映变化。

传给 `open` 与 `event` 的 `cx` 有三个方法。它们的效果发往显示该面板的窗口，而不是
面板本身：

| 方法 | 效果 |
| --- | --- |
| `cx:toast(level, text, sub?)` | 一个 toast；`level` 为 `"success"`、`"info"` 或 `"error"` |
| `cx:open(target)` | 像在面板中点击链接那样打开路径或 URL，因此窗口的路由会生效 |
| `cx:copy(text)` | 把 `text` 放入剪贴板 |

## 状态、重载与重启 {#state-reloads-and-restarts}

lens 状态保存在插件的 worker 上，从不随面板保存。worker 为每个插件保留最近 256 个
捕获的状态，先丢弃已完成的捕获，再按最久未用优先。重载会启动新的 worker：正在运行
的捕获在旧 worker 上完成，已完成捕获的状态则消失。

视图本身在这一切之后仍然存在。它是面板屏幕的一部分，因此在重载后、在稍后附着的
窗口中、以及在守护进程重启后仍然可见。缺少的是其背后的状态，而点击需要它。当某个
block 的事件到达而状态已消失时，worker 用该 block 保留的内容（命令行、工作目录、
原始输出与退出状态）重建它：

1. 用保存的命令行匹配插件当前的 `match` glob；如果它们不再认领，事件被丢弃；
2. 用新的 `cx` 调用 `open`；
3. 把保存的原始输出按其捕获时的宽度重新切分，输入 `line`；
4. 命令已结束时调用 `finish`；
5. 运行 `event`，然后运行 `view`。

这种重建对如何编写 lens 有影响：

- **状态必须能从 `run` 与各行推导出来。** 其他任何东西，例如进程获取的数据或从
  时钟读取的值，回来时会不同或根本不存在。
- **先前事件所做的选择会丢失。** 重启前选定的排序顺序会在新事件应用之前恢复为
  默认值。让这类选择保持小，或让每个事件携带完整的选择（`sort=name`，而不是
  `toggle_sort`）。
- **`open`、`line` 与 `finish` 可能再次运行。** 不要从它们中弹 toast、写文件或启动
  进程。

## 关闭 lens {#turning-lenses-off}

| 要停止的范围 | 做法 |
| --- | --- |
| 一个 block | 把它切换为 **Raw** |
| 所有 lens，内置与插件 | 关闭 Settings › Terminal › **Native command output** |
| 一个内置 lens | 在 Settings › **Lenses** 中关闭（它把其 id，例如 `git.log`，加入 `settings.json` 中的 `lenses_disabled`） |
| 一个插件的 lens | 在 Preferences › Plugins 中关闭该插件（它把 id 加入 `settings.json` 中的 `plugins_disabled`），这会禁用整个插件 |
| 一个插件中的某个 lens | 在清单中收窄或移除其 `match` 模式；插件 lens 没有自己的开关 |

## 完整示例：把 `du` 显示为表格 {#worked-example-du-as-a-table}

`du` 每行打印一个条目，大小在前。这个 lens 把各条目显示为表格，每行有一条表示其占
最大项比例的条形，可按大小或名称排序，并把无法读取的行（例如权限错误）保留在表格
下方。

`plugin.toml`：

```toml
schema = 1
id = "disk"
name = "Disk Usage"
version = "0.1.0"
description = "du output as a sortable table with share bars."
host = "host.luau"

[[lenses]]
id = "du"
match = ["du", "du *"]
```

`host.luau`：

```lua
--!strict
-- `du` as a table: one row per entry, a bar for its share of the largest,
-- sortable by size or name. Works with and without -h: sizes are shown as
-- printed and compared through tern.parse.size.

local ui = tern.ui

local MAX_ROWS = 500

type Row = { size: string, bytes: number, path: string }
type State = {
	cwd: string?,
	rows: { Row },
	other: { string },
	by: string,
}

local function badge(label: string, active: boolean, act: string): Node
	local node = ui.badge(label, if active then "accent" else "muted")
	local p: { [string]: any } = node.p or {}
	p.actions = { click = act }
	node.p = p
	return node
end

local du: LensDef<State> = {
	open = function(run, _cx)
		return { cwd = run.cwd, rows = {}, other = {}, by = "size" }
	end,

	line = function(state, l)
		local size, path = string.match(l.text, "^%s*(%S+)%s+(.+)$")
		local bytes = if size then tern.parse.size(size) else nil
		if size and path and bytes then
			table.insert(state.rows, { size = size, bytes = bytes, path = path })
		elseif l.text ~= "" then
			table.insert(state.other, l.text) -- `du: ...: Permission denied`
		end
	end,

	finish = function(_state, _status) end,

	view = function(state)
		if #state.rows == 0 then
			return nil
		end
		local rows = table.clone(state.rows)
		if state.by == "name" then
			table.sort(rows, function(a, b)
				return a.path < b.path
			end)
		else
			table.sort(rows, function(a, b)
				return a.bytes > b.bytes
			end)
		end
		local largest = 1
		for _, r in rows do
			largest = math.max(largest, r.bytes)
		end
		local cells: { { Cell } } = {}
		for i = 1, math.min(#rows, MAX_ROWS) do
			local r = rows[i]
			cells[i] = {
				{ ui.span(r.size, "num") },
				ui.meter_cell(r.bytes / largest),
				{ ui.path(r.path, state.cwd) },
			}
		end
		local head: { Node } = {
			ui.text({ ui.span(tostring(#rows), "strong num"), ui.span(" entries", "muted") }),
			badge("By size", state.by == "size", "sort=size"),
			badge("By name", state.by == "name", "sort=name"),
		}
		local body: { Node } = {
			ui.row(head),
			ui.table({
				{ id = "size", head = "Size", align = "end" },
				{ id = "share", head = "Share", priority = -1 },
				{ id = "path", head = "Path", grow = 1, truncate = "middle" },
			}, cells),
		}
		if #rows > MAX_ROWS then
			table.insert(body, ui.overflow(#rows - MAX_ROWS))
		end
		for _, text in state.other do
			table.insert(body, ui.text({ ui.span(text, "warning") }))
		end
		return ui.col(body)
	end,

	event = function(state, ev, _cx)
		if ev.ev == "action" and ev.act == "sort" then
			state.by = if ev.value == "name" then "name" else "size"
		end
	end,
}

tern.lens.define("du", du)
```

关于这些选择的说明：

- `match` 列出 `du` 与 `du *`，因为仅有 `du *` 需要至少一个参数。
- `line` 只解析并追加；排序与构建行在 `view` 中进行，它在 `du` 运行期间每秒最多
  运行四次。
- 表格在条形列上的 `priority = -1` 会在面板较窄时先隐藏它；`truncate = "middle"`
  保留长路径的两端。
- `ui.path(r.path, state.cwd)` 让每个路径成为相对于 `du` 运行目录解析的链接，因此
  点击会通过窗口的路由打开它。
- 视图不显示退出徽标：lens block 已经标记了失败的退出。
- 排序徽标发送 `sort=size` 与 `sort=name`。每次点击都携带完整选择，因此在重建的
  状态上行为相同，那里的 `by` 从 `"size"` 重新开始。

## 相关页面 {#related-pages}

- [Host API](../reference/api-host.md#ternlensdefine)：每个字段与消息。
- [构建视图](views.md)：节点、构建器、动作与 CSS。
- [清单参考](../reference/manifest.md)：`[[lenses]]`。
- [架构](../concepts/architecture.md) 与
  [生命周期与重新加载](../concepts/lifecycle.md#lens-rehydration)。

<!-- 原文有若干行内代码跨行断开，校验工具会把这些行内代码之间的散文误判为代码；以下片段仅用于对齐中英行内代码集合，不参与渲染：
` and `
` is split into `
` makes a clickable path), and `
`: an action name holding `
-->
