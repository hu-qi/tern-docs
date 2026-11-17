# 扩展 Carly {#extending-carly}

桌面窗口插件以函数而非 JSON-schema 工具来扩展 Carly 这个有状态的 Lua 工具。默认情况下，
每个已加载的本地窗口插件注册的导出与请求上下文对 Carly 都可用。仅 host 端插件与远程插件
不能提供这些集成。

## 内置窗口工具 {#built-in-window-tools}

无需插件，Carly 就能检视并操作活动的 Tern 窗口：

- `inspect` 列出会话、host、标签页、面板、agent 与进程；`object="block"`
  返回 screen、board、Markdown、浏览器及其他 block 的类型化状态。
  `read_block` 返回它们的内容。
- `inspect object="settings"` 把每一项持久化设置列为点分键，并附带其值、类型、
  可选项、范围与说明。`configure` 对其中的键应用一个 patch；接受嵌套对象与点分路径。
- `session` 切换、新建、重命名与关闭会话。`arrange` 对标签页重新分组、重命名与
  换色。`actions` 发现并运行内置动作、插件动作与键位映射动作。`processes`
  列出本地进程 ID 或向其发送信号。
- `run_command`、`send_input` 与 `lua` 打开或操作 block；Lua 上下文还暴露完整的
  窗口插件 API，包括文件、文档、board、agent、screen、浏览器、数据库、host 与进程，
  但不含插件自己的 `tern.secrets`。
- `canvas_read`、`canvas_shot`、`canvas_edit` 与 `canvas_history` 操作 canvas
  block：按 id 列出图形及其页面框、文本与样式；把某个区域看作一张图片；添加、移动、
  调整大小、旋转、重设样式、改变类型、分组、对齐、调整次序或删除图形（每次调用为
  一个撤销步骤）；以及列出、撤销或重做该 block 的步骤。

## 同步与异步结果 {#synchronous-and-asynchronous-results}

`await(value)` 原样返回同步值，或等待一个可等待对象。例如，`cx.agents:start(...)`
立即返回新面板，`cx.agents:list()` 返回行；`await(cx.agents:wait(pane))` 等待回复。
只有可等待对象会挂起 Lua 调用。`await_all` 接受一个可等待对象列表。

## 导出函数 {#export-a-function}

把注册代码放在插件的 `window.luau` 中：

```lua
local tern = require("tern")

tern.carly.export("current", {
	sig = "() -> {pane: number?}",
	doc = "The pane currently focused in this window.",
}, function(cx, call)
	return { pane = cx.session:focused() }
end)

tern.carly.export("pwd", {
	sig = "() -> string",
	doc = "Run pwd and return its output.",
}, function(cx, call)
	tern.process.run({ "pwd" }, { timeout_ms = 5000 }, function(result, fresh_cx)
		if result.status ~= 0 then
			call:fail(result.stderr)
		else
			call:reply(result.stdout)
		end
	end)
	return call:wait(6000)
end)
```

Carly 通过 `help()` 或 `help("plugins.my-plugin")` 发现函数，并这样调用：

```lua
local focused = await(plugins["my-plugin"].current())
local directory = await(plugins["my-plugin"].pwd())
return { focused = focused, directory = directory }
```

`cx, call` 之前的参数是位置参数。即使不使用，也要声明这两个尾部参数：省略的固定参数
会用 nil 补齐，这样可选值不会让上下文与调用句柄错位。传给该固定签名的参数过多会失败；
可变参数的导出可以解包其参数与尾部句柄。
所有结果都是可等待对象，包括立即返回的结果。多个返回值会变成数组。值通过 JSON 跨
VM 传递：支持 table、字符串、布尔值、有限数字与 null；函数、userdata、线程与循环引用
会失败，并指出出问题的路径。参数与回答的编码 JSON 上限为 1 MiB：更长的字符串回答
会被截断以适配，并以 `[… N bytes cut]` 结尾，其他超过上限的值则失败。缺少返回值与
缺少回答都是错误；要表示 null 结果，请显式返回 `nil`。

