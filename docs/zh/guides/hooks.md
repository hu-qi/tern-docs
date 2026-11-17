# Host 钩子与 spawn 过滤器 {#host-hooks-and-the-spawn-filter}

host 钩子让插件的 host 半区对机器上各面板的行为作出反应：命令启动或结束、目录或标题变化、程序退出。spawn 过滤器更进一步，在 shell 启动之前改写它的程序、参数、目录与环境。本页介绍这些事件、其处理器可以做什么、过滤器的约定，以及这一切在哪里运行。

## 钩子在哪里运行 {#where-hooks-run}

钩子属于 host 半区，而 host 半区运行在面板所在的位置：

- **随会话守护进程运行**（常见情形），每个插件的 host 半区都在守护进程中自己的 worker 线程上运行。钩子能听到该守护进程运行的每个面板，无论哪个窗口显示它，并且在没有任何窗口打开时仍然继续运行。
- **没有守护进程时**，当窗口自行运行其面板，该窗口为自己的面板运行各 host 半区及其钩子。你的代码不会有任何变化，但 `tern.pane.list()` 与这些事件只覆盖该窗口的面板，effect 也只到达该窗口。
- **远程 host** 为自己的面板运行自己插件的 host 半区。你机器的 host 半区从不会听到远程 host 的面板；你的 window 半区会通过窗口事件听到。
- **iOS** 不运行任何 host 半区。

由于 host 半区在守护进程中运行，其中的 `tern.getenv`、`tern.fs` 与 `tern.process` 看到的是守护进程的环境与机器，而不是某个窗口的。

## 事件 {#events}

在 `host.luau` 中，`tern.on(name, fn)` 订阅 `fn`：

