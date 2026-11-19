# 窗口 API {#window-api}

window 上下文会在本机的每个 Tern 窗口中运行 `window.luau`，每个窗口按插件各自拥有一个 VM，
运行在该窗口的 UI 线程上。它掌管命令面板命令、快捷键、内置命令的覆盖、文件打开与链接点击的路由、
chrome 格式化器、全局 CSS、窗口事件和布局脚本。由于它共享 UI 线程，其预算很短：
每次调用 50 ms（包括加载时运行入口），chrome 格式化器与 `available` 检查为 4 ms。参见
[运行时、预算与 JIT](../concepts/runtime.md)。

Web 客户端不运行任何 Lua，因此那里不存在 window 半区。iOS 以解释方式运行它们。

## Carly 的 Lua 工具 {#carly-s-lua-tool}

在桌面端，Carly 使用一个独立的、会话本地的 Luau VM，其 `cx` 与 window 插件相同。
`lua` 调用会保留全局变量，直到 `/new` 或每日轮转；插件重载不会重置它们。窗口注册类 API 与
`tern.secrets` 不可用；`loadstring` 以及常规的环境/文件系统/进程/网络/窗口 API 都可用。
用 `help("cx.session")` 或 `help("tern.process")` 查看共享声明。

```lua
local pane = cx.session:focused()
cx:run(pane, "pwd\r")
return await(cx.session:settle(pane, 30000))
```

`cx.session:settle(pane, ms?) -> Awaitable<string>` 等待 shell 完成（OSC 133）或其截止时间，
并返回最后几行输出。默认 30000 ms，上限 120000；面板关闭会让它失败。插件以
`:next(function(text, err, cx) … end)` 消费同一个 awaitable，从而获得一个新的上下文。
Carly 使用 `await` 或 `await_all({a, b})`。她的 `cx` 及其会话、布局、canvas 与浏览器对象
在被抢占和 await 期间保持有效；保存的引用会针对当前活跃调用解析。在活跃调用之外使用它们会报错。
插件上下文仍会在其处理函数返回时失效。

打印内容与返回值构成 Carly 的工具回答；`_` 和 `_out` 保留完整的第一个返回值与打印文本。
已保存工作区的 `snippets/*.luau` 模块需用 `require("name")` 显式加载，绝不自动加载。
无头模式下的 `carly lua "<code>"` 把原始回答存入 `state.carly.last_tool`；
其卡片以围栏代码块展示，以保留打印内容与 traceback 的换行。面向模型的工具回答仍为纯文本。
Carly 具备常规的 window 插件 API 能力：读取环境、读写文件系统、进程、网络请求、向任意指定面板输入，
以及操作窗口。相对文件路径使用她所在 VM 的工作目录，而非写入边界。参数校验、操作错误、截止时间
与资源预算仍然生效。

## Carly 导出与请求上下文 {#carly-exports-and-request-context}

`tern.carly` 安装在桌面端 window 插件 VM 中（host、Web 和 iOS 中没有）。
能力与示例参见[扩展 Carly](../guides/carly.md)。

| 注册项 | 约定 |
| --- | --- |
| `tern.carly.export(name, {sig, doc}, fn)` | 注册或替换一个带文档的导出；名称 `[a-z][a-z0-9_]{0,23}`，最多 16 个，sig/doc 各 1–1024 字节 |
| `tern.carly.context(fn)` | 替换请求提供者；`fn(cx) -> string?`，4 ms，每个插件 400 字符，总计 1600 |

默认情况下，每个已加载的本地 window 插件的已注册导出和上下文都可供 Carly 使用。
`help()` 列出导出项，`help("plugins.<id>")` 显示它们的签名与文档。

Carly 调用 `await(plugins[id][name](...))`。参数以 JSON 值传递；
函数接收这些位置参数，随后是一个新建的常规 window 插件 `cx` 和一个 `ExportCall`。
它拥有常规的 50 ms 插件预算。同步返回会立即解析 awaitable；多个返回值会变成数组。
既不返回也不回复即为立即出错。

`ExportCall` 在定时器/进程/fetch 回调中依然有效：

- `call:reply(value) -> boolean`：用 JSON 安全的值回复一次。
- `call:fail(message) -> boolean`：失败一次。
- `return call:wait(ms?)`：等待回调，默认 30000 ms，上限 120000。
- `call.cancelled`：在完成、取消、过期或重载后为 true。

迟到的回复返回 false。参数与回答的上限为编码后 JSON 的 1 MiB：超过上限的字符串回答
（一次回复或单个返回值）会在 UTF-8 边界处截断以适配，并以 `[… N bytes cut]` 结尾，
N 为被省略的字节数；其他任何超过上限的值都会失败。`call:fail` 消息上限为
16 KiB。函数、userdata、线程、循环引用与非有限数字会失败，并给出出错路径。
重载会以 `plugin <id> reloaded
before answering` 使待处理的调用失败。Carly 侧缓存的导出函数会在调用时查找新的实现。

上下文会追加一个 **Plugins** 段落，并公布每个已加载本地 window 插件注册的导出。
出错或超出预算的提供者绝不会阻塞提问。导出处理函数及其后续回调具有常规的插件 API 能力。

## 注册 {#registration}

每个注册类成员（`tern.command`, `tern.bind`, `tern.override`,
`tern.route.*`, `tern.chrome.*`, `tern.files.button`, `tern.css`, `tern.on`,
`tern.carly.export`、`tern.carly.context`）都可以在入口加载时或之后、从任意处理函数中调用。
调用期间做出的注册会在调用返回时生效：命令面板行、键位映射的插件层、Files 面板的按钮
与格式化器会被重新读取，新的样式表会被装入。重载会随 VM 一并丢弃它们，并重新运行入口。

插件按 id 排序。下文的“插件顺序”即指该顺序，同一插件内则指注册顺序。

## 面板与标签页 id {#pane-and-tab-ids}

面板与标签页 id 是 Lua 数字。本机的 id 即 `tern ls` 所显示的。远程主机上的面板带有 host 标记，
Tern 将其与 id 一起打包到 2^53 以下以便 Lua 处理，因此 id 在 double 中保持精确。
请把 id 原样传回，即从 `cx.session`、payload 和 `cx.layout` 结果中收到的形式；
不要用它们做计算，也不要跨窗口比较。

## `tern.command` 命令 {#terncommand}

```lua
tern.command: (def: CommandDef) -> ()

type CommandDef = {
	id: string,
	title: string,
	icon: string?,
	group: string?,
	keys: { string }?,
	available: ((cx: WindowCx) -> boolean)?,
	run: (cx: WindowCx) -> (),
}
```

添加一个命令面板行，以及动作 `plugin.<plugin>.<id>`，快捷键（`tern.bind`、`settings.json` 的
`keybinds`）和状态段都可以引用该动作。

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `id` | 是 | ASCII 字母、数字、`_` 和 `-`；不能是 `bind` |
| `title` | 是 | 命令面板标签 |
| `icon` | 否 | Tern 图标名；未知或缺失时显示 `puzzle` |
| `group` | 否 | 命令面板分组（默认：插件的 `name`） |
| `keys` | 否 | 默认组合键，每个都按 `tern.bind` 的方式绑定到该动作（`"cmd+shift+h"`，序列 `"ctrl+a>c"`） |
| `available` | 否 | 每次命令面板列出各行时调用；结果为假值时隐藏该行。预算 4 ms，钩子 `available plugin.<plugin>.<id>`；出错则隐藏该行 |
| `run` | 是 | 运行该命令，钩子 `command <id>`，50 ms |

会抛出 ``tern.command: bad id `<id>` (letters, digits, `_` and `-`; not
`bind`)``, and a conversion error when `title` is not a string or `run` is
not a function.

再次注册同一 `id` 会替换该行；其 `keys` 会追加到已注册的绑定中。

```lua
tern.command({
	id = "scratch",
	title = "Open scratch file",
	icon = "file",
	keys = { "cmd+alt+j" },
	run = function(cx)
		cx:open(tern.plugin.data .. "/scratch.md", "beside")
	end,
})
```

## `tern.bind` 快捷键 {#ternbind}

```lua
tern.bind: (chord: string, action: string | ((cx: WindowCx) -> ())) -> ()
```

| 参数 | 类型 | 含义 |
| --- | --- | --- |
| `chord` | `string` | 按键，写法与 `settings.json` 的 `keybinds` 相同：以 `+` 连接的修饰键（`ctrl`、`alt`/`opt`、`shift`、`cmd`/`super`）加一个键，序列以 `>` 连接 |
| `action` | `string` 或函数 | 动作名（[内置动作](actions.md)），或一个函数 |

函数会获得动作名 `plugin.<plugin>.bind.<n>`，其中 `n` 按注册顺序从 0 起计
本插件的函数绑定；它作为钩子 `bind <n>` 以一个新建的 `cx` 运行。

会抛出 `tern.bind: the action is a name or a function`。调用时不做其他检查：
键位映射在重建时读取该绑定，并在组合键或动作名无法解析，或 Tern 的默认项或键盘预设
已绑定了该组合键、以它开头的序列、或以它开头的序列之一时，将其略过并记录
`plugin bind left out`。用户针对相同按键的 `keybinds` 条目会替换插件的绑定。

