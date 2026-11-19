# 调试 {#debugging}

当插件行为异常时，Tern 会在三个地方告知：窗口中的 toast、插件 catalog
（`tern plugin list`、偏好设置 › 插件），以及日志文件。本页说明每类失败
出现的位置、如何获得插件自己的日志行、用 luau-lsp 做类型检查、
从脚本驱动窗口的开发者工具，以及导致大多数 bug 的错误做法。

## 失败显示的位置 {#where-failures-show}

失败在其代码运行的地方上报，每次失败上报一次：

| 失败 | toast（文本 / 第二行） | 另外 |
| --- | --- | --- |
| 清单或文件夹问题：没有 `plugin.toml`、id 无效、缺少入口或样式文件、id 重复 | “1 个插件存在问题”或“*N* 个插件存在问题” / 第一条错误 | `tern plugin list` 中的 `problem DIR: ERROR`；不会列为插件 |
| host 入口在加载时抛出错误，或使已声明的 block 或 lens 未定义 | 同一条 catalog toast | `tern plugin list` 中状态为 `failed`，偏好设置中为 Failed |
| window 入口在加载时抛出错误 | “插件 *name* 加载失败” / 错误的第一行 | 偏好设置中为 Failed；**不会**出现在 `tern plugin list` 中 |
| 处理器抛出错误、返回形状不正确的值，或超出预算 | “插件 *name*：*hook* 失败” / 错误的第一行 | 日志中带 traceback 的 `plugin handler failed` 警告 |
| 组合键或状态段指向未加载的插件动作 | “没有插件提供此动作” / 动作名 | |
| 状态段的 `command` 无法解析 | “状态段的命令未知” / 该命令及原因 | |
| 无法解析的 `tern.bind` 组合键或动作，或预设已绑定的按键 | 无 | 日志中的 `plugin bind left out` 警告 |
| 含 CSS 错误的样式表 | 无 | 指明该样式表的 `plugin style sheet has errors` 警告 |