| 事件 | 触发时机 | 载荷 |
| --- | --- | --- |
| `command_started` | shell 报告某条命令行开始运行 | `{pane, line, cwd?}` |
| `command_finished` | 该命令结束 | `{pane, line, status, took_ms}` |
| `cwd` | 面板的工作目录变化 | `{pane, path}` |
| `title` | 面板的标题变化 | `{pane, title}` |
| `pane_exited` | 面板中的程序退出 | `{pane, status}` |
| `spawn` | shell 面板即将启动 | spawn 规格；见[下文](#the-spawn-filter) |

- `pane` 是该面板在此 host 上的 id，即 `tern.pane.write` 所接受的 id。
- `line` 是 shell 报告的命令行，按输入时的样子（别名不展开）。`cwd` 是命令启动时 shell 所在的目录（已知时）。
- `status` 是退出状态；`took_ms` 是命令运行了多久，以毫秒计，由 host 测量。
- `command_started` 与 `command_finished` 需要 shell 集成，由它报告命令行。`command_finished` 只对启动已被看到的命令触发。

host 不认识的事件名会在 `tern.on` 调用处抛出错误。同一插件的处理器在其 worker 上按注册顺序运行。每个插件都有自己的 worker，因此不同插件的处理器并发运行，顺序不确定。每次处理器调用都有 host 的 2 s 预算；慢的那一个只会拖慢它自己的插件。

## 钩子中的 `cx` {#the-hook-cx}

事件处理器收到 `(ev, cx)`。`cx` 会把 effect 发送到该事件所属面板所在的窗口，即显示该面板所在会话的每个窗口：

| 方法 | 效果 |
| --- | --- |
| `cx:toast(level, text, sub?)` | 一个 toast；`level` 为 `"success"`、`"info"` 或 `"error"` |
| `cx:open(target)` | 以在面板中点击链接的方式打开路径或 URL，因此每个窗口的路由都会生效 |
| `cx:copy(text)` | 把 `text` 放入剪贴板 |

没有窗口附着时，effect 会被丢弃。钩子不能触碰布局、命令面板或窗口的状态：那是 window 半区的职责（窗口事件见[布局与工作区](layout.md#window-events)）。

## 向面板写入 {#writing-to-panes}

`tern.pane.write(pane, text)` 把 `text` 写入面板的伪终端，如同键入。以 `"\r"` 结尾即可运行命令；省略 `"\r"` 则把文本留在提示符上，供用户确认。写入在处理器返回之后应用，已不存在的面板会被忽略。

`tern.pane.list()` 以 `{pane, cwd?, program, title, busy}` 记录的形式，返回该 host 上所有程序尚未退出的面板。`program` 是程序名称，对插件 block 则是该 block 类型；block 的面板从其 `init` 运行之前就会被列出。`busy` 报告的是正在运行的、经 shell 集成的命令，而非一般进程活动。

```lua
local function title_of(pane: number): string?
	for _, info in tern.pane.list() do
		if info.pane == pane then
			return info.title
		end
	end
	return nil
end
```

向 shell 写入功能强大，也很容易出错：用户可能正在输入，或者正在运行全屏程序。与其直接运行命令，更宜把它留在提示符上；并且只在该面板中的用户刚做了某件事、需要回应时才写入。

## spawn 过滤器 {#the-spawn-filter}

`spawn` 处理器在该 host 上每个 shell 面板启动之前运行（插件 block 不启动进程，因此永远不会到达它）。它收到规格并返回要使用的规格，返回 `nil` 表示保持不变：

```lua
tern.on("spawn", function(spec: SpawnSpec): SpawnSpec?
	spec.env.EDITOR = "nvim"
	return spec
end)
```

| 字段 | 内容 |
| --- | --- |
| `program` | 程序，已解析：登录 shell（例如 `/bin/zsh`），除非该面板被要求运行其他程序 |
| `args` | 其参数，包含守护进程添加的登录标志 |
| `cwd` | 面板将启动于其中的目录 |
| `env` | Tern 为该面板设置的变量，按名称 |

`env` 只包含 Tern 在面板继承的环境之上添加的内容，不包含继承的环境本身。在守护进程的面板中，这些是 `TERN_IDENTITY`、`TERN_PANE`、`TERN_PANE_SOCKET`、`TERN_WINDOW_KEY`、`TERN_WINDOW_SOCKET`（空）、`TERN_EXE`、`TERN_LENSES`、`TERN_COMPLETE` 与 `TERN_BLOB_DIR`。因此你可以添加变量并覆盖这些变量，但无法移除继承的变量：删除某个键只是让 Tern 不再设置它。继承的值请用 `tern.getenv` 读取。

返回的表如何被应用：

- `program` 与 `args` 缺失时保持原值。
- `cwd` 缺失或不是目录时被忽略：面板会在原本的位置启动。守护进程会展开开头的 `~`。
- `env` 被当作完整集合：你删除的键不会被设置，新增的键会被添加。请把收到的规格修改后返回，而不是返回一个只含你改动的新表。

守护进程会等待该过滤器，因此它是同步且短暂的：

- **顺序。** 带有 `spawn` 处理器的插件按插件 id 顺序运行，每个都收到前一个的结果。同一插件中的多个处理器按注册顺序运行。
- **每个插件 50 ms。** 面板对每个插件的回答最多等待 50 ms，从请求入队时开始计时，因此 worker 花在完成另一个处理器上的时间也计入。迟到的回答会被丢弃，面板按原样的规格启动，日志会写 `plugin spawn filter took over 50 ms; skipped`。
- **不等待进程或请求。** `tern.process.run` 与 `tern.fetch` 会在面板启动之后才回调。请使用 `tern.fs`、`tern.kv` 与字符串处理，并提前缓存任何慢操作。
- **失败。** 抛出错误、或返回既非表也非 `nil` 的处理器会保持原规格不变，并将消息以 toast 形式发送到每个窗口，因为此时还没有面板可供定向。

当窗口在没有守护进程的情况下运行其面板时，该过滤器同样会运行。此时 `env` 改为持有该窗口的变量（`TERN_WINDOW_SOCKET`、`TERN_WINDOW_PANE`、`TERN_EXE`、`TERN_LENSES`、`TERN_COMPLETE`、`TERN_BLOB_DIR`）。

## 完整示例：projects {#worked-example-projects}

这个 host 半区为每个新 shell 提供 `TERN_PROJECT`，即其启动时所在 git 仓库的名称；对运行超过 30 秒的命令在结束时显示 toast，并记住最近 20 条；还会捕获 `gti` 拼写错误，把修正后的命令放到提示符上。

`plugin.toml`：

```toml
schema = 1
id = "projects"
name = "Projects"
version = "0.1.0"
description = "TERN_PROJECT in new shells, toasts for slow commands."
host = "host.luau"
```

`host.luau`：

```lua
--!strict
-- New shells get TERN_PROJECT (the name of the git repository they start
-- in); commands that run longer than SLOW_MS toast when they finish; a
-- `gti` typo is corrected on the prompt, waiting for Enter.

local SLOW_MS = 30000

local function repo_root(dir: string): string?
	local at: string? = dir
	while at and at ~= "" do
		if tern.fs.exists(at .. "/.git") then
			return at
		end
		at = string.match(at, "^(.*)/[^/]*$")
	end
	return nil
end

tern.on("spawn", function(spec: SpawnSpec): SpawnSpec?
	local root = if spec.cwd then repo_root(spec.cwd) else nil
	if not root then
		return nil
	end
	spec.env.TERN_PROJECT = string.match(root, "[^/]+$") or root
	return spec
end)

local function title_of(pane: number): string?
	for _, info in tern.pane.list() do
		if info.pane == pane then
			return info.title
		end
	end
	return nil
end

tern.on("command_finished", function(ev: CommandFinishedEvent, cx: EffectCx)
	if ev.took_ms < SLOW_MS then
		return
	end
	local seconds = ev.took_ms // 1000
	local where = title_of(ev.pane) or ("pane " .. ev.pane)
	if ev.status == 0 then
		cx:toast("success", ev.line, string.format("Finished in %ds · %s", seconds, where))
	else
		cx:toast("error", ev.line, string.format("Exit %d after %ds · %s", ev.status, seconds, where))
	end
	local recent = tern.kv.get("slow") or {}
	table.insert(recent, 1, { line = ev.line, status = ev.status, took_ms = ev.took_ms })
	while #recent > 20 do
		table.remove(recent)
	end
	tern.kv.set("slow", recent)
end)

tern.on("command_finished", function(ev: CommandFinishedEvent, _cx: EffectCx)
	local rest = string.match(ev.line, "^gti (.*)$")
	if ev.status == 127 and rest then
		tern.pane.write(ev.pane, "git " .. rest) -- no "\r": Enter runs it
	end
end)
```

在 `~/work/stencil/crates` 中打开标签页，得到的 shell 里 `echo $TERN_PROJECT` 会输出 `stencil`。运行 `gti status` 会以 “command not found”（状态 127）失败，而 `git status` 会出现在下一个提示符上，等待 Enter。

关于这些选择的说明：

- **过滤器保持轻量。** `repo_root` 每层目录只做一次 `exists` 调用，远在 50 ms 之内。它在仓库之外返回 `nil`，从而不改变规格。
- **它修改收到的规格。** 向 `spec.env` 赋值会保留 Tern 设置的变量；返回全新的 `{ env = { TERN_PROJECT = … } }` 会把它们丢掉。
- **一个事件两个处理器。** 它们在同一个 worker 上按顺序运行；其中一个失败不会阻止另一个。
- **toast 出现在命令运行的位置。** `cx` 指向显示该面板的窗口，而面板标题会告诉用户是哪一个。
- **`tern.kv` 保留历史。** 该列表在重启后仍存于插件的数据目录，窗口命令可以在那里显示它。两个半区共享一个 `kv.json`，因此 window 半区读到的是 host 半区最后设置的内容；参见[文件、进程与存储](io.md)。
- **只是键入，而非运行。** 拼写修正省略了 `"\r"`，因此除非用户按下 Enter，什么都不会运行。

## 相关页面 {#related-pages}

- [Host API](../reference/api-host.md#ternon) 与[事件](../reference/events.md)：每个事件及其字段。
- [布局与工作区](layout.md)：窗口事件与窗口 `cx`。
- [架构](../concepts/architecture.md)：host 半区在哪里运行。
- [信任与安全](../concepts/security.md)：向面板写入意味着什么。