把导出所需的凭据放在 [`tern.secrets`](../reference/api-window.md#ternsecrets)，
而不是 `tern.kv`：Carly 自己的 VM 无法读取它们，只能调用使用它们的导出。

导出名匹配 `[a-z][a-z0-9_]{0,23}`，每个插件最多 16 个。`sig` 与 `doc` 都是必需的、
非空的，且不超过 1024 字节。以相同名称注册会替换原有注册。重新加载会替换实现，但不重置
Carly 的全局变量；任何仍在等待旧插件的调用会在该 VM 被丢弃之前失败。

## 稍后作答 {#answer-later}

函数在 UI 线程上运行，受插件 50 ms 预算的限制。通过 process、fetch 或 timer API 启动
缓慢的工作。返回 `call:wait(ms)`，并在回调中通过 `call:reply(value)` 或
`call:fail(message)` 作答一次。默认等待为 30000 ms，上限为 120000。在已作答、取消、
超时或重新加载之后，reply/fail 返回 false；此时 `call.cancelled` 读到 true。

调用句柄的生命周期长于该函数。它的 `cx` 不是：回调必须使用它们收到的新上下文。
不要在闭包中保存作用域上下文。

## 添加请求数据 {#add-request-data}

```lua
tern.carly.context(function(cx)
	local pane = cx.session:focused()
	return pane and ("Focused pane " .. tostring(pane)) or nil
end)
```

每个插件一个 provider，重新注册时替换。`fn(cx)` 返回字符串或 nil。插件 VM 执行其
4 ms 预算；错误与被中断的超时会不报错地省略，不会阻塞提问。成功的结果不会因第二次
墙钟检查而被丢弃。已注册的 provider 与导出名会出现在标注为 **Plugins** 的标题下。
每个插件最多贡献 400 个字符，总共 1600 个。

## 从插件提问 {#ask-from-a-plugin}

```lua
tern.command({
	id = "explain",
	title = "Ask Carly about this pane",
	run = function(cx)
		cx:ask_carly("Explain the failure in this pane.")
	end,
})
```

`cx:ask_carly(text)` 会打开 Carly 并提交一个显示的、非空的问题，可在任何 window
插件上下文中使用，包括回调、导出与 Carly 自己的上下文。

`cx:action(name)` 让插件或 Carly 运行任意动作名，包括另一个已加载插件的
`plugin.<id>.<command>`、内置命令、键位映射动作与聚焦视图动作。

## 安排提醒与监视 {#schedule-reminders-and-watches}

每个已加载的桌面窗口插件都可以从作用域的窗口回调中调用 `tern.carly.schedule(spec)`。
插件创建的任务会记录 `by = "plugin:<id>"`。Carly 的 Lua 工具拥有同样的 API。任务在
重新加载与重启后依然存在，并且只在其创建它的窗口中运行。用 `tern.carly.tasks()` 列出
所有窗口的任务，用 `tern.carly.cancel(id)` 删除一个；id 不存在时返回 false。心跳是
内置任务 0，由它的间隔设置管理，而不是被替换或删除。

```lua
-- A reminder: no check, so the due time starts a Carly turn.
local reminder = tern.carly.schedule({
	title = "Stand-up",
	when = "in 20m",
	prompt = "Remind the user that stand-up starts now.",
})

-- A cheap watch: no model call until a matching command finishes.
tern.carly.schedule({
	title = "Build finished",
	on = "command_finished",
	pane = 14,
	check = [[return function(ev, cx, state)
		if ev.ev == "command_finished" and ev.pane == 14 then
			return {line = ev.line, status = ev.status}
		end
	end]],
	prompt = "The build in pane 14 finished. Read it and summarize the result.",
})
```

`TaskSpec` 包含 `title`、`when`/`on` 中恰好一个、可选的 `check` 源码、`prompt`、
锚定 `pane`、`once`、事件监视的 `expires`，以及用于替换的 `id`。时间形式有 `in 20m`、
`at 15:00`、`at 2026-10-04 09:00`、`every 30m`、`daily 09:00`、`weekdays 09:00` 和
`mon,thu 18:30`。当循环间隔会启动模型回合时，必须至少为五分钟；对于不带 prompt 的
检查，则为至少一分钟。事件任务需要 check 或 pane，默认在 12 小时后过期（最多七天）。
一次性时间与事件监视默认为 `once = true`。最多可安排 50 个任务。

check 是返回 `function(ev, cx, state)` 的源码字符串，而不是闭包。每个 check 在自己的
VM 中同步运行，受 50 ms 预算限制；不要 await。`state` 以 JSON 持久化。`nil` 表示
静默，`false` 结束任务，带 `prompt` 的字符串或 table 会启动一个回合。不带 prompt 的
字符串会变成一次告警，不调用模型。没有 check 时，每次触发都会启动一个回合。check 还会
在创建时收到 `dry_run`，并在窗口重新打开后收到 `resume`；在跨重启监视工作时，把当前
面板状态与保存的基线比较。上面的示例只响应实时的 command-finished 事件，而不响应
resume。无效的 spec、编译失败与 dry-run 失败都会报错并指明字段。

**Settings › Carly › Scheduled**，或 `carly_tasks` 动作，可管理任务并显示最近十次
运行。`TaskInfo` 包含 spec、id、创建它的 `window`、`by`（`carly`、`user`、
`plugin:<id>` 或 `heartbeat`）、`paused`、下一个 RFC 3339 时间，以及 `runs`，
其中含 `at`、`outcome`（`quiet`、`said`、`failed`、`missed`、`skipped`）和可选的
`text`。

## API 能力 {#api-capabilities}

安装插件就意味着信任它的本地代码。导出会收到一个新的普通 window 插件 `cx`；其共享
API 与后续回调拥有常规的插件能力与预算。Carly 自己的 Lua 工具也可以通过这些 API 读取
环境变量、读写文件、运行程序、抓取 URL、向任意指定面板输入，并操作窗口。不存在单独的
Carly 审批或按回合的访问层级。

常规的参数校验、查找错误、操作失败、超时与资源限制仍然适用。重新加载不会重置
Carly 会话本地的 VM。

参见 [Window API](../reference/api-window.md#carly-exports-and-request-context)
与[动作名](../reference/actions.md)。