catalog toast 在 host 的 catalog 变化时出现（窗口附着时，以及改变了它的
重新加载之后）。若 window 重新加载失败的正是上一次加载的那些错误，
则不会再次弹 toast，因此损坏的插件每次变化只上报一次，而不是每次重新加载
都上报。host 处理器产生的 toast 发往显示相关面板的窗口，或对定时器、进程与
fetch 回调以及 `spawn` 过滤器发往该 host 的每个窗口。参见
[运行时、预算与 JIT](../concepts/runtime.md#failures-and-toasts)。

“插件 *name*：*hook* 失败”中的 hook 指明了是哪个处理器：
`command scratch`、`bind 0`、`override new_tab`、`route.open`、`status`、
`timer`、`counter.view`、`greet.line`、某个事件名。完整列表见
[运行时、预算与 JIT](../concepts/runtime.md#a-tripped-budget)。

## catalog {#the-catalog}

`tern plugin list` 打印为其所在面板提供服务的会话守护进程的插件，
每个插件一行，然后每个问题一行：

```text
hello 0.1.0 Hello — 1 blocks, 1 lenses, window  ready
problem /Users/me/Library/Application Support/Tern/plugins/broken: invalid id "Broken" (lowercase letters, digits and -, 1-32 long)
```

每行形如 `ID VERSION NAME — N blocks, M lenses[, window]  STATUS`，其中
STATUS 是 `ready`、`disabled`，或 `failed: ` 加错误的第一行。
`--json` 打印整个 catalog，包含条目、问题以及 host 的 `jit` 标志。

这些状态涵盖的内容：

- catalog 是 **host 的**。加载失败的 window 入口会让插件在这里仍为
  `ready`；应查看偏好设置或窗口的 toast。
- 没有守护进程运行时，`tern plugin list` 只读取插件文件夹，不运行任何
  Lua：此时 `ready` 仅表示清单有效，且设置允许该插件。

`tern plugin reload` 让守护进程重新加载每个插件，并打印新的 catalog。
当有插件失败或文件夹存在问题，它以 1 退出，因此可用作脚本或编辑器任务中的
检查。它需要运行中的守护进程（否则报 `no daemon running`）。
`install`、`remove`、`link` 与 `unlink` 也会重新加载，且只打印失败的部分。
参见 [命令行](../reference/cli.md)。

### 偏好设置 › 插件 {#preferences-›-plugins}

插件页面列出本机的插件，并带一个徽标：Ready、Off，或“Failed: ”加错误的
第一行。徽标取 host 状态与此窗口状态中较差的一个，因此当
`tern plugin list` 显示 `ready` 时，失败的 window 入口仍会在这里显示。
每个已附着的远程 host 的插件以该 host 的名称列在其后，只读。页面的
重新加载按钮会重新加载此窗口的插件以及每个已附着 host 的插件，
等同于命令面板的 **重新加载插件** 命令。

## 日志 {#logs}

### 自己的日志行 {#your-own-lines}

`tern.log.debug`、`info`、`warn` 与 `error` 写入一行，target 为
`tern::plugin`，字段为 `plugin=<id>`；`print` 即 `tern.log.info`。
默认过滤器 `warn,stencil=info` 让 Tern 自身的模块从 info 起记录，
其他一切从 warn 起。`tern::plugin` 不是 Tern 模块，因此**默认只写入
`tern.log.warn` 与 `tern.log.error`**；`print`、`info` 与 `debug` 被丢弃。

因此，开发时想查看某个值，最快的方式是
`tern.log.warn(...)`，或从 window 处理器发一个 toast
（`cx:toast("info", text)`）。要保留所有级别，启动进程时设置 `STENCIL_LOG`，
它会替换日志文件与标准错误所用的过滤器：

```sh
STENCIL_LOG=warn,stencil=info,tern::plugin=debug
```

进程在启动时读取 `STENCIL_LOG`。这对 host 半区很重要，因为它运行在会话
守护进程中：守护进程由第一个窗口启动，并带着启动时的环境在窗口关闭后继续
运行。要让 host 半区拥有自己的过滤器，请运行一个单独的守护进程。以
`TERN_DAEMON_SOCKET` 指向新 socket 启动的窗口，会在那里启动自己的守护进程，
它继承该窗口的环境：

```sh
export STENCIL_LOG=warn,stencil=info,tern::plugin=debug
export STENCIL_LOG_DIR=/tmp/tern-plugin-logs
export TERN_DAEMON_SOCKET=/tmp/tern-plugin-dev.sock
tern ~/src/my-plugin
```

该窗口及其守护进程把每个插件行记录到 `/tmp/tern-plugin-logs`。它打开的面板
属于那个守护进程，是与平常用途分开的会话；`STENCIL_LOG_DIR` 避免两个守护
进程写入同一文件。window 半区使用同样的过滤器记录，因为它运行在窗口进程中。

### 日志文件 {#log-files}

| 平台 | 日志文件夹 |
| --- | --- |
| macOS | `~/Library/Logs/Tern` |
| Linux | `$XDG_STATE_HOME/tern/logs`（`~/.local/state/tern/logs`） |
| Windows | `%LOCALAPPDATA%\Tern\Logs` |
| 任意 | `$STENCIL_LOG_DIR`（设置时） |

host 半区记录到 `tern-daemon.log`（当窗口在没有守护进程的情况下运行其面板
时，记录到该窗口的 `tern.log`）；window 半区记录到 `tern.log`。文件达到
16 MiB 时轮转为 `<name>.1.log`。命令面板的 **打开日志与应用状态** 会写出
缓冲的行并打开日志文件夹。

Tern 自身关于插件的报告按默认过滤器写入。可搜索这些消息：

| 消息 | 含义 |
| --- | --- |
| `plugin handler failed` | 处理器抛出错误；该行含 `plugin`、`hook` 以及带 traceback 的错误。 |
| `plugin hook exceeded its budget; paused` | 预算触发；`paused_ms` 说明暂停多久。 |
| `plugin hook resumed after its pause` | 暂停的钩子重新运行。 |
| `plugin failed to load` | host 入口失败。 |
| `plugin window entry failed to load` | window 入口失败。 |
| `not a usable plugin` | 文件夹问题。 |
| `plugin bind left out` | 组合键或动作无法解析，或预设已绑定这些按键。 |
| `plugin style sheet has errors` | 无法解析的 CSS，并给出样式表名称。 |
| `plugin spawn filter took over 50 ms; skipped` | 缓慢的 `spawn` 过滤器。 |
| `plugin keeps re-rendering; requests dropped` | block 在循环中请求渲染。 |

## 预算作为一种信号 {#budgets-as-a-signal}

超出预算的处理器会抛出 `tern: <hook> exceeded <n> ms`，弹一次 toast，
随后其钩子被**暂停**：首次触发后 5 s，若在上次暂停结束后不久再次触发则
时长翻倍（最多 5 分钟）。暂停期间的调用被跳过且不弹 toast，并以 debug 级别
记录为 `paused plugin hook skipped`；到期的定时器、进程与 fetch 回调会等待，
在暂停结束时运行。其表现是某个命令、绑定、格式化器或 block 视图弹了一次
toast 后在一段时间内毫无反应。偏好设置 › 插件以及（对 host 半区而言）
`tern plugin list` 会显示被暂停的钩子；window 半区在钩子暂停与恢复时会收到
`tern.on("budget", …)`。`tern plugin reload <id>` 可立即结束单个插件的暂停。

| 预算 | 适用于 |
| --- | --- |
| 4 ms | chrome 格式化器与 `available` 检查 |
| 50 ms | 其余每次 window 调用，包括 window 入口 |
| 2 s | 每次 host 调用，包括 host 入口 |

触发几乎总是意味着工作在错误的位置进行：在 window 处理器中遍历文件或做大读取、
随输入增长而变慢的解析、等待某事的循环。由于单位是钩子，一个缓慢的定时器
回调会禁用该 VM 中该插件的所有定时器回调。修好原因并重新加载：命令面板的
**重新加载插件**、`tern plugin reload`，或在包中保存文件。把耗时的工作移到
`tern.process.run`、分散到 `tern.timer` 回调，或移到 host 半区。参见
[运行时、预算与 JIT](../concepts/runtime.md#budgets)。

## 用 luau-lsp 做类型检查 {#type-checking-with-luau-lsp}

`tern plugin types DIR` 写出 `DIR/tern.d.luau`，即整个 `tern` 模块的定义。
在包目录中让 luau-lsp 指向它：

```sh
cd ~/src/my-plugin
tern plugin types .
```

`.vscode/settings.json`（或所用编辑器的 luau-lsp 设置）：

```json
{
  "luau-lsp.platform.type": "standard",
  "luau-lsp.sourcemap.enabled": false,
  "luau-lsp.types.definitionFiles": { "@tern": "tern.d.luau" }
}
```

在命令行上做同样的检查：

```sh
luau-lsp analyze --platform=standard --definitions=@tern=tern.d.luau host.luau window.luau
```

升级 Tern 后需重新写出定义。有三件事检查器不会告知：

- luau-lsp 会把 `require("tern")` 报告为未知的 require。请使用全局
  `tern`，它是同一个表。
- 该文件为两个入口声明同一个 `tern`。属于某个上下文的成员在其文档中标为
  `Host only` 或 `Window only`，但从 `window.luau` 调用 host 成员能通过
  类型检查，却在运行时报错。
- 类型在某些地方比运行时更宽：面板与标签页表中的 `cwd` 是 `string?`，
  因为 host 的 `tern.pane.list` 可能给出 `nil`，而 window 的表里始终是
  字符串（未知时为 `""`）。

## 从脚本驱动窗口 {#driving-a-window-from-a-script}

Tern 的开发者工具（`tern help dev`）可以带控制端点运行窗口并向其发送命令，
其中三个用于插件：

| 命令 | 作用 |
| --- | --- |
| `plugins run <action>` | 按名称运行动作，如同绑定到它的按键：`plugins run plugin.scratch.scratch`、`plugins run new_tab`。 |
| `plugins expect "<text>"` | 等到焦点面板的某个 surface（插件 block 的视图、lens block 的原生视图）显示该文本。 |
| `plugins fixtures` | 用 Tern 的测试插件替换插件文件夹并加载它们（含 host 半区），使用 `settings.json` 保存的 `plugins` 与 `plugins_disabled`。 |

以 `--control` 启动的窗口照常运行插件，因此 `plugins run` 与
`plugins expect` 测试的是真实的包：

```sh
tern --control /tmp/tern-ctl.sock ~/src/my-plugin &
tern ctl --control /tmp/tern-ctl.sock plugins run plugin.counter.open
tern ctl --control /tmp/tern-ctl.sock plugins expect '"Count: 0"'
tern ctl --control /tmp/tern-ctl.sock css
tern ctl --control /tmp/tern-ctl.sock tree "[data-surface='plugin.counter.counter']"
```

在 Tern 面板中，不带 `--control` 的 `tern ctl` 驱动输入它的那个窗口，
无需设置任何端点：在那里执行 `tern ctl css` 会列出该窗口的样式表。

[脚本](../scripts/index.md) 记录了脚本或 `ctl` 可以发送的每条命令。

`ctl` 把各个词拼成一条命令行，因此对场景解析器需要引号的文本，要在 shell
引号内再加引号。其他控制命令对样式排查有帮助：`css` 按层叠顺序列出已安装的
样式表（寻找 `plugin:local:<id>:styles` 以及 `tern.css` 的名称），
`tree SEL` 显示选择器匹配到的可见元素，`state` 以 JSON 打印应用状态。

`plugins fixtures` 用于开发 Tern 本身。它从构建该二进制文件的源码树加载
fixtures，且只在自行运行面板的进程中可用：无头运行（`tern shot`、
`tern serve`），这些进程本来不加载插件。在附着到守护进程的窗口中，它会以
`a daemon runs this machine's panes, with its own plugins` 失败。一个场景
如下所示：

```text
ready
plugins fixtures
palette "New Counter"
key Enter
plugins expect "Count: 0"
type "+"
plugins expect "Count: 1"
shot plugin-block
```

## 常见错误 {#common-mistakes}

### 留到以后使用的 `cx` {#a-cx-kept-for-later}

window 的 `cx` 只在收到它的那次调用期间有效。把它存进 upvalue，并在定时器、
进程或 fetch 回调或之后的事件中使用，会抛出错误。定时器、进程与 fetch 回调
各自获得一个新的 `cx`；请使用那个。

```lua
tern.on("window_start", function(_cx)
	tern.timer(1000, function(cx)
		if cx then
			cx:toast("info", "Use the cx you were given")
		end
	end)
end)
```

### `--!strict` 下的 props {#props-under-strict}

节点的 `p` 类型为 `{ [string]: any }?`，因此当 `p` 可能不存在时，
`node.p.actions = …` 无法通过类型检查。先构建表，再赋值：

```lua
local node = tern.ui.badge("Retry", "accent")
local p: { [string]: any } = node.p or {}
p.actions = { click = "retry" }
node.p = p
```

在 `--!strict` 下，还要让 span 列表只包含 span（在 span 表之间混入裸字符串
无法通过检查），并把柱状图与 sparkline 的 series 标注为
`local series: { { any } } = {}`。参见
[UI 构建器](../reference/ui.md)。

### 通过 `data-role` 为 block 设置样式 {#styling-blocks-through-data-role}

插件 block 的类型体现在其区域元素的 `data-surface` 上，而不是 `data-role`：

| 目标 | 选择器 |
| --- | --- |
| 插件 block | `.sf-main[data-surface='plugin.<plugin>.<block>']`（另有 `.sf-dock`、`.sf-layer`） |
| lens block | `.sf-block[data-role='lens.plugin.<plugin>.<lens>']` |
| 自己的节点 | 来自节点 `role` 属性的 `[data-role='…']` |

对 `--control` 窗口执行 `tern ctl tree SEL` 可看出选择器是否匹配。参见
[chrome 与样式](chrome.md#useful-selectors)。

### 写入插件目录 {#writing-into-the-plugin-directory}

包目录会被监视，其中的任何改动都会重新加载该上下文中的所有插件。把缓存或
日志文件写在入口旁边的插件会不断重新加载自身。请写入 `tern.plugin.data`。

### 格式化器中永不变化的值 {#values-that-never-change-in-a-formatter}

chrome 格式化器按其输入缓存。读取时钟、文件或进程结果的格式化器会一直显示
第一个答案，直到其输入变化。把数据放在 upvalue 中，并在数据变化时调用
`tern.chrome.refresh()`（对时钟而言是从定时器中调用）。参见
[chrome 与样式](chrome.md#refreshing)。

### 毫无作用的组合键 {#a-chord-that-does-nothing}

当默认键位或 `keymap` 预设已绑定某个组合键（或它开头的序列）时，插件的绑定
会被略过，并产生 `plugin bind left out` 警告，不弹 toast。请选用默认键位
未占用的组合键，或在 `settings.json` 的 `keybinds` 中绑定该动作，它的优先级
高于所有层。参见 [命令、按键与覆盖](commands.md#keymap-layering)。

### 检查了错误的机器 {#checking-the-wrong-machine}

`tern.fs` 与 `tern.process` 作用于其半区所运行的机器。window 半区为远程
host 上的面板读取 `pane.cwd` 时，检查的是窗口的磁盘，而不是该 host 的。
请把远程面板的文件检查放到 host 半区，并安装在该 host 上。

## 另见 {#see-also}

- [生命周期与重新加载](../concepts/lifecycle.md)：插件何时加载与
  重新加载。
- [运行时、预算与 JIT](../concepts/runtime.md)：预算、toast 与
  日志 target。
- [错误](../reference/errors.md)：错误消息及其原因。
- [命令行](../reference/cli.md)：`tern plugin` 的完整内容。

<!-- 原文有行内代码跨行断开，校验工具会把这些行内代码之间的散文误判为代码；以下片段仅用于对齐中英行内代码集合，不渲染：
` and `
`, `
`). To keep every level, start the process with `
-->
