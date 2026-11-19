# 运行时、预算与 JIT {#runtime-budgets-and-jit}

每个插件半区都在各自的 Luau VM 中运行：沙箱化、上限 256 MiB，
并在某次调用超出其时间预算时被中断。失败的调用只损失该次调用；
超出时间的调用还会让其钩子暂停一段时间。本页说明该 VM、各项预算以及
预算触发时会发生什么、失败如何上报与记录，以及 Luau 何时
以原生代码运行。

## VM {#the-vm}

每个 VM 都是一份 Luau 状态，带有 Luau 的标准库，并在任何插件代码运行
之前被置于沙箱模式：

| 可用 | 不可用 |
| --- | --- |
| Luau 的基础函数（`pcall`、`error`、`pairs`、`setmetatable`、`typeof`、`loadstring` 等） | `io`：Luau 没有 I/O 库 |
| `string`、`table`、`math`、`coroutine`、`utf8`、`bit32`、`buffer`、`vector`、`integer` | Luau 的 `os`，除 `clock`、`date`、`difftime` 与 `time` 之外的部分（没有 `os.execute`、`os.getenv`、`os.remove`、`os.exit`） |
| Luau 的 `debug`，其中只有 `debug.info` 与 `debug.traceback` | |
| `os.clock`、`os.date`、`os.difftime`、`os.time` | `package`、`dofile`、`loadfile` |
| `require`，限于该插件之内（[模块](#modules)） | `collectgarbage` 中除 `"count"` 之外的选项 |
| `print`，即 `tern.log.info` | 修改内置库：它们是只读的（`string.upper = nil` 会报错） |
| 全局 `tern`（[API 参考](../reference/api.md)） | |

带日期表的 `os.time` 按本地时间解读该表，与标准 Lua 一致，因此它是
`os.date("*t")` 的逆运算：`os.time(os.date("*t", t)) == t`。Luau 自带的
`os.time` 会将该表读作 UTC；Tern 的不会。本地时区就是半区所运行机器所在的时区：
位于远程 host 上的 host 半区使用该 host 的时区。超出范围的字段会顺延
（`day = 32` 表示下个月的第一天），夏令时切换所跳过的时间向后移动一小时，
而重复出现的时间取第一个，除非表中写明 `isdst = false`。
对于以 UTC 给出的时间（`os.date("!*t")`、带 `Z` 的时间戳），需自行换算
日期，如 [Review Queue](../examples/review-queue.md) 示例所做的那样。

插件定义的全局变量是普通的：它们位于只读库之上的可写层中，在该 VM 内
由入口及其加载的每个模块共享。

文件、进程、环境、网络与钥匙串只能通过 `tern`（`tern.fs`、`tern.process`、
`tern.fetch`、`tern.getenv`、`tern.secrets`）访问；不存在离开该 VM 的其他
途径。这是一道为健壮性而设的边界，并非安全边界：这些 `tern` 成员能触及
用户所能触及的一切。参见
[信任与安全](security.md)。

## 模块 {#modules}

`require` 接受一个字符串。`"tern"` 返回 `tern` 表，也就是作为全局安装的
同一个表。其余参数使用 Luau 的按字符串 require，相对于调用 `require` 的
文件解析，并限于插件目录之内：

- `./name` 与 `../name` 解析为 `name.luau`、`name.lua`、
  `name/init.luau` 或 `name/init.lua`；匹配到多个即为错误。
- 会离开插件目录的路径按未找到处理并失败。
- 不读取 `.luaurc` 文件与 `@alias` 路径。
- 模块在每个 VM 中只运行一次；之后对同一文件的 `require` 返回其
  缓存结果。

代码块以其绝对路径命名，因此错误信息与 traceback 会给出文件名与行号。

```lua
-- host.luau
local pods = require("./lib/pods")

-- lib/pods.luau
local M = {}

function M.parse(text: string): { string }
	local out = {}
	for line in string.gmatch(text, "[^\n]+") do
		table.insert(out, line)
	end
	return out
end

return M
```

luau-lsp 无法解析 `require("tern")`；需要类型检查的代码应使用
全局 `tern`。参见 [API 参考](../reference/api.md#types-for-luau-lsp)。

## 内存 {#memory}

每个 VM 最多可分配 256 MiB。超过上限的分配会在发起它的那次调用中抛出
Luau 内存错误。这是普通错误：该次调用失败，并与其他错误一样被上报，
`pcall` 可以捕获它，钩子保持启用。host 半区为 block 与 lens 捕获保留的
Lua 状态计入其 VM 的上限，这也是工作线程只为最近 256 次 lens 捕获保留
状态的原因之一。

## 预算 {#budgets}

每一次进入 Lua 的调用都在时间预算下运行，预算取决于它运行的位置：

| 调用 | 预算 | 原因 |
| --- | --- | --- |
| Host：每次调用，包括运行 `host.luau` | 2 s | 缓慢的工作线程只拖住自己的插件 |
| Window：chrome 格式化器（`tab_title`、`window_title`、`status`）与 `available` | 4 ms | 它们在窗口构建一帧时运行 |
| Window：其余每次调用，包括运行 `window.luau` | 50 ms | 它运行在 UI 线程上，其间窗口不做其他事 |
| 守护进程等待 `spawn` 过滤器 | 每个插件 50 ms | shell 正等着启动 |

`spawn` 的等待不是 VM 预算：过滤器本身在工作线程上、于 2 s 的 host 预算
下运行，但守护进程在 50 ms 后就不再等待该插件的答复，并以该插件生效之前
的 spec 启动 shell（记录为 `plugin spawn filter took over 50 ms; skipped`）。
参见 [host 钩子与 spawn 过滤器](../guides/hooks.md)。

当同一 VM 中的一次调用内部又发起调用时，若外层调用的截止时间更早，
内层调用沿用该截止时间。

预算只计 Lua 运行的时间。花在原生代码上的时间不计入：
Tern 的 API（`cx.board:open`、`cx.agents:list`、`tern.fs.read`、
`tern.process.run`）、为 `require` 编译模块、耗时的内置函数（一个巨大的
`string.rep`），或线程等待 CPU 的时间。迟触发的定时器从实际运行时开始计
预算，而不是从应触发的时刻。为使一连串缓慢的原生调用仍能终止，
一次调用最多还可占用十个预算的墙上时间，原生调用包含在内（窗口内 500 ms，
chrome 格式化器内 40 ms，host 半区内 20 s）；超过后抛出
`tern: <hook> exceeded <n> ms, native calls included`。

预算通过 Luau 的中断机制强制执行，该机制在函数调用、返回与循环迭代处
运行。原生调用绝不会被中途停止：Tern 在其返回时再次检查，而永不返回的
调用会挂住其线程。对 FIFO 或网络挂载上停止响应的文件做无界的 `tern.fs.read`，
会在等待期间一直阻塞窗口，可能直到 Tern 被杀掉；传入 `max_bytes`，
它会拒绝除普通文件之外的一切。`tern.process.run` 在返回之前就在调用线程上
启动其进程，因此启动缓慢的程序（带大量配置的 shell、Windows 上的 PowerShell）
同样占用 UI 线程的时间。

预算用于拦截意外情况：死循环、随输入增长而变慢的解析。
耗时较长的工作应放在 `tern.process.run` 中，或分散到 `tern.timer` 回调里，
绝不放在 UI 线程上的循环中。

## 预算触发时 {#a-tripped-budget}

超出截止时间的调用会抛出 `tern: <hook> exceeded <n> ms`。从那一刻起，
该调用中的每次中断检查都会再次抛出，直到该调用返回，因此处理器内部的
`pcall` 无法捕获该错误并继续执行。调用返回后，其钩子在该 VM 中暂停：

- 首次触发会将钩子暂停 5 s。在上次暂停结束后的 10 分钟内再次触发，
  暂停时长翻倍，最多 5 分钟；若连续 10 分钟没有触发，下一次触发又从
  5 s 重新开始。持续触发的钩子每次暂停期间只运行一次，且永远不会
  被永久关闭。
- 钩子暂停期间，其调用会被跳过：不运行，也不弹 toast
  （`tern: <hook> is paused for <n> s after exceeding its budget`，
  以 debug 级别记录为 `paused plugin hook skipped`）。此间到期的定时器、进程、
  fetch 与 await 回调不会丢失：它们会在暂停结束时运行，而多次到期的定时器
  只运行一次。
- 暂停及其结束都会被记录（`plugin hook exceeded its budget; paused`，含 `paused_ms`，以及 `plugin hook resumed after its pause`）。
  window 半区还会以 `budget` 事件收到这两个通知（参见
  [Window API](../reference/api-window.md#ternon)）：
  先是 `{hook, state = "paused", ms, paused_ms}`，然后是 `{hook, state = "resumed"}`。
- 暂停的钩子显示在偏好设置 › 插件中（两个半区），对 host 半区还会显示在
  `tern plugin list` 中（`paused over budget: <hooks>`）。

被暂停的单位是钩子：

| 上下文 | 钩子名称 |
| --- | --- |
| Host | `load`（入口）；`<block>.init`、`<block>.view`、`<block>.title`、`<block>.key`、`<block>.event`、`<block>.resize`、`<block>.save`；`<lens>.open`、`<lens>.line`、`<lens>.finish`、`<lens>.view`、`<lens>.event`；每个 `tern.on` 事件名（`command_started`、`cwd` 等）与 `spawn`；`timer`；`process`；`fetch` |
| Window | `load`；`command <id>`；`bind <n>`；`override <command>`；`available plugin.<plugin>.<id>`；`route.open`；`route.link`；`tab_title`；`window_title`；`status`；每个 `tern.on` 事件名（`window_start`、`focus` 等）；`timer`；`process`；`fetch` |

因此，触发预算的 `view` 会在暂停期间停止渲染该类型的所有 block，而一个
缓慢的定时器回调会在暂停结束前占住该 VM 中该插件的所有定时器回调。
钩子按 VM 划分：某个窗口中的触发不会暂停另一个窗口中的钩子。重新加载会
创建全新的 VM 并结束所有暂停；`tern plugin reload <id>` 只对单个插件这样做。

## 失败与 toast {#failures-and-toasts}

抛出错误的处理器只损失该次调用：插件继续运行，其状态就是处理器抛出之前
留下的状态，失败会被记录并显示：

| 失败 | toast（第一行 / 第二行） | 显示位置 |
| --- | --- | --- |
| 处理器抛出错误、返回形状不正确的值，或触发其预算 | “插件 *name*：*hook* 失败” / 错误的第一行 | Host：显示相关面板的窗口；对于定时器、进程与 fetch 回调以及 `spawn` 过滤器，则是该 host 的每个窗口。Window：该窗口。 |
| window 入口加载失败 | “插件 *name* 加载失败” / 错误的第一行 | 该窗口，除非相同的失败已由前一次加载上报过 |
| host 的 catalog 存在问题或有 Failed 插件 | “1 个插件存在问题”或“*N* 个插件存在问题” / 第一条错误 | 附着到该 host 的每个窗口，在其 catalog 变化时 |
| block 的 `init` 抛出错误 | 处理器 toast，且该 block 以退出状态 1 结束，错误打印在面板中 | 显示该 block 的窗口 |

触发预算只在其触发时弹一次 toast；被暂停钩子跳过的调用不再弹 toast。
错误消息本身参见 [错误](../reference/errors.md)。

## 日志 {#logs}

`tern.log.debug`、`info`、`warn` 与 `error` 用制表符（经 `tostring`）拼接
其参数，并在该级别下通过 Tern 的 tracing 记录一行，target 为 `tern::plugin`，
字段为 `plugin=<id>`。`print` 即 `tern.log.info`。

日志行写入该半区所运行进程的日志文件：

| 平台 | 日志文件夹 |
| --- | --- |
| macOS、iOS | `~/Library/Logs/Tern`（在 iOS 上位于应用的容器内） |
| Linux | `$XDG_STATE_HOME/tern/logs`（`~/.local/state/tern/logs`） |
| Windows | `%LOCALAPPDATA%\Tern\Logs` |
| 任意 | `$STENCIL_LOG_DIR`（设置时） |

host 半区记录到 `tern-daemon.log`（当窗口在没有守护进程的情况下运行其面板时，
记录到该窗口的日志）；window 半区记录到该窗口的 `tern.log`。文件达到 16 MiB
时轮转为 `<name>.1.log`，`<name>.2.log` 是保留的最旧一份。警告与错误还会
写入标准错误。

默认过滤器是 `warn,stencil=info`：Tern 自身的模块（`stencil_*`）从 info 起
记录，其他一切从 warn 起。`tern::plugin` 不是 `stencil` target，因此默认只有
`tern.log.warn` 与 `tern.log.error` 会写入文件；`print`、`tern.log.info` 与
`tern.log.debug` 被丢弃。要保留它们，启动进程时设置 `STENCIL_LOG`；它会替换
文件与标准错误两处的过滤器：

```sh
STENCIL_LOG=warn,stencil=info,tern::plugin=debug
```

运行时自身的报告位于 Tern 的 target 之下，默认以 warn 级别写入文件：
`plugin handler failed`（含 `plugin`、`hook` 以及带 traceback 的错误）、
`plugin hook exceeded its budget; paused`、`plugin failed to load`、
`plugin window entry failed to load`、`not a usable plugin`、
`plugin spawn filter took over 50 ms; skipped`、
`plugin keeps re-rendering; requests dropped`、`plugin bind left out` 与
`plugin style sheet has errors`。参见 [调试](../guides/debugging.md)。

## 定时器、进程与 fetch 回调 {#timers-process-and-fetch-callbacks}

`tern.timer`、`tern.process.run` 与 `tern.fetch` 的回调绝不会在另一个线程上
运行。当定时器到期、进程结束或请求完成时，该 VM 的属主被唤醒，并在与该 VM
其他所有处理器相同的线程上自行运行该回调：

| 上下文 | 运行于 | 回调参数 | 预算 |
| --- | --- | --- | --- |
| Host | 插件的工作线程，在请求之间 | `fn()`、`cb(result)` | 2 s |
| Window | 窗口的 UI 线程，在渲染之后 | `fn(cx)`、`cb(result, cx)`，各带一个新的 `cx` | 50 ms |

进程或请求在 VM 的线程之外运行；只有其回调会回来。由于回调与其他所有处理器
串行执行，Lua 状态无需加锁，回调也绝不会中途打断处理器。到期的定时器、
已结束的进程与已完成的请求按最旧优先运行。待处理的定时器、进程与 fetch 回调
随其 VM 在下一次重新加载时结束；进程或请求本身则运行到结束。参见
[文件、进程与存储](../guides/io.md)。

## JIT {#jit}

在 macOS、Linux 与 Windows 上，Tern 的发布构建包含 Luau 的原生代码生成器；
当 CPU 属于 Luau 代码生成器所支持的类型时，它会把加载的每个 chunk（入口与
模块）编译为原生代码，否则由解释器运行。从源码构建的开发版本不包含代码
生成器，除非以 `luau-jit` feature 构建，否则以解释方式执行。macOS 应用以
`com.apple.security.cs.allow-jit` 授权签名，加固运行时要求进程在创建可执行
内存之前必须持有该授权。iOS 禁止应用使用可执行内存，因此 iOS 上的 Tern
不包含代码生成器，始终解释执行。插件代码在两种模式下相同，只有速度不同。

当该 VM 启用原生代码生成时，`tern.runtime.jit` 为 `true`。host 的 catalog 也
带有 `jit`（只要有任一 host 半区在启用 JIT 的状态下加载即为 true），`tern plugin list --json`
会打印它。

`jit` 能说明与不能说明什么：

| `jit` 报告 | `jit` 不报告 |
| --- | --- |
| 该构建包含 Luau 的代码生成器（iOS 与开发构建中为 false） | 某个特定函数是否被编译为原生代码 |
| CPU 受代码生成器支持，在创建 VM 时检查 | 操作系统是否实际授予了可执行内存 |
| | 关于另一半区或其他 host 的任何信息；每个 VM 只报告自己的情况 |

用它做诊断，而不是用来选择代码路径。

## 数字与 id {#numbers-and-ids}

Luau 的 `number` 是 64 位浮点数：整数在 2<sup>53</sup> 以内精确。
`tern` API 接受或返回的每个数字都是 `number`。
`tern.json.encode` 把整数写作 JSON 整数，其他数字写作浮点数；
`tern.json.decode` 把 JSON 数字读作 Luau 数字。
Luau 的 `integer` 库（把 64 位整数作为独立值类型）也已加载，但 `tern` 中
没有任何东西会产生这类值。

面板与标签页的 id 是数字。在 host 半区中，它们是守护进程自己的 id。
在 window 半区中，本机的 id 就是 `tern ls` 所显示的那些。远程 host 的面板在
高位带有 host 标记，这些位无法在 double 中保留，因此 Tern 在把这类 id 交给
Lua 之前将其压到 2<sup>53</sup> 以下，并在 Lua 传回时解包。
把 id 视为不透明的值：原样传回，不要对其做算术，也不要比较来自不同窗口的 id。

## 相关页面 {#related-pages}

- [限制](../reference/limits.md)：所有预算与上限汇总在一张表中。
- [生命周期与重新加载](lifecycle.md)：重新加载会重置什么。
- [调试](../guides/debugging.md)：定位出错的处理器。

<!-- 原文有行内代码跨行断开，校验工具会把这些行内代码之间的散文误判为代码；以下片段仅用于对齐中英行内代码集合，不渲染：
`, with `
`, and `
-->