键位映射层级，由低到高：Tern 的默认项与键盘预设、插件的绑定、用户的 `keybinds`。参见
[命令、按键与覆盖](../guides/commands.md#keymap-layering)。

```lua
tern.bind("ctrl+alt+shift+h", "plugin.hello.say_hi")
tern.bind("ctrl+alt+shift+t", function(cx)
	local pane = cx.session:focused()
	if pane then
		cx:run(pane, "cargo test\r")
	end
end)
```

## `tern.override` 覆盖 {#ternoverride}

```lua
tern.override: (command_id: string, fn: (cx: WindowCx) -> boolean?) -> ()
```

在每次运行内置命令 `command_id` 之前运行 `fn`，无论是从命令面板、按键、菜单还是 Tern 的
其他部分触发。覆盖按插件顺序运行；第一个返回真值的会终止其余覆盖并跳过内置命令。
抛出异常的处理函数视为 `false`。钩子名为 `override <command_id>`。

| 参数 | 类型 | 含义 |
| --- | --- | --- |
| `command_id` | `string` | 内置命令 id（[内置动作](actions.md#commands)） |
| `fn` | 函数 | 返回 `true` 以替换内置命令 |

会抛出 ``tern.override: unknown command `<id>` ``。只有命令面板命令可以被覆盖；
其他动作名（`palette`、`goto_tab:N`、`edit.*` 等）不是命令。

当任一插件处理函数运行时，该窗口的插件都不可及：从处理函数中触达的内置命令
（`cx:command`、`cx:open`、`cx.layout:new_tab`）会按 Tern 自身的行为运行，不走覆盖、不走路由。
因此覆盖可以调用它自己的命令而不会递归：

```lua
tern.override("new_tab", function(cx)
	cx:toast("info", "New tab")
	cx:command("new_tab")
	return true
end)
```

## `tern.route.open` 打开路由 {#ternrouteopen}

```lua
tern.route.open: (fn: (req: OpenRequest, cx: WindowCx) -> RouteDecision?) -> ()

type OpenRequest = {
	path: string,
	line: number?,
	col: number?,
	host: string,
	how: How,
	origin: Origin,
}

type How = "default" | "beside" | "below" | "split" | "tab" | "replace" | "over" | "preview"
type Origin = "palette" | "files" | "drop" | "link" | "system" | "cli" | "carly"
```

为有人请求的文件打开注册处理函数。处理函数按插件顺序运行，直到某个返回决定；
若都未返回，Tern 自行打开该文件。钩子名为 `route.open`。

| 字段 | 含义 |
| --- | --- |
| `path` | 绝对路径；存在时为规范化路径（已解析符号链接与 `..`） |
| `line`、`col` | 要定位到的位置，从 1 起计，仅当请求指定时存在 |
| `host` | 文件所在主机的名称 |
| `how` | 打开方式：`default`、`beside`、`below`、`split`、`tab`、`replace`（就地替换聚焦的 block）、`over`（占用聚焦面板的位置直到其关闭）、`preview` |
| `origin` | 发起者：`palette`、`files`（Files 面板）、`drop`、`link`（面板或 file block 中的文件链接）、`system`（访达的“打开方式”、程序坞）、`cli`（`tern open`）、`carly`（Carly 的 window 上下文） |

守护进程面板中的 `tern open` 会转发到某个接受打开请求的窗口，该路由在那里运行。
Tern 自行发起的打开（恢复状态、git 与 board 视图、Files 预览）不走路由。

```lua
tern.route.open(function(req, _cx)
	if req.path:sub(-5) == ".json" and req.how ~= "replace" then
		return { block = "jsonx.viewer", args = { req.path } }
	end
	return nil
end)
```

## `tern.route.link` 链接路由 {#tern-route-link}

```lua
tern.route.link: (fn: (link: LinkRequest, cx: WindowCx) -> RouteDecision?) -> ()

type LinkRequest = {
	url: string,
	pane: number?,
	mods: { cmd: boolean, alt: boolean, shift: boolean, ctrl: boolean },
}
```

为面板中的链接点击、链接菜单的“打开链接”项、host 插件与 surface 请求的打开，
以及系统交给 Tern 的 URL 注册处理函数。它在任何内置处理之前运行，因此可以认领
自定义 scheme 与不存在的路径。钩子名为 `route.link`。

| 字段 | 含义 |
| --- | --- |
| `url` | 被点击时的链接（`https://…`、`file://…`、一个路径、自定义 scheme） |
| `pane` | 链接所在的面板；没有时为 `nil`（声明中写的是 `number`） |
| `mods` | 按住的修饰键：`cmd`（⌘，PC 上为 Super）、`alt`、`shift`、`ctrl` |

```lua
tern.route.link(function(link, cx)
	local ticket = link.url:match("^jira://(%u+%-%d+)$")
	if ticket then
		cx:open("https://example.atlassian.net/browse/" .. ticket)
		return { handled = true }
	end
	return nil
end)
```

## 路由决定 {#route-decisions}

```lua
type RouteDecision = {
	block: string?,
	args: { string }?,
	url: string?,
	path: string?,
	how: How?,
	handled: boolean?,
}
```

处理函数返回 `nil` 表示放行，或返回一个表。按下面的顺序，第一个出现的字段决定结果，
其余字段被忽略。

| 决定 | 对 `route.open` 而言 | 对 `route.link` 而言 |
| --- | --- | --- |
| `nil` | 交给下一个处理函数，最后由内置打开处理 | 交给下一个处理函数，最后由内置处理 |
| `{ block = "<plugin>.<id>", args = {…} }` | 在文件所在主机（`req.host`）、文件所在目录中以 `args` 打开该插件 block，位置按请求的 `how` 决定 | 在被点击面板所在主机、面板所在目录中打开该 block，按住 ⌥ 时在面板旁边打开 |
| `{ url = "…" }` | 将该 URL 视为被点击的链接：链接路由会看到它一次，随后走内置处理 | 对该 URL 走内置的链接处理（路由不再运行） |
| `{ path = "…", how = … }` | 替换路径（以及 `how` 已设置时的位置），随后走内置打开 | 在面板所在主机上以 file block 打开该路径，位置按 `how`（默认：按住 ⌥ 时在旁边，否则为默认） |
| `{ handled = true }` | 不再运行其他任何内容 | 不再运行其他任何内容 |

若某路由的 `block` 指定了该主机上任何 Ready 插件都未定义的类型，则不会打开任何内容，
并弹出错误提示："Could not open the block"，其下为 `No
plugin on <host> defines block type <kind>` beneath (also logged as `no
plugin block type for a route decision`)。该决定仍然生效：内置打开不会运行。

错误的结果会作为该路由钩子的失败上报，并按 `nil` 计算：

- `a route returns a decision table or nil`；
- ``a route decision has an unknown how `<how>` ``；
- `a route decision sets block, url, path or handled = true`。

## chrome 格式化器 {#chrome-formatters}

作用于小型输入表的纯函数：没有 `cx`，预算 4 ms，钩子名为
`tab_title`、`window_title` 和 `status`。每个插件每种各有一个格式化器
（后一次调用会替换前一个）。结果按不同输入缓存
（每种最多 256 个输入，之后缓存重新开始），且每当插件的注册发生变化或插件调用
[`tern.chrome.refresh`](#ternchromerefresh) 时缓存都会被清空，因此除此之外，
格式化器只在其输入变化时才会再次运行。失败会在窗口的下一次轮询时弹出提示；
运行超过 4 ms 的格式化器会被暂停（5 s，若持续超时则更长）。

### `tern.chrome.tab_title` 标签页标题 {#ternchrometab_title}

```lua
tern.chrome.tab_title: (fn: (tab: TabInfo) -> string?) -> ()

type TabInfo = {
	id: number,
	name: string?,
	cwd: string?,
	program: string,
	title: string,
	panes: number,
	busy: boolean,
}
```

标签页标题取自第一个格式化器返回非空字符串的插件；`nil` or `""` 保留 Tern 的标题。

| 字段 | 含义 |
| --- | --- |
| `id` | 标签页 id |
| `name` | 用户为该标签页指定的名称（若有） |
| `cwd` | 聚焦面板的工作目录（未知时为 `""`） |
| `program` | 聚焦面板的程序 |
| `title` | 聚焦面板的标题 |
| `panes` | 该标签页中的面板数量 |
| `busy` | 其中是否有命令正在运行 |

返回字符串或 `nil` 之外的任何内容都会失败，错误为 `a title
formatter returns a string or nil`。

### `tern.chrome.window_title` 窗口标题 {#tern-chrome-window-title}

```lua
tern.chrome.window_title: (fn: (win: WindowInfo) -> string?) -> ()

type WindowInfo = { [string]: any }
```

窗口标题取自第一个格式化器返回非空字符串的插件。运行时传入以下字段：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `space` | `string` | 当前会话的名称 |
| `tab` | `string?` | 活动标签页的标题 |
| `pane` | `number?` | 聚焦的面板 |
| `cwd` | `string?` | 聚焦面板的工作目录 |
| `tabs` | `number` | 当前会话中的标签页数量 |

### `tern.chrome.status` 状态行 {#ternchromestatus}

```lua
tern.chrome.status: (fn: (pane: StatusPaneInfo) -> { StatusSegment }?) -> ()

type StatusPaneInfo = {
	pane: number,
	cwd: string?,
	program: string,
	title: string,
	busy: boolean,
}

type StatusSegment = {
	text: string,
	icon: string?,
	tone: string?,
	command: string?,
}
```

聚焦面板的状态行分段。每个插件的分段都会显示，按插件顺序；`nil` 不添加任何分段。
声明中 `cwd` 为可选；窗口始终会设置它，目录未知时设为 `""`。

`busy` 在 shell 集成报告有命令正在运行时为 true，在命令结束或面板程序退出后为 false。
它是格式化器缓存键的一部分；对没有 shell 集成的程序，它不会推断活动状态。

| 分段字段 | 含义 |
| --- | --- |
| `text` | 其文本（必填） |
| `icon` | Tern 图标名，显示在文本之前 |
| `tone` | 设置 `data-tone`（`"accent"`、`"muted"`、`"error"` 等） |
| `command` | 任意动作名（[内置动作](actions.md)），点击时运行 |

分段在状态行内渲染为 `<span class="sl-plugin" data-plugin="<id>">`，
设置后带 `data-tone`，可点击时带类 `on` 与 `role="button"`。
无法解析的 `command` 会在点击时弹出提示"A status segment's
command is unknown"。结果不是列表或 `nil` 时失败，错误为
`a status formatter returns a list of segments or nil`。

```lua
tern.chrome.status(function(pane)
	if pane.program == "kubectl" then
		return { { text = "k8s", icon = "box", tone = "accent", command = "plugin.k8s.contexts" } }
	end
	return nil
end)
```

### `tern.chrome.program_icon` 程序图标 {#ternchromeprogram_icon}

```lua
tern.chrome.program_icon: (program: string, icon: string?) -> ()
```

为 `program` 选择标签页、命令面板的面板行、停靠卡片以及其他显示面板程序图标之处
所佩戴的图标，替代 Tern 自带的图标。它是一项注册，而非格式化器：在做出该注册的调用
返回时被读取，如同命令或绑定。

| 参数 | 含义 |
| --- | --- |
| `program` | 程序键，写法同图标的 `data-program` 属性（`codex`、`claude`、`vim` 表示 Vim 与 Neovim、`node`、`shell`、`other`；[chrome 与样式](../guides/chrome.md#program-icons) 列出了它们），或命令的名称（`nvim`、`npm`、`aider`：即 `TabInfo.program` 给出的值）。匹配时忽略大小写。 |
| `icon` | Tern 图标名（[图标名](../elements/data.md#icon-names)）：`provider-openai`、`provider:openai`（模型提供者的标志）、`sparkle`、`tile-omp` 之类的应用图块。`nil` 收回本插件对 `program` 的选择。 |

面板的图标按以下先后顺序确定：其会话自带的图标（omp 的会话所设置的那个），
然后是第一个插件（按 id 顺序）对面板命令名的选择，再是对其程序键的选择，
然后是 `program_icons` 设置对命令名的选择，再是对键的选择，最后是 Tern 的。
应用图块（`tile-*`）原样替换标签页的卡片；其他任何图标都绘制在空白卡片上。
纯文本标签页以标签页的文本颜色平铺绘制它。

对没有任何图标使用的名称会抛出 ``tern.chrome.program_icon: unknown icon `<name>` ``，
对空程序会抛出 `tern.chrome.program_icon: empty program`。

```lua
-- Codex tabs wear OpenAI's mark instead of Codex's tile.
tern.chrome.program_icon("codex", "provider-openai")
```

### `tern.chrome.refresh` 刷新 {#ternchromerefresh}

```lua
tern.chrome.refresh: () -> ()
```

丢弃本窗口所有格式化器的缓存结果并唤醒窗口，窗口会在下一帧重绘其标签页、状态行与标题：
每个格式化器都会以当前输入再运行一次。当格式化器在其输入之外读取的数据
（由定时器、进程、事件提供的外部变量）发生变化后调用它。其他窗口保留各自的缓存；
每个窗口运行自己的 window 半区。

从格式化器中调用时抛出 `tern.chrome.refresh: not from a formatter`。
计时的分段仅在有待计数的内容时才由定时器刷新：

```lua
local started: { [number]: number } = {}
local tick: TimerHandle? = nil

local function schedule()
	if tick == nil and next(started) ~= nil then
		tick = tern.timer(1000, function()
			tick = nil
			tern.chrome.refresh()
			schedule()
		end)
	end
end

tern.on("command_started", function(ev, _cx)
	started[ev.pane] = tern.now()
	schedule()
end)
tern.on("command_finished", function(ev, _cx)
	started[ev.pane] = nil
	tern.chrome.refresh()
end)

tern.chrome.status(function(pane)
	local since = started[pane.pane]
	if since == nil then
		return nil
	end
	return { { text = string.format("%ds", (tern.now() - since) // 1000), icon = "clock" } }
end)
```

## `tern.files.button` 文件面板按钮 {#ternfilesbutton}

```lua
tern.files.button: (def: FilesButtonDef) -> ()

type FilesButtonDef = {
	id: string,
	title: string,
	icon: string?,
	run: (files: FilesInfo, cx: WindowCx) -> (),
}

type FilesInfo = {
	root: string?,
	host: string,
	selection: { string },
	tab: "files" | "changes" | "refs",
}
```

在 Files 面板的头部、More 之前添加一个按钮
（[chrome 与样式](../guides/chrome.md#files-pane-buttons)）。
每个插件的按钮都会显示，按插件顺序。与头部自带的工具一样，
它们在指针位于面板上方时淡入，在面板拥有键盘焦点时显示一个。与那些工具不同，
它们在 Changes 与 Refs 标签页以及窄面板中依然显示。

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `id` | 是 | ASCII 字母、数字、`_` 和 `-` |
| `title` | 是 | 工具提示与无障碍名称 |
| `icon` | 否 | Tern 图标名；未知或缺失时显示 `puzzle` |
| `run` | 是 | 点击时以该面板和一个新建的 `cx` 运行，钩子 `files button <id>`，50 ms |

| `files` 字段 | 含义 |
| --- | --- |
| `root` | 面板显示的文件夹，在其主机上为绝对路径；不显示任何文件夹时为 `nil` |
| `host` | 该文件夹的主机名；没有文件夹时为 `""` |
| `selection` | 选中行的绝对路径，选中的文件夹代表其被选中的后代项；没有选中项时为光标所在行的路径；可能为空 |
| `tab` | 面板显示的标签页 |

会抛出 ``tern.files.button: bad id `<id>` (letters, digits, `_` and `-`)``，
以及 `title` 不是字符串或 `run` 不是函数时的转换错误。再次注册同一 `id`
会就地替换该按钮。处理函数错误会像其他任何钩子那样弹出提示。

按钮渲染为 `<button class="icon-btn ft-hb ft-rv ft-plugin"
data-plugin="<plugin>" data-id="<id>">` inside `.ft-plugins`（位于头部的
`.ft-tools` 中），因此 `tern.css` 可以为某一个设置样式。

```lua
tern.files.button({
	id = "butler",
	title = "Open in Butler",
	icon = "sparkle",
	run = function(files, cx)
		local target = files.selection[1] or files.root
		if target then
			cx:open(target, "beside")
		end
	end,
})
```

## `tern.css` 全局样式表 {#terncss}

```lua
tern.css: (name: string, source: string) -> ()
```

把 `source` 安装为全局样式表 `plugin:local:<plugin>:<name>`，位于 Tern 自带的样式表之后，
或替换该名称的样式表。清单中的 `styles` 是样式表 `plugin:local:<plugin>:styles`。

| 参数 | 类型 | 含义 |
| --- | --- | --- |
| `name` | `string` | ASCII 字母、数字、`_` 和 `-`；不能是 `styles` |
| `source` | `string` | CSS |

会抛出 ``tern.css: bad name `<name>` (letters, digits, `_` and `-`; not
`styles`)``. CSS parse errors don't raise; they are logged as `plugin style
sheet has errors`。重载会移除每个插件样式表并重新安装它们。
（`tern.d.luau` 将该样式表
命名为 `plugin:<plugin>:<name>`；运行时使用此处展示的 `local` 段。）Web 标签页不运行
window 入口，因此 `tern.css` 样式表永远不会到达那里；它会从目录安装其守护进程的 Ready
插件的清单 `styles`。

插件 block 的区域元素（`.sf-main`、`.sf-dock`、`.sf-layer`）带有
`data-surface="plugin.<plugin>.<id>"`；lens block 带有
`.sf-block[data-role="lens.plugin.<plugin>.<id>"]`。参见
[chrome 与样式](../guides/chrome.md)。

```lua
tern.css("status", [[
#statusline .sl-plugin[data-plugin="k8s"] { color: var(--accent); }
]])
```

## `tern.on` 事件订阅 {#ternon}

```lua
tern.on: (name: string, fn: (...any) -> ...any) -> ()
```

把 `fn` 订阅到窗口事件 `name`。处理函数接收 payload 和一个新建的 `cx`，
`window_start` 例外，它只接收 `cx`。

| 事件 | 处理函数 |
| --- | --- |
| `window_start` | `(cx)` |
| `focus` | `({pane, tab}, cx)` |
| `pane_created`、`pane_closed` | `({pane}, cx)` |
| `tab_created`、`tab_closed` | `({tab}, cx)` |
| `command_started` | `({pane, line}, cx)` |
| `command_finished` | `({pane, line, status, took_ms}, cx)` |
| `cwd` | `({pane, path}, cx)` |
| `title` | `({pane, title}, cx)` |
| `agent_state` | `({pane, old, new}, cx)`：agent 的状态发生变化，取值同 `cx.agents:list()` 所给（`working`、`waiting_input`、`idle`、`exited`）；对上次查看之后新出现的 agent，`old` 为 `nil` |
| `agent_finished` | `({pane, result}, cx)`：agent 的一轮结束（`result` 为其自报的 `done` 或 `failed`），或 agent 本身结束（`exited`，或随其 block 一起 `closed`） |
| `float_moved` | `({pane, tab, over, corner?, stashed?, docked?}, cx)`：用户松开了拖动或甩出的浮窗；它吸附到 `over` 的 `corner`，从 `stashed` 边缘滑出，或停靠到 `over` 的 `docked` 一侧 |
| `session_ended` | `({session, name, shown}, cx)`：某个会话消失（在此处、别处关闭，或被 `tern kill session` 关闭，或以 0 退出的 `--end-on-success` block 结束）；若消失的是正在显示的那个（`shown`），窗口此时已显示它此前显示的那个会话 |
| `budget` | `({hook, state, ms?, paused_ms?}, cx)`：本插件自己的某个钩子因运行超出预算而暂停（`state = "paused"`，其预算 `ms`，暂停时长 `paused_ms`）或恢复（`state = "resumed"`） |
| `canvas_action` | `(ev: CanvasAction, cx) -> boolean?`，仅针对本插件拥有的 canvas |

会抛出 ``tern.on: unknown window event `<name>` ``。钩子名即事件名。
[事件](events.md#window-events)说明了各事件何时触发以及按什么顺序触发。

## `tern.secrets` 密钥存储 {#ternsecrets}

```lua
tern.secrets.get: (name: string) -> Awaitable<string?>
tern.secrets.set: (name: string, value: string?) -> Awaitable<nil>
```

把插件的凭证（API 密钥、OAuth 令牌）保存在系统的安全存储中，而非明文文件中：
macOS 上为登录钥匙串，Windows 上为凭据管理器，Linux 上为 Secret Service，
系统存储失败时回退到 Tern 状态目录下仅所有者可读的文件。开发版构建只保存在这些文件中，
无头会话（`tern shot`、`serve`、测试）保存在内存中，每次启动都是全新的。

| 函数 | 行为 |
| --- | --- |
| `get(name)` | 解析为存于 `name` 下的密钥（任意字节），或 `nil` |
| `set(name, value)` | 把 `value`（任意字节，至多 64 KiB）存于 `name` 下并替换原有值，解析为 `nil`；`value` 为 `nil` 时删除它 |

每个密钥都存于账户 `plugin.<plugin id>.<name>` 下，因此插件只读写自己的密钥。
名称需匹配 `[a-z0-9][a-z0-9._-]{0,63}`。

系统请求解锁钥匙串时存储可能会阻塞，因此两个调用都在 UI 线程之外运行并返回 awaitable：
插件使用 `:next(function(value, err, cx) … end)`。名称不合法、值超过 64 KiB
（在触及存储之前检查）以及存储失败都会使 awaitable 失败，错误为
`tern.secrets.get: <reason>` 或 `tern.secrets.set: <reason>`；
除了参数不是字符串之外，调用时不会抛出任何异常。若某密钥的钥匙串一直处于锁定状态
（用户关闭了解锁提示），`get` 会失败而不是解析为 `nil`：它就在那里，只是无法取到。

仅限 window 插件半区：host 半区和 Carly 自己的 Lua VM 没有
`tern.secrets`。Carly 只能通过插件的导出访问插件的凭证。

```lua
tern.secrets.get("api.token"):next(function(token, err, cx)
	if err then
		cx:toast("error", "Keychain", err)
	elseif not token then
		cx:toast("info", "Sign in first")
	else
		tern.fetch("https://api.example.com/me", {
			headers = { Authorization = "Bearer " .. token },
		}, function(result, cx) … end)
	end
end)
```

## window cx {#window-cx}

Carly 使用与已加载 window 插件相同的 window 方法和能力：
向任意指定面板输入、toast 与剪贴板操作、布局变更、创建、聚焦、显示、关闭，
以及每一个命令或动作。聚焦与显示使用常规的插件默认值；关闭面板使用原始的会话操作，
而非 Carly 专用的确认保护。参数校验、未知目标与底层操作失败仍然生效。

插件的打开请求不走路由。Carly 的文件打开使用来源 `carly`；她的 URL
打开会查询链接路由。

```lua
declare extern type WindowCx with
	session: SessionCx
	layout: LayoutCx
	canvas: CanvasCx
	docs: DocsCx
	board: BoardCx
	browser: BrowserCx
	db: DbCx
	settings: SettingsCx
	git: GitCx
	notebook: NotebookCx
	actions: ActionsCx
	agents: AgentsCx
	procs: ProcsCx
	screen: ScreenCx
	function run(self, pane: number, text: string): ()
	function open(self, target: string, how: How?, reveal: Reveal?): ()
	function new_block(self, kind: string, args: { string }?, how: How?, opts: BlockOpts?): number?
	function command(self, id: string): ()
	function action(self, name: string): ()
	function ask_carly(self, text: string): ()
	function pick(self, opts: PickOptions): Awaitable<PickItem?>
	function prompt(self, opts: PromptOptions?): Awaitable<string?>
	function toast(self, level: ToastLevel, text: string, sub: string?): ()
	function copy(self, text: string): ()
	function window_key(self): string
end

type ToastLevel = "success" | "info" | "error"
type BlockOpts = { focus: boolean?, target: number?, dir: Dir?, ratio: number? }
```

执行操作的 window 处理函数会拿到 `cx`：命令、绑定、覆盖、路由、
`available` 检查、窗口事件，以及窗口的定时器、进程与 fetch 回调。
`cx` 仅在接收它的那次调用期间有效；之后使用已保存的 `cx` 会报错。定时器、进程与 fetch
回调会拿到一个新的 `cx`。当某个 `cx` 的另一次调用仍在运行时，通过它发起调用会抛出
`cx is already in use`。

| 成员 | 行为 | 抛出 |
| --- | --- | --- |
| `cx.session` | [会话 cx](#session-cx) | |
| `cx.sessions` | 会话的列出/当前/创建/切换/重命名/关闭/锁定/解锁 | 未知会话或空名称 |
| `cx.hosts` | 主机的列出/当前/添加/切换/信任/断开/终端 | 未知或已断开的主机；指纹不匹配 |
| `cx.board` | [board cx](#board-cx)（桌面） | 未知或过期的卡片或泳道；无效的元数据；磁盘错误 |
| `cx.browser` | [browser cx](#browser-cx) | |
| `cx.db` | [数据库 cx](#database-cx)（桌面） | |
| `cx.settings` | [设置 cx](#settings-cx) | 未知的键/类型/枚举值或无效的快捷键 |
| `cx.git` | [git cx](#git-cx) | 桌面 |
| `cx.notebook` | [笔记本 cx](#notebook-cx) | |
| `cx.actions` | [动作 cx](#actions-cx) | |
| `cx.agents` | [agent cx](#agent-cx) | |
| `cx.procs` | [进程 cx](#processes-cx)，仅本地桌面 | |
| `cx.layout` | [布局 cx](#layout-cx) | |
| `cx.canvas` | [canvas cx](#canvas-cx) | |
| `cx.whiteboard` | [whiteboard cx](#whiteboard-cx)（桌面） | |
| `cx.docs` | [文档 cx](#documents-cx)（桌面） | |
| `cx:run(pane, text)` | 把 `text` 按输入的形式写入面板的程序；以 `"\r"` 结尾可运行 shell 命令 | `no program runs in that pane` |
| `cx:open(target, how?)` | Tern 自身的打开（路由不运行）。给定 `how` 时，路径（绝对、`file://`，或相对于聚焦面板的目录）以 file block 打开，位置由 `how` 决定。不给 `how` 或目标不是路径时，`target` 按在聚焦面板中点击的链接打开：文件在 file block 中，文件夹在 Files 面板中，网页链接在 browser block 或浏览器中，其他一切通过系统处理 | ``unknown how `<how>` `` |
| `cx:new_block(kind, args?, how?, opts?)` | 在窗口的当前主机上以 `args` 打开 `kind`（`"<plugin>.<id>"`）的插件 block，位置由 `how` 决定（默认 `default`），并聚焦它（`opts.focus = false` 保持当前显示的焦点）。`opts.target`、`opts.dir` 与 `opts.ratio` 按 `cx.canvas:open` 的方式[决定位置与尺寸](#opening-at-a-saved-size)。返回其面板，当地没有 Ready 插件定义 `kind` 时返回 `nil`（不弹提示：由调用方决定） | ``unknown how `<how>` ``; a bad `target`, `dir` or `ratio` |
| `cx:command(id)` | 运行内置命令 `id`；覆盖不运行 | ``unknown command `<id>` `` |
| `cx:action(name)` | 运行任意键位动作，包括 `plugin.<id>.<command>`，对 Carly 也具有常规的 window 插件能力 | 未知动作或插件处理函数 |
| `cx:ask_carly(text)` | 从任意 window 插件上下文（包括回调、导出以及 Carly 自身）打开 Carly 并提问显示出来 | 空问题 |
| `cx:pick(opts)` | [请用户](#asking-the-user)在聚焦面板上方的选择器中从 `opts.items` 选一项；解析为所选项目，被关闭时为 `nil` | `cx:pick: items is missing`、`cx:pick: items is empty`、`cx:pick: item <n> is not a table`、`cx:pick: item <n> has no label` |
| `cx:prompt(opts?)` | [请用户](#asking-the-user)在聚焦面板上方的输入框中输入一行；解析为文本，被关闭时为 `nil` | |
| `cx:toast(level, text, sub?)` | 在本窗口显示一个 toast；`sub` 是第二行 | ``unknown toast level `<level>` (success, info or error)`` |
| `cx:copy(text)` | 把 `text` 放入剪贴板 | |
| `cx:window_key()` | 本窗口的 key：即 `tern … --window KEY` 所接收、`tern inspect` 在每个客户端的 `conn` 旁列出的值（第一个窗口为 `""`，其他为 `"2"`、`"3"` 等）。从 window 上下文用 `tern.process.run` 启动的进程会以 `TERN_WINDOW_KEY` 获得它，因此它们运行的 `tern …` 命令无需 `--window` 即可抵达本窗口 | |

`how` 取值：`default`、`beside`、`split`（同 `beside`）、`below`、
`tab`、`replace`（就地替换聚焦的 block；没有任何内容聚焦时为 `default`）、`over`（见下文）、
`preview`. `replace` 与 `preview` 用于放置文件：
除 `below`、`tab` 和 `over` 之外的每个取值下，`cx:new_block` 都把它的插件 block 开在聚焦 block
旁边，且只有 `over` 会占用另一个 block 的位置。

`over` 在聚焦面板的槽位中打开任意类型的新 block（当 `cx:new_block` 的 `opts` 或
`cx.canvas:open` 的 spec 给定了 `target` 时，则为 `target` 的槽位），如同在该面板中运行的程序接管它一样。
该面板离开视野，停靠在其会话的牌堆中，其程序仍在运行。
当新 block 关闭时（`cx:exit`、⌘W、其程序退出），该面板会以自身的 id
回到同一槽位并获得焦点。没有任何内容聚焦时，`over` 等同 `default`；在浮窗上则开在该浮窗所覆面板的旁边。
期间从牌堆发出的面板留在被发出的位置，block 只是关闭；此后被停靠或浮起的面板亦然。
只有打开该 block 的窗口会把面板放回：该窗口重启之后，或 block 在会话的另一个窗口中关闭时，
面板留在牌堆中。

布局与会话变更会复制到该会话的其他窗口；焦点仍属于本窗口自己。

### 向用户提问 {#asking-the-user}

`cx:pick` 与 `cx:prompt` 用 Tern 自带的选择器向窗口前的人提问，绘制在聚焦面板之上，
但不使窗口其余部分变暗（没有面板显示时，居中显示在变暗的窗口上）。它们会立即返回一个
[awaitable](api-shared.md#awaitables-and-ternsleep)；回答在
`:next(function(answer, err, cx) … end)` 中以一个新的 `cx` 到达，或在 Carly 的 Lua
中通过 `await` 得到。

```lua
type PickItem = {
	label: string, detail: string?, group: string?, icon: string?, current: boolean?,
	[string]: any,
}
type PickOptions = { items: { PickItem }, placeholder: string?, icon: string?, action: string? }
type PromptOptions = { value: string?, placeholder: string?, icon: string?, action: string? }
```

| 选项 | 含义 |
| --- | --- |
| `items` | 仅 `cx:pick`，必填：各行，按此顺序。输入时按 `label` 过滤；最多显示前 200 个匹配项 |
| `value` | 仅 `cx:prompt`：输入框的初始文本，处于选中状态，输入即替换 |
| `placeholder` | 空输入框的提示，同时也是选择器的无障碍名称 |
| `icon` | 输入框的 Tern 图标；未知或缺失时显示 `puzzle` |
| `action` | ↵ 的作用，显示在按键说明中：未指定时，`pick` 为 `select`，`prompt` 为 `confirm` |

| 项目字段 | 含义 |
| --- | --- |
| `label` | 该行显示的内容 |
| `detail` | 标签之后的暗色文本 |
| `group` | 连续多个同组项目上方的标题 |
| `icon` | 该行的 Tern 图标（默认：输入框的图标） |
| `current` | 显示对勾，标记当前选择 |

↑/↓ 移动，↵ 作答，Esc 或点击选择器之外会将其关闭。
`cx:pick` 解析为所选项目：即传入的那个表本身，因此它携带的其他字段（路径、id）会一并返回。
`cx:prompt` 解析为按输入得到的文本，可能为空。当用户关闭选择器，或另一个选择器、
命令面板或其他插件的问题取代了它时，两者都解析为 `nil`：同一时刻只显示一个问题。
该 awaitable 永不失败。

```lua
local function quote(s: string): string
	return "'" .. s:gsub("'", "'\\''") .. "'"
end

tern.command({
	id = "branch",
	title = "New branch…",
	icon = "branch",
	run = function(cx)
		local pane = cx.session:focused()
		cx:prompt({ placeholder = "Branch name", icon = "branch", action = "create branch" })
			:next(function(name, _err, cx)
				if name and name ~= "" and pane and cx then
					cx:run(pane, "git switch -c " .. quote(name) .. "\r")
				end
			end)
	end,
})

tern.command({
	id = "deploy",
	title = "Deploy to…",
	run = function(cx)
		cx:pick({
			placeholder = "Deploy to…",
			action = "deploy",
			items = {
				{ label = "staging", detail = "eu-west-1", group = "Pre-production", url = "https://staging.example.com" },
				{ label = "production", detail = "eu-west-1", group = "Live", url = "https://example.com" },
			},
		}):next(function(target, _err, cx)
			if target and cx then
				cx:toast("info", "Deploying to " .. target.label, target.url)
			end
		end)
	end,
})
```

### 文档 cx {#documents-cx}

桌面端的 `cx.docs` 工作在文档层面，而非编辑器控件层面。`open(path,
{how?, line?})` returns a pane; `new_note(title, markdown)` 通过 Tern 的种子笔记路径创建
一个会话所有的笔记，内容为 `# title` 后跟 Markdown 正文。

其他所有方法都返回 awaitable，在 Carly 中用 `await` 消费，在插件中用 `:next`
消费：

| 方法 | 结果 |
| --- | --- |
| `read(path, {from?, lines?})` | 精确文本，包括缓冲区中尚未保存的修改；默认整篇文档 |
| `outline(path)` | 解析后的 Markdown 标题 `{title, level, line}`（不含代码围栏内的标题） |
| `search(path, query)` | 区分大小写的字面匹配 `{line, column, text}` |
| `write(path, text)` | 整体替换；父目录存在时会创建缺失的文件 |
| `edit(path, {find, replace, all?})` | 替换第一个匹配，或全部不重叠的匹配 |
| `edit(path, {line, insert})` | 在一基行号之前插入精确文本；EOF 接受下一行 |
| `edit(path, {heading, append})` | 追加到指定章节的末尾，在其子章节之后 |
| `append(path, text)` | 在 EOF 处追加精确文本 |
| `save(path)` | 缓冲区保存确认后为 true；已关闭的既有文件无需保存 |

编辑返回 `{from, to}`，即含首尾的一基变更行范围。标题名称为渲染后的/纯标题；
标题缺失或重复会失败且不做任何编辑。查找字符串缺失同样会失败。行号与 Unicode 字符列
从 1 起计。相对路径针对聚焦面板的目录解析。

已打开的文档使用其共享缓冲区、撤销、脏状态与自动保存。已关闭的文件使用同目录下的原子写入，
保留编码与权限。针对期间已变化的缓冲区准备的编辑会安全地失败；请针对新文本重试。
操作在 30 秒后超时。

```lua
local pane = cx.docs:open("/tmp/plan.md", {how = "beside"})
await(cx.docs:edit("/tmp/plan.md", {heading = "Next", append = "- Ship\n"}))
return await(cx.docs:outline("/tmp/plan.md"))
```

### canvas cx {#canvas-cx}

canvas 是原生 block 类型 `tern.canvas`：持久、可复制的内容由 window Lua 提供，
没有 host 入口。包 id `tern` 为保留值。其 surface role 为 `plugin.tern.canvas`。
它显示 UI 节点，没有图形：whiteboard（canvas block，类型 `canvas`）属于
[`cx.whiteboard`](#whiteboard-cx)，对 canvas 调用 `set` 会抛出相应错误。

```lua
declare extern type CanvasCx with
	function open(self, spec: CanvasSpec): (number?, string?)
	function set(self, pane: number, change: CanvasChange): ()
	function get(self, pane: number): CanvasInfo?
	function list(self): { CanvasInfo }
end

type CanvasSpec = {
	title: string, about: string?, view: Node?, md: string?, dock: Node?,
	how: How?, focus: boolean?, target: number?, dir: Dir?, ratio: number?,
}
type CanvasChange = {
	title: string?, about: string?, view: Node?, md: string?, dock: Node?,
	set: { [string]: Node | false }?,
}
type CanvasInfo = {
	pane: number, owner: string, title: string, about: string,
	view: Node?, dock: Node?,
}
type CanvasAction = {
	pane: number, owner: string, act: string, node: string,
	value: string?, mods: { string }?,
	text: string?, title: string?, about: string?,
}
```

`open` 接受用 `tern.ui` 构建的 `view` 树，或 Markdown `md`，两者不可同时给出。
默认为 `"beside"`，对插件与 Carly 都会聚焦新面板；
`target`、`dir` 与 `ratio` 用于[以保存的尺寸打开它](#opening-at-a-saved-size)。
不支持 canvas 的 host 返回 `nil, err`。视图的根会被绘制；`dock` 固定在底部。
视图根键 `__canvas` 保留给隐藏元数据，使用它会同步抛出。其他键会被保留，包括根键 `"0"`。
`get` 读取本窗口的副本，对非 canvas 或状态尚未到达的对象返回 `nil`。`list` 省略视图/dock 树。

`set` 替换所提供的字段。其 `set` 映射修补视图根之下的路径：带键的子项使用其键，
无键的子项使用从 0 起的索引（`"jobs.build"` 或 `"0"`）。`false` 移除节点。
新键追加到既有父项之下；未知父项会抛出。插件更新只能指定自己的 id；Carly 可以更新任意
canvas。创建者的插件 id 或 `"carly"` 会一直保存。任何调用方都可以读取 canvas。

限制为每次编码后的变更 256 KiB、2000 个节点、深度 32、标题 80 字符、`about` 2000 字符。
无效的树与路径会在发送前抛出，表中未声明的字段（包括 `owner`）以及不含字段的
`set` 同样如此。输入/编辑器节点会被拒绝（canvas 不接受按键），图像也会被拒绝
（没有 blob 传输）。状态在守护进程重启后保留；重载插件不会重置其 canvas。

只有 `action` 事件会送达点击所在窗口的拥有者。在插件中注册
`tern.on("canvas_action", function(ev, cx) ... end)`。第一个真值返回会消费该点击；
没有处理函数或全部返回假值时，会弹出提示 `Nothing handles “<act>” here`。切换与选择是本地行为。
`cx.session:event(pane, {ev = "action", id = node, act = name})` 在调用处理函数返回后，
无需指针即可投递同一动作，例如从测试命令中触发。

Carly 在她的会话 VM 中注册 `tern.carly.on_canvas(fn)`，payload 相同，
使用一个新建的常规能力上下文，预算 50 ms。在处理函数内部请使用异步的 `:next` 续延，
而非仅限根部的 `await`。处理函数在会话重置时消失。未处理的点击会变成一次显示的 agent 轮次，
以 JSON 数据形式引用该动作、节点文本、标题和持久化的 `about`，说明该按钮的用途。
她的回复使用常规的 chip/卡片行为，卡片关闭时附一个 toast。
iOS 没有 Carly 回退；Web 没有 window Lua。

```lua
tern.on("canvas_action", function(ev, cx)
	if ev.act ~= "refresh" then return false end
	cx.canvas:set(ev.pane, { md = "Refreshed" })
	return true
end)
```

[SDK](../index.md#the-sdk) 中完整的、仅用 window 的 Canvas Dashboard 包，
含一个在重载后查找既有自有 canvas 的命令面板命令，以及一个带键的状态更新处理函数。
安装方式：

```sh
tern plugin install github.com/stencil-hq/tern-sdk/plugins/examples/canvas
```

用于无头检查时，`carly last` 显示最后一次工具结果或排队的 canvas Action 提示；
`carly last "<contains>"` 还会断言回答包含给定文本。同一文本也存于
`state.carly.last_tool.text`。

#### 以保存的尺寸打开 {#opening-at-a-saved-size}

`target`、`dir` 与 `ratio`（位于 `CanvasSpec`，或 `cx:new_block` 的
`opts` 中）在同一次调用中放置新 block 并设定其尺寸，因此它的第一帧就已是最终宽度：
不会先出现默认一半宽的一帧再调整。

- `target` 是要分割的面板（默认：聚焦面板），`dir` 是 block 在该面板上所占的一侧：
  `right`（默认）、`down`、`left` 或 `up`。任一者都会使放置成为对该面板的分割，
  因此它们需与 `how` 的 `default`、`beside` 或 `split` 搭配；与 `tab` 或 `below` 一起会抛出，
  `target` 不在任何标签页中时亦然。
- `ratio` 是新 block 在其所在分割中的占比，介于 0 与 1 之间（不含端点），
  并像拖动分隔条那样保持在最小面板尺寸之上。没有 `target` 或 `dir` 时，它设定 `how`
  所形成的分割；当 block 在独占的标签页中打开时被忽略。

要以用户留下的宽度重新打开侧边栏，可在关闭前从 `cx.session:layout(tab)` 读取其占比：
`TabTree` 分割的 `ratio` 是其第一个子项的占比，因此左侧边栏的占比即其分割的 `ratio`，
右侧的则为 `1 - ratio`。旁边的面板仍以常规的分割动效让位，`reduce_motion` 会关闭该动效。

```lua
local pane, err = cx.canvas:open({
	title = "Outline", md = outline, focus = false,
	target = terminal, dir = "left", ratio = saved_share or 0.25,
})
```

### whiteboard cx {#whiteboard-cx}

whiteboard 是 canvas block（类型 `canvas`）：无尽页面上的图形、箭头、文本与墨迹，
用户也可以在上面绘制。`cx.whiteboard` 像 Carly 的 `canvas_read` 与 `canvas_edit`
工具那样读写它们，单位为页面单位（100% 缩放时 1 视图 px），图形以其 16 位十六进制 id 标识。
仅桌面端。

```lua
declare extern type WhiteboardCx with
	function open(self, opts: { how: How?, focus: boolean? }?): Awaitable<number>
	function read(self, pane: (number | string)?, query: WhiteboardQuery?): WhiteboardState
	function edit(self, pane: (number | string)?, edits: { WhiteboardEdit }): WhiteboardResult
end
```

`open` 放置一个空 whiteboard（`how` 默认为 `"beside"`），在它可读可编辑后解析为其面板；
若该 block 始终未显示，则在 10 秒后失败。`pane` 为 nil 时指聚焦的 whiteboard，
否则指唯一打开的那个；指定 `cx.canvas` 面板或其他 block 类型会抛出。

`read` 按从后到前的顺序列出图形，每个分组在其内部内容之前，含 `id`、`type`、
其边框的页面框（`x`、`y`、`w`、`h`）、文本与样式（省略默认值），另加 `view`：
用户当前看到的页面区域及其 `zoom`。可用 `ids`（含其内部内容）、`area`
（`{x, y, w, h}`）与 `max_shapes`（默认 200，最多 2000）过滤。

`edit` 按顺序应用其编辑，作为用户可撤销的单个撤销步骤。每个编辑有一个 `op`，
且只接受该 op 的字段：任何其他字段都会抛出，并指明该编辑，且不会写入任何内容。`add`
以 canvas 当前样式生成一个 `type`（`rect`、`ellipse`、`diamond`、`triangle`、`hexagon`、
`parallelogram`、`star`、`cylinder`、`pill`、`bracket`、`brace`、`text`、`arrow`、`line`、
`polygon`、`curve`、`ink`、`highlight`、`image`），`ref` 为其命名，供同一次调用中后续编辑引用。
`bracket`（`[`）或 `brace`（`{`）向右张开，不接受文本与箭头；`rotate` 与 `flip` 可转动它。
其他 op 有 `move`、`resize`、`rotate`、`text`、`style`、`delete`、`lock`、`unlock`、`group`、
`ungroup`、`duplicate`、`order`、`align`、`distribute`、`layout`、`flip`、
`look`、`paper` 与 `show`；Carly 的 VM 中 `help('WhiteboardEdit')` 列出了它们的字段。

`layout` 无需算术即可摆放图形：`ids`（各自单独）或 `groups`（id 列表，各自作为整体移动），
间隔 `gap`（默认 40），从左上角 `x`、`y` 起（默认：它们的起始位置）。`axis` 使其排成一行或一列，
在 `edge` 处对齐（默认居中）；`cols` 逐行填满网格，每个图形在其单元格中居中。
带 `gap` 的 `distribute` 保留沿轴的第一个图形，并让其余图形恰好相隔 `gap`。
回答包含 ref、被触及的图形、被移除的图形以及 `notes`，后者会标出两端图形相接的箭头
（它们会画得过短或完全不画）。

```lua
local pane = await(cx.whiteboard:open())
local edits = {}
local function box(name)
	table.insert(edits, {op = 'add', type = 'rect', x = 0, y = 0, w = 160, h = 60, text = name, ref = name})
end
local services = {'Auth', 'Orders', 'Search'}
box('CDN')
for _, name in services do box(name) end
-- The services in a row, then the CDN centered 100 above it.
table.insert(edits, {op = 'layout', ids = services, axis = 'horizontal', gap = 60})
table.insert(edits, {op = 'layout', groups = {{'CDN'}, services}, axis = 'vertical', gap = 100})
for _, name in services do
	table.insert(edits, {op = 'add', type = 'arrow', from_shape = 'CDN', to_shape = name})
end
cx.whiteboard:edit(pane, edits)
return cx.whiteboard:read(pane).view
```

### 会话 cx {#session-cx}

```lua
declare extern type SessionCx with
	function sessions(self): { SessionInfo }
	function layout(self, tab: number): TabLayout?
	function find_tab(self, spec: string, session: number?): number?
	function find_session(self, spec: string): number?
	function tab_of(self, pane: number): number?
	function pane(self, pane: number | string): PaneInfo?
	function read(self, pane: number | string, opts: ReadOpts?): (BlockRead | string)?
	function selection(self, pane: (number | string)?, opts: { max_chars: number? }?): BlockSelection?
	function surface(self, pane: number | string, opts: SurfaceOpts?): (SurfaceTree | string)?
	function view(self, pane: number | string, opts: SurfaceOpts?): (ViewNode | string)?
	function event(self, pane: number | string, ev: { [string]: any }): ()
	function panes(self): { PaneInfo }
	function tabs(self): { TabInfo }
	function focused(self): number?
	function resolve(self, spec: string): number?
	function block_types(self): { BlockTypeInfo }
end
```

| 方法 | 返回 |
| --- | --- |
| `panes()` | 窗口的每个面板，无论在标签页中还是已停靠，均以 [`PaneInfo`](#ternchromestatus) 表示（此处的 `cwd` 始终是字符串） |
| `tabs()` | 窗口的每个标签页，涵盖所有会话，以 [`TabInfo`](#ternchrometab_title) 表示 |
| `focused()` | 聚焦面板的 id，或 `nil` |
| `resolve(spec)` | `spec` 指定的面板，或 `nil`：`"@focused"`、面板 id、精确标题、忽略大小写的标题，然后是程序名，已停靠的面板也包括在内；多个匹配时，优先活动标签页中的，其次任意标签页中的，最后是已停靠的 |
| `block_types()` | 本窗口在其当前主机上可以打开的 block 类型，形式为 `{kind, title, icon, palette}`：先是原生 canvas，然后是当地每个 Ready 插件的每个 block（`kind` 为 `"<plugin>.<block>"`；`palette` 表示命令面板是否提供它） |

```lua
local pane = cx.session:resolve("nvim")
if pane then
	cx.layout:focus(pane)
end
```

#### 会话与分割树 {#sessions-and-split-trees}

`sessions()` 为每个会话返回 `{id, name, current, locked, tabs}`。
`find_session` 先匹配 id，再匹配精确名称，再忽略大小写匹配名称。
`find_tab` 在给定会话（默认当前会话）中匹配一基位置或标题词；`tab_of` 包括浮动的 block。
未匹配时返回 `nil`。`TabInfo` 还包含 `session`、`color`、一基的
`position` 和聚焦的 `pane`；四者都参与 chrome 缓存失效。

`layout(tab)` 返回 `{tab, root, floats, zoomed, focus}` 或 `nil`。
`TabTree` 的叶子是 `{pane}`；分割是
`{split = "right"|"down", ratio, [1] = left_or_top, [2] = right_or_bottom}`。
每个浮窗是 `{pane, over, corner = "tl"|"tr"|"bl"|"br"}`。这些是分割树，
而非 `surface` 返回的 TSP 树。

#### 面板读取与树 {#pane-reads-and-trees}

`pane` 与 `panes` 包含仅 window 的 kind/tab/focused/floating/parked/busy/at_prompt、
当前的 `running = {line, ms}`、`last = {line, status, took_ms}`、exited/error/alert、
浏览器 URL、原生路径与插件 block 类型。host 的 `tern.pane.list` 保持不变。
检查结果仅在 `kind = "terminal" | "agent"` 时提供 `program`、`busy`、`at_prompt`、`running`、`last`
与 `exited`；对其他所有类型（包括原生与插件 block）这些字段都不存在。`tern.chrome.status`
保留其现有的 `StatusPaneInfo` payload，其中包括所有类型的底层 `program` 与 `busy`。

`read` 使用每个 block 实际的模型返回 `{kind, info, ...}`：终端行
（包括 TSP surface）、插件文本、浏览器 URL/标题/加载状态/历史、文件文本
与未保存的修改、git 状态/提交、SQLite schema/行/SQL、笔记本单元格/输出、
board 泳道/卡片、进程、profile 函数或屏幕快照信息。它永不运行浏览器 JavaScript，也不获取焦点。
未加载的状态会如实报告。

`ReadOpts` 接受 `as = "table" | "text"`（默认 table）、`lines`（60，最多 2000）、
`rows`（25，最多 500）、`max_chars`（8000，最多 64000）、终端的 `scrollback`（true），
以及一基的文件 `from`（默认跟随视图）。

| `kind` | `kind` 与 `info` 之外的表字段 |
| --- | --- |
| `terminal`、`agent` | `lines`、`more`、`surface` |
| `plugin` | `title`、`text`（main、dock 与 layer） |
| `browser` | `url`、`title`、`loading`、`progress`、`error`、`back`、`forward`、`driven` |
| `file` | `path`、`host`、`file_kind`、`mode`、`dirty`、`load`、`first`、`total`、`lines`、`caret`、`selection`；媒体/十六进制：`size`、`image`、`hex` |
| `git` | `root`、`ready`、`provisional`、`head`、`upstream`、`operation`、`staged`、`unstaged`、`conflicts`、`selection`、`open`、`commits`、`stashes`、`running` |
| `database` | `path`、`memory`、`phase`、`read_only`、`dirty`、`area`、`schema`、`browse`、`execute`；缓存的查询行保留 SQL NULL 并标记未加载的行 |
| `notebook` | `path`、`phase`、`kernel`、`dirty`、`active`、`cells`，含源码、输出、标签、索引、类型、执行计数与状态 |
| `board` | `path`、`phase`、`view`、`filter`、`hide_done`、`lanes`，含标题、完成/折叠状态，以及卡片中的文本、完成、标签、截止、子任务与光标 |
| `canvas` | `canvas`、`phase`、`shapes`、`selected`、`tool`、`look`、`paper`；失败时为 `error` |
| `procs` | `sampled`、`totals`、`sort`、`descending`、`tree`、`filter`、`rows`、`selected` |
| `profile` | `process`、`pid`、`take`（录制期间 host 的会话守护进程在采样时其 `hosted = true`）、`show`、`samples`、`functions`（含 name/self/total）、`focus`、`thread`、`query` |
| `screen` | `host`、`display`、`phase`、`failure`、`control`、`frame = {w, h}`；像素不是文本 |

行式列表在受限时带有 `more`（或 `<list>_more`）；在支持的情况下，
`first`/`total` 描述所选的窗口范围。`as = "text"` 在省略标记中标明上限。
本构建中不可用的按类型字段会缺失。SQL NULL 单元格与未缓存的整行槽位为 `tern.json.null`；
已加载的行始终是表，即使其所有单元格都是 NULL。空数组仍带数组标记。

`selection(pane?, {max_chars?})` 以 `{pane, kind, text, chars_clipped?}`
返回用户在 block 中选中的文本，那里没有任何选中内容时为 `nil`。该文本即复制所取的文本：
终端的选中单元格，否则是窗口的选择（当其始于该 block 内部时，例如 omp 的对话记录、Carly、
block UI 等 TSP surface），并保留 Markdown 列表标记与段落换行。`kind` 为该 block 的 `read` 类型。
不给 `pane` 时先读聚焦面板，然后是第一个持有选择的其他面板。`max_chars`
默认 8000（最大 64000）；`chars_clipped = true` 标记被截断。文件 block 则以 `read` 范围报告其选择。
它从不聚焦或滚动任何内容。

```lua
local sel = cx.session:selection()
if sel then
	return ("%s %d:\n> %s"):format(sel.kind, sel.pane, (sel.text:gsub("\n", "\n> ")))
end
```

`surface` 返回 `{surface = {id, title?, role?, mode}, main?, dock?, layer?, more?}`。
它选择活跃的 surface，否则选择最新的保留内联 surface。整块被省略的区域计入顶层的 `more` 计数。
节点使用 TSP 线上形式 `{id, k, p?, c?, more?}`；`more` 统计被省略的后代数量。
`SurfaceOpts` 接受 `as`、`root`（节点 id）、`nodes`（500，最多 5000）、`depth`
（默认全部，最多 64）与 `max_chars`。`view` 采用相同的上限，返回
Tern 的无障碍子树 `{role, name?, value?, states?, children?, more?}`，
不含 id 与边界；隐藏或未挂载的 block 返回 `nil`。
`event` 为插件和 Carly 向面板的程序发送 TSP 事件。canvas 没有程序：在那里它只接受
`action` 事件（其他任何事件都会抛出），并在调用处理函数返回后，将每个事件作为对节点 `id`
的点击投递（[canvas cx](#canvas-cx)）。

```lua
return cx.session:read("@focused", {as = "text", rows = 10})
```

### 屏幕 cx {#screen-cx}

`cx.screen:displays()` 返回本地显示器的 awaitable 列表，含 `id`、
`name`、`width`、`height`、`scale` 与 `primary`。用
`cx.screen:share(id, {how = "view"})` 共享一个；`"control"` 转发键盘/指针
输入，nil 或 `"main"` 选择主显示器。返回的面板 id 可用于
`status(pane)`（phase、host、display、control、frame、failure）与
`stop(pane)`（关闭共享）。两者也接受会话 resolve spec。

### 进程 cx {#processes-cx}

`cx.procs` 始终针对本地桌面机器，而非聚焦的远程主机。`list(options?)`、`find(name_or_pid)`
与 `children(pid)` 返回 awaitable，基于与 Carly 的 `processes`/`inspect processes`
相同的后台采样器。Carly 使用 `await(...)`；插件使用 `:next(function(result, err, cx) ... end)`。

`list` 返回 `{local, sample, total, more, processes}`。选项有 `sort`
（`name`、`pid`、`user`、`cpu`、`memory`、`gpu`、`threads`、`disk`）、`descending`、
`name`、`user`、`cwd`、`limit`（默认 100，1–5000）与 `tree`（默认 false）。
文本过滤器以 AND 组合，匹配不区分大小写的子串。名称、PID 与用户默认升序；
用量列降序。树形输出是前序列表，带 `depth` 与 `context`（为提供上下文而保留的不匹配祖先）。
详情包括命令行、可执行文件、父进程、cwd、用户、状态与用量；cwd 及其他未知的系统详情为 nil。
`find` 返回最忙的名称匹配项或精确 PID，不存在时为 nil。`children` 返回直接子进程，最多 5000。
端口与端口过滤被省略：采样器不收集套接字，而将套接字映射到属主需要另做整机范围的系统扫描。

`signal(pid, signal)` 接受 `terminate`、`kill`、`interrupt`、`hangup`、`stop`
与 `continue`；成功时返回 `{pid, signal, signaled=true}`。它直接向一个正的本地 PID 发送信号；
错误会抛出共享的机器可读信封 `{kind, message, pid, signal}`。

`open()` 返回在当前位置面板旁、聚焦的 Processes block 的面板 id（为空时开新标签页）。
`profile(pid, {seconds=20})` 打开一个 profile block，并在采样与符号化完成后返回
`{pane, pid, process, samples, functions, ...}` 的 awaitable。时长 1–3600 秒。
前 25 个函数包含 `name`、`self` 与 `total` 采样计数；系统剖析器失败会使该 awaitable 拒绝。
profile block 被关闭同样会使它拒绝。

```lua
local rows = await(cx.procs:list({name = "rust", sort = "memory", tree = true}))
local p = await(cx.procs:find("rustc"))
if p then
	local report = await(cx.procs:profile(p.pid, {seconds = 2}))
	print(report.pane, report.functions)
end
```

## 动作 cx {#actions-cx}

`cx.actions:list(query?)` 返回内置与插件的命令面板动作，含 `id`、
`label`、`group`、`keys`（生效的书写形式组合键）、`available`，以及可选的
`plugin` id。不可用的命令仍可被发现。查询词匹配 id、标签与分组。`describe(id)`
返回一个精确的 id 或报错。`keys()` 把生效的组合键映射到动作 id 数组，保留焦点解析的优先级。

`cx.actions:run(id_or_exact_label)` 返回与 Carly 的 `actions` 工具相同的成功消息；
未知与有歧义的标签会报错。`cx:action(name)` 是前往同一分派的快捷方式。与其他
Carly 工具一样，关闭是非交互式的。

### 笔记本 cx {#notebook-cx}

`cx.notebook` 使用与笔记本 block 相同的已加载单元格、撤销历史与 Python 内核。
笔记本 id 即面板 id。单元格 id 是来自 `cells` 的稳定数字键，而非行索引；
重载笔记本会替换这些键。

| 方法 | 结果 |
| --- | --- |
| `open(path)` | 在聚焦面板旁打开，并返回其笔记本面板 id |
| `cells(nb)` | 按文档顺序返回所有单元格，包括完整的源码与输出 |
| `run(nb, {cell = id})` 或 `run(nb, {all = true})` | `Awaitable<{NotebookCell}>`，按运行顺序的输出快照 |
| `add(nb, {kind, source, after?})` | 新单元格 id；可撤销；默认追加，`after = 0` 则前插 |
| `edit(nb, cell, source)` | 可撤销的源码替换，保留输出 |
| `kernel_status(nb)` | `NotebookKernel`，当前解释器以及执行/输入/失败详情 |
| `kernel_restart(nb)` | `Awaitable<NotebookKernel>`，未经确认的重启后新内核处于空闲 |

单元格类型有 `"code"`、`"markdown"` 与 `"raw"`。每个 `NotebookCell` 包含
`id`、`nbformat_id`、`kind`、`source`、`count`、`state`（`idle`、`queued`、`running`）
与 `outputs`。输出保留流文本、以 MIME 为键的 `data` 与 `metadata`、
执行结果 `count`、显示 id 以及完整的错误 traceback。Python
异常是普通的错误输出，而非 await 失败。可空的返回值使用 `tern.json.null`。

内核状态包含 `status`（`not_started`、`starting`、`idle`、`busy`、
`dead`）、`label`、`python`、`version`、`implementation`、`env`、`pid`、`waiting`、
`running`、`input = {prompt, password}` 与 `dead`（失败消息）。
执行与解释器启动在 UI 线程之外运行。await 没有执行超时；交互式输入使用笔记本 UI。
已排队或正在运行的目标单元格无法通过此 API 运行或替换。内核丢失、笔记本关闭，
或等待中的单元格被替换/移除，都会使 await 失败；重置 Lua VM 会取消该 await，
但不会停止用户的内核。

```lua
local nb = cx.notebook:open("/tmp/analysis.ipynb")
local id = cx.notebook:add(nb, {kind = "code", source = "print(6 * 7)"})
cx.notebook:run(nb, {cell = id}):next(function(cells, err, cx)
	if err then error(err) end
	cx:toast("success", cells[1].outputs[1].text)
end)
```

Carly 用 `await(cx.notebook:run(nb, {all = true}))` 而非 `:next`。
对正在加载或已失败的笔记本执行操作会抛出真实的加载/文件错误。

### agent cx {#agent-cx}

`cx.agents:list()` 返回所有会话中的 agent：agent block，以及在提示符处运行 omp 的
shell（其 `command` 为 `tern.json.null`），两者的 `kind = "agent"`：
`{pane, command, model, cwd, state, last_message}`。未知的元数据为 `tern.json.null`。
目标接受面板 id 或 resolve spec，例如 `"@focused"` 与 agent 标题。

- `start({prompt, cwd, command?, how?}) -> pane`：像 New agent block 一样打开；
  省略的命令与位置使用设置。`how` 为 `"split"`、`"tab"` 或
  `"replace_if_alone"`。输入就绪后窗口即提交提示，即使启动它的 VM 已重置。
- `ask(agent, text)`：粘贴一条提示并按下回车；需要输入已就绪。
- 桌面端 `wait(agent, {timeout?}) -> Awaitable<string?>`：等待至空闲，返回
  最后一段助手文本。超时以毫秒计（默认 30000）。已消失/已退出的
  agent 与超时会拒绝。已排队/已提交的输入不会被过早视为空闲。
- `transcript(agent, {last?})`：来自 omp TSP 聊天的按时序的 `{role, text, tools}`。
  角色为 `"user"`/`"assistant"`；思考与 chrome 被排除，工具
  调用元数据/输出会保留。默认 last=50，最大 1000；零表示空。
  非 omp 的 agent 没有结构化对话记录。
- `interrupt(agent)`：Ctrl-C，保留该 block。
- `stop(agent)`：关闭该 block 并结束其程序，不做确认。

工作/空闲来自进度 OSC 9;4；暂停的进度或提问浮层表示
`waiting_input`。插件对等待使用 `:next(function(message, err, cx) ... end)`；
Carly 使用 `await(...)`：

```lua
local pane = cx.agents:start({prompt = "Explain the failing tests", cwd = "/work/app"})
local answer = await(cx.agents:wait(pane, {timeout = 120000}))
return {answer = answer, messages = cx.agents:transcript(pane, {last = 4})}
```

### git cx {#git-cx}

`cx.git` 通过与 git block 相同的已配置引擎操作本地仓库。目标是 `repo` 返回的描述符、
一个路径、一个本地面板 id，或 `cx.session:resolve` 风格的 spec，例如 `"@focused"`。
所有方法都返回 Awaitable：Carly 使用 `await(...)`；插件使用 `:next(function(result, err, cx)
... end)`。失败会以 git 的错误拒绝；重置 VM 会丢弃迟到的回答。

| 方法 | 结果 / 含义 |
| --- | --- |
| `repo(target)` | 根目录、分支、HEAD、上游、领先/落后情况以及进行中的操作 |
| `status(repo)` | 已暂存、未暂存与冲突文件列表，含重命名的来源与行数 |
| `log(repo, {limit?, path?})` | 跨引用的 git 图历史；默认 50，最多 100000；路径跟随 HEAD 的文件重命名 |
| `diff(repo, {path?, staged?, rev?})` | 统一文本；默认未暂存、已暂存索引，或单个修订的提交补丁 |
| `stage(repo, paths)` / `unstage(repo, paths)` | 只变更索引；字面的仓库相对路径，空列表不做任何变更 |
| `commit(repo, message, {amend?})` | 以完整消息提交索引，可选地修正 HEAD |
| `branches(repo)` | 本地与远程分支目标、跟踪关系与当前状态 |
| `checkout(repo, name, {detached?})` | 切换分支、创建本地跟踪分支，或在某修订处分离 |
| `create_branch(repo, name, {at?})` | 在 HEAD 或指定修订处创建并检出分支 |
| `stash_push(repo, {message?})` | 暂存已跟踪与未跟踪的变更 |
| `stash_pop(repo, {index?})` | 应用并丢弃一个 stash，最新在前、索引从 0 起（默认 0） |
| `open(repo, {how?})` | git 面板 id；原生位置用语，默认复用标签页中的某个 block |

`diff` 不能同时使用 `staged = true` 与 `rev`。变更操作共享 git block 的
串行工作线程、撤销日志，以及对根目录上每个已打开 block 的刷新。

```lua
local repo = await(cx.git:repo("@focused"))
local changes = await(cx.git:status(repo))
await(cx.git:stage(repo, {"src/main.rs"}))
local patch = await(cx.git:diff(repo, {staged = true}))
local pane = await(cx.git:open(repo, {how = "tab"}))
```

### 设置 cx {#settings-cx}

`settings.json` 可以保存的每一项偏好都可通过 `cx.settings` 获取，包括默认值
（文件中只保留被改动的项）。根字段名是规范名称；`terminal.font_size` 是 `font_size` 的别名。
点分路径指代嵌套字段（`carly.model`、`sqlite.drop.quoted`）；
`get` 也可以读取整个子树。

| 方法 | 结果 |
| --- | --- |
| `get(key)` | 当前值或子树 |
| `set(key, value)` | 经常规钳制与保存后的生效值 |
| `set_many(table)` | 原子地应用点分键或嵌套补丁；返回所有叶子值 |
| `list(prefix?)` | 点分叶子键映射到当前值 |
| `describe(key)` | 由 Settings 推导出的 `{type, enum, range, default, nullable, doc}` |
| `themes()` | 已安装主题的名称 |
| `keybinds()` | 用户的快捷键覆盖，而非生效的键位映射 |
| `bind(chord, action_or_actions)` | 绑定一个动作或按优先级排序的动作数组 |
| `unbind(chord)` | 写入空覆盖，把按键留给程序 |

未知的键、无效的类型/枚举值与重叠的路径会失败且不改变偏好。嵌套对象补丁会合并；
`keybinds` 替换整个覆盖映射。数值在其存储类型内通过既有的设置钳制处理。
`null`/nil 清除可选偏好；`get` 对它们返回 nil。`list` 把未设置的键保留为 `tern.json.null`。
无头会话保持临时性。要从替换用的 `keybinds` 映射中恢复某个组合键的默认绑定，请移除该条目；
`cx.actions:keys()` 显示生效的绑定。

```lua
cx.settings:set_many({["carly.model"] = "@smol", notebook = {start_on_open = true}})
cx.settings:bind("cmd+shift+h", "new_tab")
local font = cx.settings:describe("terminal.font_size")
```

## 会话与主机 cx {#sessions-and-hosts-cx}

`cx.sessions:list()` 返回每个具名会话（`id`、`name`、`host`、
`current`、`locked`、`note`、标签页数量）。`:current()` 返回正在显示的那个。
`:create({name?, cwd?})` 在当前主机上创建并显示一个会话，
其第一个标签页在 `cwd` 中启动。`:switch(spec?)`、`:rename(spec, name)`、
`:close(spec?)`、`:lock(spec?)` 与 `:unlock(spec?)` 接受精确名称或 id；
nil 与 `"@current"` 选择正在显示的会话。空名称会报错。
关闭会在没有交互式确认或锁定保护的情况下结束程序；关闭最后一个会话会使其保持打开且为空。

`cx.hosts:list()` 与 `:current()` 返回机器信息，含身份链、
连接状态与详情、实测的 `rtt_ms`（不可用时为 null），以及会话/面板 id。id 原样传给会话与布局命名空间。
主机 spec 接受槽位、不区分大小写的名称、地址、`"local"` 或 `"@current"`。

桌面端 `:add(address)` 返回 `Awaitable<ManagedHost>`；Carly 使用 `await`，
插件使用 `:next(function(host, err, cx) ... end)`。它在连接后解析，若连接失败或主机断开则失败。
首次接触仍使用 Tern 常规的密钥验证：检查 `detail.fingerprint`，
独立核验它，然后调用 `:trust(host, fingerprint)` 或使用
主机对话框。指纹不匹配会报错，而非接受该密钥。

`:switch(host)` 显示已连接主机的上一个会话。`:terminal(host,
{cwd?, command?})` 在那里打开并聚焦一个 shell 标签页，返回其面板 id。
`:disconnect(host)` 断开并忘记一台远程机器；其程序继续在那里运行。
本地主机无法断开。

```lua
local session = cx.sessions:create({name = "Build", cwd = "/tmp"})
local pane = cx.hosts:terminal("local", {cwd = "/tmp", command = "printf hello"})
cx.sessions:switch(session.id)
```

### board cx {#board-cx}

桌面端的 `cx.board` 在卡片/泳道层面编辑 Markdown 任务板。
`open(path, {how = "beside"})` 返回一个 board 面板；其他所有方法都返回
awaitable（Carly：`await(...)`；插件：`:next(function(result, err, cx) ... end)`）。
board 参数接受本地路径或 board 面板 id；相对路径使用聚焦的本地面板的 cwd。
`how` 还接受 `default`、`below`、`tab`、`pip`
与 `preview`。

| 方法 | 行为 |
| --- | --- |
| `boards()` | 本地面板 cwd 与检出根目录中已打开的 board 及任务/看板 Markdown 文件 |
| `read(board, {rows?, from?, max_chars?})` | 通用 block 读取器的泳道/卡片；默认 25 行，最多 500；`from` 为第一个一基泳道；`more` 报告被省略的数据 |
| `add(board, {lane, text, tags?, due?, subtasks?})` | 添加一张卡片；返回其不透明 id；子任务是字符串或 `{text, done?}` |
| `move(card, lane, {position?})` | 按卡片 id 移动到泳道标题/id；一基位置（不计该卡片），默认追加 |
| `check(card, done)` | 使用该 board 引擎的完成泳道移动来勾选/重新打开 |
| `edit(card, {text?, tags?, due?})` | 只替换所提供的字段；`tags={}`/`due=false` 清除这些字段；保留备注/子任务 |
| `remove(card)` | 移除该卡片及其备注与子任务 |
| `add_lane(board, {title, position?})` | 插入一个泳道，默认追加；返回其不透明 id |
| `rename_lane(board, lane, title)` | 按精确标题或 id 重命名泳道 |
| `remove_lane(board, lane)` | 移除该泳道及其所有卡片 |

标签省略 `#`；日期使用 `YYYY-MM-DD`。卡片/泳道使用来自 `read`
（或插入）的 `id`，而非行位置。它们的 id 在模型编辑与撤销期间保持稳定，
但外部文件重载与重新打开会使其失效；之后请重新读取。泳道标题重复时必须用 id。
移入 Done 会勾选卡片；移出会重新打开它。已打开的 board 共享实时模型、撤销、渲染与
自动保存。关闭文件后的操作在磁盘未变时保留模型身份，并使用同一引擎加窗口线程之外的原子写入。
自动保存失败会拒绝，同时保留已打开 board 的内存内修改与撤销。

```lua
local pane = cx.board:open("/repo/TODO.md")
local card = await(cx.board:add(pane, {lane = "Doing", text = "Write docs",
	tags = {"docs"}, subtasks = {"Draft", "Review"}}))
await(cx.board:check(card, true))
local board = await(cx.board:read(pane, {rows = 500}))
```

### 数据库 cx {#database-cx}

桌面端的 `cx.db` 打开现有的本地 SQLite 数据库而不创建面板。
每个操作都在引擎的有序工作线程上运行并返回 awaitable；
插件使用 `:next(function(result, err, cx) ... end)`，Carly 使用 `await`。

| 方法 | 等待结果 |
| --- | --- |
| `open(path, {read_only = true}?)` | 不透明的数字连接 id，归本 Lua VM 所有 |
| `tables(db)` | 主数据库的用户表与视图名称，已排序 |
| `schema(db, table)` | 存储的 CREATE SQL；未知名称会失败 |
| `query(db, sql, {limit = 1000}?)` | `{columns = {string}, rows = {{DbCell}}}` |
| `exec(db, sql)` | 成功时为 `tern.json.null` |

相对路径针对聚焦面板的 cwd 解析，没有面板时针对主目录。
连接会一直存在，直到其 Lua VM 被丢弃。默认使用 SQLite 实际的只读打开标志。
只有 `open(path, {read_only = false})` 允许 `exec`；除非 SQL 显式开启事务，
否则写入自动提交。即使是可写句柄，`query` 也要求一条产生行的只读语句。
它不重写 SQL。`limit` 限制返回的行数；为零时只返回列。

行保持位置：SQL NULL 为 `tern.json.null`；文本与有限数值
是普通的字符串/数字。Blob 为 `{blob = {byte, ...}}`，超出 Luau 精确数值范围的整数
为 `{integer = decimal_string}`，非有限实数为 `{real = "inf" | "-inf"}`。空数组仍是数组。
SQLite 失败会使 awaitable 失败；插件与 Carly 之间没有权限隔离。

```lua
cx.db:open("/tmp/catalog.sqlite"):next(function(db, err, cx)
	if err then error(err) end
	cx.db:query(db, "SELECT * FROM products", {limit = 20}):next(function(result, err, cx)
		if err then error(err) end
		cx:toast("success", tostring(#result.rows) .. " rows")
	end)
end)
```

### 浏览器 cx {#browser-cx}

`cx.browser:call(op) -> Awaitable<BrowserResult>` 运行 `tern browser` 的 op
词汇表。插件使用 `:next(function(result, err, cx) ... end)`；Carly 使用
`await`。回答为 `{ok = answer}` 或 `{error = {kind, message}}`。
重置会话会丢弃 Carly 未完成的回答。browser block 可以在 macOS、Linux 与 Windows 上
被驱动。

`blocks` 列出窗口的每个 browser block（包括用户的），形式为
`{block, url, title, owner, shown, driven}`：`owner` 是画中画浮于其上的 block（停靠时为 `nil`），
`shown` 表示它是否在屏幕上，`driven` 表示是否由脚本驱动。每个接受 `block` 的 op 都接受其中任意一个。
被驱动的页面在不可见时仍以其页面尺寸保持存活；
`release` 把 block 交还给用户（设置脚本为其页面设置的重置，block 保留）。

`open` 接受 `owner`（浮于其上的 block）、可选的 `url`
（`about:blank`）、`corner = "tl" | "tr" | "bl" | "br"`（`"br"`）、`width` 与
`height`（页面尺寸，单位 CSS px，默认 1280 × 800）、`profile`（网站数据存储名称，
默认 `"agent"`，默认存储为 `tern.json.null`）
以及 `show`（`true`），或用 `how = "beside" | "below" | "over"` 按
`owner` 停靠该 block 而非浮动它：在其右侧或下方分割，或以 `over` 占用其位置
（owner 被停靠，其程序仍在运行），直到页面关闭。停靠的 block 获取焦点并以其自身尺寸排布页面；
`how` 与 `corner` 或 `show = false` 同用会回答 `invalid`。
页面接受调用后，它回答 `{block, url}`。使用 `show = false` 时，
block 以停靠方式打开，位于会话的牌堆中，而非浮动：它永不
出现在屏幕上或获取焦点，其页面以 `width` × `height` 运行，
每个 op 都像对待显示的页面那样作用于它（`state` 报告该尺寸，
`viewport` 改变它，`shown` 保持 `false`）。发出其卡片即可显示它。

`snapshot` 接受 `block`, optional `root`（ref 或 CSS 选择器）、`depth`、`nodes`
（400，最多 3000）、`mode = "outline" | "text"` 与 `format = "tree" | "text"`。
它返回 URL/标题、树或文本、被省略的节点以及 iframe 元数据。交互式
元素获得稳定的隔离世界 ref；密码值被遮蔽，隐藏节点被省略。它永不启动 Tern 的驱动页面/对话框策略，
但对原生页面求值会安装平台的驱动委托。

`act` 接受 `block`、`ref`、`action = "click" | "fill" | "press" | "select" |
"check" | "uncheck" | "hover" | "scroll"`, optional `text`、`keys`（组合键字符串或
数组）、`dx` 与 `dy`。它尽可能使用受信任的输入；过期的 ref 会以
`not_found` 失败。Carly 可以以常规的 window 插件能力使用每一项浏览器操作。

`pick` 接受 `block` 并让其页面进入元素拾取模式：指针下的元素被描边，
点击即拾取它（页面看不到该点击），Esc 取消。它回答 `{picked, url, title}`，
`picked` 为 `{ref, selector, tag, role, name?, text?, value?, box = {x, y, width, height}}`
（`box` 以视口 CSS px 计，密码值被遮蔽），或 `{cancelled = true,
url, title}`. `ref` is a snapshot ref, so `act` takes it. A newer `pick`
会取消等待中的那个；导航会以 `failed` 结束它。与
`snapshot` 一样，它永不使该 block 变为被驱动。
无头快照会以 `failed: a headless session shows no pages` 失败；同步的
`session:read` 仍会提供 URL/标题。

```lua
local page = await(cx.browser:call({op = "snapshot", block = pane}))
if page.error then error(page.error.message) end
return page.ok
```

### 布局 cx {#layout-cx}

```lua
declare extern type LayoutCx with
	function new_tab(self, launch: Launch?, reveal: Reveal?): number?
	function split(self, target: number, dir: Dir, launch: Launch?, reveal: Reveal?): number?
	function focus(self, pane: number): ()
	function close(self, pane: number): ()
	function move(self, pane: number, target: number, dir: Dir | "swap", reveal: Reveal?): boolean
	function resize(self, pane: number, dir: Dir, cells: number): boolean
	function tab(self, spec: TabSpec, reveal: Reveal?): (number?, string?)
	function move_to_tab(self, pane: number, tab: number, reveal: Reveal?): (boolean, string?)
	function move_to_new_tab(self, pane: number, session: number?, reveal: Reveal?): (number?, string?)
	function float(self, pane: number, over: number?, corner: Corner?, opts: FloatOpts?): (boolean, string?)
	function dock(self, pane: number, target: number?, dir: Dir?, reveal: Reveal?): (boolean, string?)
	function park(self, pane: number): (boolean, string?)
	function unpark(self, pane: number, reveal: Reveal?): (boolean, string?)
	function even(self, tab: number): ()
	function name_tab(self, tab: number, name: string?): ()
	function color_tab(self, tab: number, color: TabColor?): ()
	function order_tab(self, tab: number, position: number): ()
	function rename_session(self, session: number, name: string): (boolean, string?)
	function snapshot(self): LayoutSnapshot
	function restore(self, snap: LayoutSnapshot): (boolean, string?)
	function arrange(self, spec: Arrange): ({ TabArrangement }?, string?)
end

type Dir = "right" | "down" | "left" | "up"
type Corner = "tl" | "tr" | "bl" | "br"
type TabColor = "red" | "orange" | "yellow" | "green" | "teal" | "blue" | "purple" | "pink"
type Reveal = { focus: boolean? }
type FloatOpts = { focus: boolean?, size: { number }? }
```

| 方法 | 行为 | 返回 |
| --- | --- | --- |
| `new_tab(launch?)` | 在当前会话中打开一个运行 `launch` 的标签页，并使其成为活动标签页 | 新面板，或当 `launch.block` 指定的类型在该主机上不存在时为 `nil` |
| `split(target, dir, launch?)` | 在 `target` 的 `dir` 一侧用新面板分割面板 `target`，位于 `target` 的主机、`target` 的目录（除非设置了 `launch.cwd`）；新面板获取其标签页的焦点 | 新面板，或当 `target` 不在任何标签页中或该 block 类型缺失时为 `nil` |
| `focus(pane)` | 聚焦该面板（在本窗口内） | 无 |
| `close(pane)` | 对插件与 Carly 而言是原始的会话关闭 | 无 |
| `move(pane, target, dir, reveal?)` | 把面板移到目标的边缘，或以 `"swap"` 交换；对插件与 Carly 默认显示 | 移动时为 `true`，被拒绝时为 `false` |
| `resize(pane, dir, cells)` | 把面板最近的分隔条朝 dir 移动约 cells 个单元格；负值朝反方向移动 | 有分隔条移动时为 `true`，没有时为 `false` |
| `tab(spec)` | 构建工作区标签页并命名它 | 标签页 id（其首个面板无法启动时为 `nil`），然后是在任何面板无法启动时的错误字符串（[工作区](#workspaces)） |

`split`、`move` 与 `resize` 会抛出 ``unknown direction `<dir>` (right, down,
left or up)``。把面板移到另一台主机时，`move` refuses (returns `false`)。

`Reveal` 为 `{focus = boolean}`。插件与 Carly 共享相同的默认值：
创建与以往一样显示，`move` 聚焦被移动的 block，默认的
`split` 把其目标标签页的焦点交给新 block 而不切换标签页。
显式 true 会显示结果；false 保持当前显示的焦点。

`move_to_tab` 把 block 放在目标标签页聚焦叶子的旁边；
`move_to_new_tab` 在该 block 自己的或指定的会话中使其成为最后一个标签页。
跨主机移动会被拒绝。`float` 默认由接管旧区域及其最近角落的叶子
接管；已有的浮窗可被重新放置。`dock` 在其仍然有效时默认回到原分割，
否则在 owner 旁边。

`float` 的选项是 `Reveal` 加上 `size = {w, h}`，即浮窗在其掠视时的尺寸
（聚焦它仍会使其变大，与任何浮窗一样）。每个不超过 1 的值表示它浮于其上的框架的占比
（`{0.4, 0.3}`）；大于 1 则表示约等于那么多个终端单元格（`{80, 24}`：列宽、在其
顶部条之下的行高）。两者可以混用。尺寸按调用时的窗口计算，
像用户拖动的尺寸那样保存，并受布局的钳制：至少 240 × 150 px，至多占框架的某个比例。
浮窗仍然吸附到角落；没有自由位置。不是两个正数的尺寸会抛出
``size must be {w, h}: …``。当浮窗已落下但尺寸尚无法计算时
（窗口尚未排布，或没有终端测量过其单元格），`float` 返回 `true`
并说明尺寸未应用的原因。对浮窗调用 `float(pane, nil, nil, {size = …})` 会就地调整其尺寸。
[`float_moved`](events.md#float_moved) 事件说明用户拖动浮窗后把它放在哪里。

`park` 把 block 从其标签页取出，放入其会话的停靠面板牌堆中，
如 **Park pane**（⌃⇧↓）所做的那样，其程序仍在运行：其所在分割
收拢，或当它是该标签页唯一的 block 时该标签页关闭。对未知或已停靠的 block 返回
`false, why`。`unpark` 把已停靠的 block 发到当前标签页中其聚焦 block 的旁边，
如 **Parked panes** 所做的那样，并对未停靠的 block 返回 `false, why`。
要把已停靠的 block 放到别处，`move`、`move_to_tab`、`move_to_new_tab`、带 `over` 的 `float`、
`arrange` 与 `focus` 都可以直接从牌堆中取它。已停靠的 block 具有
`parked = true` 且没有 `tab`。

`even` 按标签页 id 均分分割。`name_tab` 对 nil/空值清除显式标题；
`color_tab` 对 nil 清除；`order_tab` 使用一基的会话位置。`rename_session`
拒绝空名称或未知会话。`snapshot` 捕获树、浮窗、名称、颜色、顺序与已停靠面板，而非
程序。若 block 被打开/关闭或保存的会话消失，
`restore` 返回 `false, why`；否则恢复且不夺取当前显示的焦点。

Carly 在一轮中的首次变更会捕获一份快照。若布局发生变化，
会在该轮结束时提供一个 **Carly rearranged your workspace** toast 与 **Undo**。
若其 block 已不再匹配，撤销会安全地拒绝。恢复的标签页标题与选中的填充立即出现，
没有新标签页的进入动效。

#### 单次调用分组 {#one-call-grouping}

`arrange` 原子地重新分组一个会话：

```lua
local tabs, err = cx.layout:arrange({
	tabs = {
		{name = "Build", color = "teal", blocks = {"cargo"}, split = "rows"},
		{tab = "2", name = "Logs", blocks = {}}, -- rename-only
	},
	rest = "keep",
})
```

`session` 可以是 id 或名称（默认当前）。`tab` 可以是 id 或 `find_tab` spec；
`blocks` 接受 id 或 `resolve` spec，例如 `"@focused"`。
未指定标签页时复用持有该组最多 block 的标签页（并列时取第一个），否则新建一个。
空的 `blocks` 不向该标签页移入任何内容，从而支持仅重命名的调用。分组按提供的顺序
领衔标签页列表；未被触及的标签页保持其相对顺序。省略的 `split` 保留目标树，
并将传入的 block 追加进去；`columns`、`rows` 或均衡的 `grid` 会重建它。
未被提及的 block 保持原位（`rest = "keep"`），或集中到一个末尾的 **Other** 标签页
（`"last"`）；分组中指定的已停靠 block 会离开其牌堆进入该组的标签页。空标签页关闭而不结束程序。
校验会在做出任何变更前拒绝未知、重复或跨主机的 block。结果包含每个结果会话标签页的
`{id, position, name, blocks}`。焦点留在同一 block 上并跟随其标签页。

Carly 的直接 `arrange` 工具接受等价的 JSON，并以与每次请求上下文相同的受限窗口大纲
作答，其中包括分割树。Carly 用该大纲进行定位，用共享的 Lua API 完成聚焦、标签页切换、
文件/URL 打开与终端创建。

### `Launch` 启动参数 {#launch}

```lua
type Launch = {
	cwd: string?,
	command: string?,
	block: string?,
	args: { string }?,
}
```

| 字段 | 含义 |
| --- | --- |
| `cwd` | 工作目录（默认：新标签页或分割的起始位置） |
| `command` | 由面板的登录 shell 运行的命令行，替代交互式 shell |
| `block` | 插件 block 类型 `"<plugin>.<id>"`；面板改为运行该 block（且 `command` 不使用） |
| `args` | 该 block 的启动参数 |

没有 `launch`（或为空）时运行 shell。

Carly 的 `new_tab`、`split` 与工作区 `tab` 启动使用锚点 block 所在的
机器与目录，忽略新标签页的 Home 偏好；`split` 锚定到其目标。`~` 与 `~/…` 在该机器上展开。
OSC 7 报告的 SSH 跳转目录必须属于已连接的主机，否则启动会在
改变窗口之前失败。当该目录的主机与分割目标的主机不同时，
Carly 会在该主机上打开一个标签页，而非在本地复用该远程路径。
普通插件的启动默认值不变。

### 工作区 {#workspaces}

```lua
type TabSpec = {
	cwd: string?,
	name: string?,
	split: Dir?,
	ratio: number?,
	launch: Launch?,
	[number]: TabSpec,
}
```

`cx.layout:tab(spec)` 从树构建标签页。带 `[1]` 与 `[2]` 的节点
是沿 `split`（默认 `"right"`）在两者之间的分割，`ratio`
设定第一侧的占比（默认一半）；不含这两个键的节点是运行其 `launch` 的叶子。
`cwd` 向下继承，直到某个节点指定自己的，而叶子的 `launch.cwd` 优先于两者。
根节点上的 `name` 为该标签页命名，无论构建结束时它是否为活动标签页。
有子节点的节点上的 `launch` 被忽略。

最左侧的叶子打开该标签页；随后树通过分割填充，每一层 `[1]` 先于 `[2]`。
`tab` 返回两个值：标签页 id，以及当某个面板无法启动时的错误字符串
（全部成功时为 `nil`）。

- 当最左侧的叶子无法启动（其 `launch.block` 指定的类型在该主机上没有任何
  Ready 插件定义）时，不打开任何标签页：``nil, "could not start
  block `<kind>`"``。
- 当分割的新侧无法启动时，该侧及其下所有内容被略去，树的其余部分仍然构建，
  并命名该标签页：``<id>, "could not start block `<kind>`"``。多个错误以
  逗号分隔列出；`command` 叶子显示为 `` `<command>` ``。

不会有人替你弹出提示；请按插件应有的方式报告该错误：

```lua
local tab, err = cx.layout:tab(spec)
if err then
	cx:toast("error", if tab then "Workspace opened incomplete" else "Workspace not opened", err)
end
```

```lua
tern.on("window_start", function(cx)
	cx.layout:tab({
		name = "stencil",
		cwd = (tern.getenv("HOME") or "") .. "/work/stencil",
		split = "right",
		{ launch = { command = "nvim" } },
		{
			split = "down",
			{ launch = { command = "cargo watch -x check" } },
			{},
		},
	})
end)
```

## 相关页面 {#related-pages}

- [命令、按键与覆盖](../guides/commands.md)、
  [路由打开与链接](../guides/routing.md)、
  [chrome 与样式](../guides/chrome.md)、[布局与工作区](../guides/layout.md)。
- [内置动作](actions.md)：命令 id 与动作名。
- [事件](events.md)：窗口事件的 payload 与顺序。
