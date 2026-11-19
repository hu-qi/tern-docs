# 错误 {#errors}

插件作者或用户可能遇到的每一条消息，按出现位置分组，并给出原因与修复方法。引述的文本为原文逐字；`<…>` 标记其中的可变部分。大多数消息通过五种渠道之一送达：

| 渠道 | 落入其中的内容 | 到哪里查看 |
| --- | --- | --- |
| 抛出的错误 | 对 `tern` 的调用拒绝了其参数 | 调用方的处理函数失败；`pcall` 可以捕获 |
| 处理函数 toast | 处理函数抛出异常、超出预算，或返回了不合法的值 | “Plugin *name*: *hook* failed”，其下为错误的第一行 |
| 问题 | 某个文件夹条目不是可用的插件 | `tern plugin list`、偏好设置 › 插件、“plugins have problems” toast |
| Failed 状态 | 插件的某个入口未能加载 | `tern plugin list`（host）、偏好设置、“Plugin *name* failed to load”（window） |
| 日志 | 运行时报告、含 traceback 的完整错误文本 | `tern-daemon.log` 或窗口的 `tern.log`；参见[调试](../guides/debugging.md) |

## 处理函数失败 {#handler-failures}

处理函数抛出异常时，只有这次调用失败，别的都不受影响：插件继续运行，其状态停留在处理函数抛出之前留下的样子。Tern 会记录 `plugin handler failed`（warn），带上插件、钩子以及含 traceback 的完整错误，并显示一个 toast：

```text
Plugin Kubernetes: pods.view failed
/Users/me/src/tern-k8s/host.luau:42: attempt to index nil with 'items'
```

第一行给出插件名（即清单中的 `name`）与**钩子**；第二行是错误的第一行。钩子名称列在[运行时、预算与 JIT](../concepts/runtime.md#a-tripped-budget)中。host 的失败会在显示相关面板的窗口中弹出 toast；对于定时器、进程与 fetch 回调以及 `spawn`，则会在该 host 的每个窗口中弹出；window 的失败只在该窗口中弹出。

| 消息 | 原因 | 修复 |
| --- | --- | --- |
| `tern: <hook> exceeded <n> ms` | 调用超出了其预算：2000（host）、50（window）或 4（格式化器、`available`）。该次调用中之后的每次中断都会再次抛出，因此 `pcall` 无法挽回 | 把工作移到 `tern.process.run`，拆分到多个 `tern.timer` 回调中，或限制输入。该钩子会在那个 VM 中暂停，首次 5 s，反复触发时更长 |
| `tern: <hook> is paused for <n> s after exceeding its budget` | 对更早触发过预算、且仍在暂停中的钩子的调用；跳过而不运行，以 debug 级别记录日志，从不弹出 toast | 修复那个慢的钩子；暂停结束后它会再次运行，或在 `tern plugin reload <id>` 之后立即运行 |
| 一个 Luau 内存错误 | VM 达到了 256 MiB | 少存状态；丢弃对大型字符串与表的引用 |
| `cx is already in use` | 在同一个 `cx` 的另一次调用仍在运行时发起了该窗口的 `cx` 调用（例如来自嵌套的处理函数） | 使用处理函数收到的那个 `cx`，一次只调用一个 |
| `the plugin is gone` | 在其 VM 已被丢弃之后调用了 `tern.timer`（来自重载后仍然存活的回调） | 无需处理；旧的 VM 已消失 |

block 的 `init` 抛出异常也会结束该 block：错误与 traceback 打印在面板中，面板以状态 1 退出。

## 加载失败 {#load-failures}

入口失败的插件处于 **Failed** 状态；其他插件正常加载。

| 消息 | 位置 | 原因 | 修复 |
| --- | --- | --- | --- |
| toast “Plugin *name* failed to load”，其下为错误的第一行 | window | `window.luau` 抛出异常、超出 50 ms 预算，或无法读取 | 修复该入口；只有失败发生变化时该 toast 才会再次出现 |
| `tern plugin list` 中的 `failed: <first line>`，偏好设置中状态为 Failed | host | `host.luau` 抛出异常或超出 2 s 预算 | 修复该入口；重新加载 |
| `block <id> is declared in plugin.toml but not defined with tern.block.define` | host | 清单声明了一个入口从未定义的 block | 在 `host.luau` 中调用 `tern.block.define("<id>", …)`，或删除 `[[blocks]]` 表 |
| `lens <id> is declared in plugin.toml but not defined with tern.lens.define` | host | lens 同理 | 调用 `tern.lens.define`，或删除 `[[lenses]]` 表 |
| `cannot read <path>: <io error>` | host 或 window | 入口文件已消失或不可读 | 恢复该文件 |
| `the plugin's worker stopped` | host | 工作线程在报告之前就已结束 | 检查日志中是否有崩溃 |
| `cannot start the plugin's worker: <error>` | host | 操作系统拒绝了新线程 | 释放资源；重新加载 |
| toast “1 plugin has problems” 或 “*N* plugins have problems”，其下为第一个错误 | window | host 的 catalog 发生变化，其中含有问题或 Failed 插件 | 运行 `tern plugin list` 查看全部 |

与它们一同记录的有：`plugin failed to load`（host）、`plugin window entry failed to load`（window）、`not a usable plugin`（每个问题一条）。

## 插件文件夹问题 {#plugins-folder-problems}

无法成为插件的文件夹条目会连同其目录一起列为问题，并且不加载任何内容。修复方法见[清单参考](manifest.md)。

| 消息 | 原因 |
| --- | --- |
| `no plugin.toml` | 该目录的顶层没有清单 |
| `cannot read plugin.toml: <io error>` | 清单不可读，或不是 UTF-8 |
| `plugin.toml is larger than 64 KiB` | |
| `missing schema`、`unsupported schema <n>`、`schema must be an integer` | `schema` 缺失、不等于 `1`，或不是整数 |
| `invalid id "<id>" (lowercase letters, digits and -, 1-32 long)` | |
| `name must be 1-64 characters` | |
| `needs a host or window entry` | `host` 与 `window` 都没有 |
| `<host\|window\|style> "<path>" must be a relative path inside the plugin` | 绝对路径、`..`，或空路径 |
| `<host\|window> "<path>" must be a .luau or .lua file` | |
| `blocks need a host entry`、`lenses need a host entry` | 有 `[[blocks]]` 或 `[[lenses]]` 但没有 `host` |
| `invalid block id "<id>"`、`duplicate block id "<id>"` | |
| `invalid lens id "<id>"`、`duplicate lens id "<id>"`、`lens "<id>" needs at least one match pattern` | |
| ``unknown field `<key>`, expected one of …``、``missing field `<key>` ``、`invalid type: …` | TOML 键与类型（解析器的输出文本） |
| `missing entry <path>` | `host` 或 `window` 文件不存在 |
| `cannot read style <path>: <io error>`、`styles are larger than 256 KiB` | |
| `duplicate id <id>` | 按名称顺序排在前面的某个条目已占用该 id；删除或重命名其中之一 |
| `too many plugins` | 有效包超过 64 个；按 id 排在 64 之后的被略去 |
| `cannot read link: <io error>` | 某个 `<name>.path` 文件不可读 |
| `link target "<text>" is not an absolute path` | `.path` 文件的内容是相对路径；用 `tern plugin link` 重新链接 |
| `link target <dir> is not a directory` | 链接的包已移动或被删除；用 `tern plugin unlink` 或重新链接 |

## 注册错误 {#registration-errors}

由执行注册的调用抛出，通常发生在入口加载期间（导致插件失败），也可能来自处理函数。

| 消息 | 原因 |
| --- | --- |
| `tern.block.define: block "<id>" is not declared in plugin.toml` | 先在 `[[blocks]]` 表中声明该 block |
| ``tern.block.define: <id>: `<init\|view>` must be a function`` | 必需的处理函数缺失或不是函数 |
| `tern.block.define: <id>: unknown font "<x>" (mono, sans)` | `font` 既不是 `"sans"` 也不是 `"mono"` |
| `tern.lens.define: lens "<id>" is not declared in plugin.toml` | 先在 `[[lenses]]` 表中声明该 lens |
| ``tern.lens.define: <id>: `<open\|line\|finish\|view>` must be a function`` | 必需的处理函数缺失或不是函数 |
| `tern.on: unknown host event "<name>" (spawn, command_started, command_finished, cwd, title, pane_exited)` | host 上下文不传递该名称（[事件](events.md#host-events)） |
| ``tern.on: unknown window event `<name>` `` | window 上下文不传递该名称（[事件](events.md#window-events)） |
| ``tern.command: bad id `<id>` (letters, digits, `_` and `-`; not `bind`)`` | |
| `tern.bind: the action is a name or a function` | 第二个参数两者都不是 |
| ``tern.override: unknown command `<id>` `` | 不是内置命令 id（[内置动作](actions.md#commands)） |
| ``tern.css: bad name `<name>` (letters, digits, `_` and `-`; not `styles`)`` | |
| ``tern.files.button: bad id `<id>` (letters, digits, `_` and `-`)`` | |
| ``attempt to index nil with 'define'``、`attempt to call a nil value` | 调用了另一个上下文的成员：`window.luau` 中的 `tern.block.define`、`host.luau` 中的 `tern.command`（[上下文](api.md#contexts)） |

`tern.bind` 在调用时不再检查其他内容。重建键位映射时，
组合键或动作无法解析的绑定会被略去，并以
`plugin bind left out` 连同原因记录日志（``unknown action `<name>` ``、
``unknown modifier `<m>` ``）；某个绑定的键已由预设绑定时，
记录为 `plugin bind left out: the preset binds these keys`。

## 返回值 {#returned-values}

返回了错误形态的处理函数会像抛出的错误那样失败，同样以它的钩子名称报告。

| 消息 | 钩子 | 原因 |
| --- | --- | --- |
| `view: expected {main?, dock?, layer?}, got <value>` 以及[视图模型](api-host.md#view-model)下列出的节点错误 | `<block>.view` | block 视图格式不正确；上一次有效的视图保留 |
| `spawn must return a spec table or nil, got <type>` | `spawn` | 过滤器返回了字符串、数字或布尔值；其结果被忽略 |
| `a route returns a decision table or nil` | `route.open`、`route.link` | |
| `a route decision sets block, url, path or handled = true` | `route.open`、`route.link` | 表中不含任何决策键 |
| ``a route decision has an unknown how `<how>` `` | `route.open`、`route.link` | `how` 不是 `default`、`beside`、`below`、`split`、`tab`、`replace`、`over` 或 `preview` |
| `a title formatter returns a string or nil` | `tab_title`、`window_title` | |
| `a status formatter returns a list of segments or nil` | `status` | |

失败的路由处理函数按“未接手”计；接着运行下一个处理函数，或 Tern 自身的打开流程。

## API 错误 {#api-errors}

由 `tern` 的成员抛出；各成员页面在上下文中逐一说明。

| 消息 | 抛出者 | 原因 |
| --- | --- | --- |
| `cannot encode a <type> as JSON`、`cannot encode a <type> key as JSON`、`cannot encode <n> as JSON`、`cannot encode tables nested this deep (or cyclic) as JSON` | `tern.json.encode`、`tern.kv.set`，以及任何发送 Lua 值的地方（视图、`save`、`spawn`） | 函数、userdata、非字符串键、NaN 或无穷大、循环引用，或嵌套超过 128 层 |
| `tern.json.decode: <parser message>` | `tern.json.decode` | JSON 不合法 |
| `tern.base64.decode: <reason>` | `tern.base64.decode` | 不是 base64：``invalid character `<c>` ``（包括与文本开头所用字母表不同的那个字母表的字符）、`invalid byte 0x<hh>`、`misplaced padding`、`truncated input` 或 `nonzero trailing bits` |
| ``tern.secrets.get: bad name `<name>` …``、``tern.secrets.set: bad name `<name>` …`` | `tern.secrets.get`、`set`（其 awaitable 失败） | 名称不匹配 `[a-z0-9][a-z0-9._-]{0,63}` |
| `tern.secrets.set: the value is <n> bytes, more than 65536` | `tern.secrets.set`（其 awaitable 失败） | 值超过 64 KiB |
| `tern.secrets.get: <store error>`、`tern.secrets.set: <store error>` | `tern.secrets.get`、`set`（其 awaitable 失败） | 系统钥匙串不可用或已锁定，且用户拒绝解锁 |
| `tern.kv.set: <io error>` | `tern.kv.set` | `kv.json` 无法写入 |
| `tern.fs.<verb> <path>: <io error>` | `tern.fs.read`、`write`、`list`、`mkdir`、`remove` | 操作失败 |
| `tern.process.run: argv is empty` | `tern.process.run` | |
| `tern.process.run <program>: <io error>` | `tern.process.run` | 程序无法启动（未找到、不可执行） |
| `tern.process.run(argv, opts?, cb): bad arguments` | `tern.process.run` | `argv` 之后的参数既不是 `cb`，也不是 `opts, cb` |
| `tern.process is not available on iOS` | `tern.process.run` | iOS 禁止启动进程；请按 `tern.runtime.os` 分支处理 |
| `tern.fetch(url, opts?, cb): bad arguments` | `tern.fetch` | 参数不是 `(url, cb)`、`(url, opts, cb)` 或 `(url, nil, cb)` |
| `tern.fetch <url>: not an absolute http or https URL` | `tern.fetch` | 其他协议、相对 URL，或没有 host |
| `tern.fetch <url>: <reason>` | `tern.fetch` | URL、方法、某个头名称或头值格式不正确；`<reason>` 来自 HTTP 库（`invalid uri character`、`invalid HTTP method`、`invalid HTTP header name`、`failed to parse header value`）。网络失败从不抛出；它们出现在 `result.error` 中 |
| `tern.ui.<builder>: <argument>: <problem>` | `tern.ui.*` | 参见[参数转换](ui.md#argument-conversion) |
| `tern.parse.<f>: lines…: expected …` | `tern.parse.*` | 参见[解析器](ui.md#parsers) |
| `cx:frame: ops must be a list` | block 的 `cx:frame` | |
| `no program runs in that pane` | window 的 `cx:run` | 该面板中没有正在运行的程序 |
| ``unknown command `<id>` `` | window 的 `cx:command` | 不是内置命令 id |
| ``unknown toast level `<level>` (success, info or error)`` | window 的 `cx:toast` | host 的 `cx:toast` 则接受任意级别 |
| ``unknown how `<how>` `` | window 的 `cx:open`、`cx:new_block` | |
| ``unknown direction `<dir>` (right, down, left or up)`` | `cx.layout` 的各方法 | |
| `tern.chrome.refresh: not from a formatter` | `tern.chrome.refresh` | 在 chrome 格式化器运行期间调用；应从定时器、事件或命令中调用 |
| ``tern.chrome.program_icon: unknown icon `<name>` `` | `tern.chrome.program_icon` | 没有 Tern 图标使用该名称；参见[图标名称](../elements/data.md#icon-names) |
| `tern.chrome.program_icon: empty program` | `tern.chrome.program_icon` | 程序名为空 |

## 无法启动的 block {#blocks-that-cannot-start}

| 消息 | 原因 | 修复 |
| --- | --- | --- |
| toast “Could not start the block” / `no block type <kind> on this host` | block 面板所在的 host 上没有定义其类型的 Ready 插件：会话守护进程（或没有守护进程时的窗口）被要求启动它。面板显示同一张“Could not start the block”卡片，并带 **Retry** 按钮 | 在运行该面板的 host 上安装或启用该插件；检查其状态 |
| toast “Could not open the block” / `No plugin on <host> defines block type <kind>` | `tern.route.open` 或 `tern.route.link` 的决策指定了某种类型，而文件（或链接面板）所在 host 上没有任何 Ready 插件定义它；结果什么都没有打开 | 在该 host 上安装该插件，或只对具备它的 host 返回该决策（`req.host`） |
| 面板中打印 `no block type <kind> on this host`，退出状态 1 | 重载之后，该 block 的插件或类型已不存在 | 恢复该插件，然后再次启动该 block |
| ``could not start block `<kind>` ``, `cx.layout:tab` 返回的第二个值（不抛出、不弹 toast） | 工作区的某个叶子节点指定了 host 上没有任何 Ready 插件定义的类型。若是第一个叶子节点：不打开任何标签页（id 为 `nil`）。若是之后的某个：它及其子树被略去，其余部分照常构建并命名。多个则以逗号分隔 | 在该 host 上安装该插件，或修正该类型 |

block 类型存在于运行该面板的 host 上：远程 host 需要在那里安装插件。iOS 不运行 host 半区，因此插件 block 只在 iOS 设备所连接的 host 上运行。

## 仅写入日志的消息 {#log-only-messages}

以下消息以 warn 级别写入日志，从不弹出 toast：

| 消息 | 含义 |
| --- | --- |
| `plugin spawn filter took over 50 ms; skipped` | 插件的 `spawn` 答复来得太晚，已被丢弃 |
| `plugin keeps re-rendering; requests dropped` | 经过 8 轮之后 `cx` 请求仍在排队（某个 `view` 调用了 `cx:render`） |
| `plugin hook exceeded its budget; paused` | 一次预算触发（同样会弹一次 toast），附带 `paused_ms` |
| `plugin hook resumed after its pause` | 触发过的钩子其暂停已结束 |
| `plugin style sheet has errors` | `styles` 中或 `tern.css` 里的 CSS 未能干净地解析；有效规则仍然生效 |
| `plugin worker didn't retire in time` | 一次重载为旧工作线程等待了 3 s |
| `cannot create the plugin data directory` | `<state>/plugin-data/<id>` 无法创建；`tern.kv` 的写入将失败 |
| `cannot hand a process result to Lua` | 已结束进程的输出无法转成 Lua 表 |

## 命令行 {#command-line}

`tern plugin` 把错误以 `tern plugin: <message>` 的形式打印到标准错误。用法错误以退出码 2 退出并打印用法；其余以退出码 1 退出，若守护进程未及时应答则为 124。

| 消息 | 子命令 | 原因 |
| --- | --- | --- |
| `plugin takes other arguments` | 任意 | 缺少子命令、未知子命令，或词数不对 |
| `unknown flag --<name>` | 任意 | |
| `--window takes a value` | 任意 | |
| `no daemon running` | `reload` | 启动 Tern，或改用 `list` |
| `the session daemon did not answer` | `reload` | 60 s 后以退出码 124 退出；某个 host 入口可能加载缓慢 |
| `no config directory for plugins` | `dir`、`install`、`remove`、`link`、`unlink` | 该机器没有配置目录 |
| `<id> is already installed (<dir>); --force replaces it` | `install` | |
| `<id> is linked (<dir>); use unlink first` | `install` | 无论是否带 `--force` |
| `<id> is already installed (<dir>)` | `link` | 已安装的副本占用了该 id |
| `<id> is linked; use unlink` | `remove` | |
| `<id> is installed, not linked; use remove` | `unlink` | |
| `no plugin <id> in <dir>` | `remove`、`unlink` | |
| `no plugin id <id>` | `remove`、`unlink` | 为空、以 `.` 开头，或含有路径分隔符 |
| `no directory <path>: <io error>`、`<path> is not a directory` | `install`、`link` | |
| `<dir> is not a plugin: <why>` | `install`、`link` | `no plugin.toml`，或加载器报告的任一[文件夹问题](#plugins-folder-problems)（`missing entry <path>`、`cannot read style <path>: <io error>` 等） |
| `<dir> is not UTF-8` | `link` | |
| `installing from git needs git` | `install` | |
| `git clone <url> failed: <git's message>` | `install` | |

更改成功之后，以下内容可能随后出现在输出中（带 `--json` 时为标准错误），但不改变退出码：`no daemon running; changes apply at next start`、`the daemon did not reload its plugins: <error>`，以及 Failed 插件与问题的 `list` 行。参见[命令行](cli.md)。

## 相关页面 {#related-pages}

- [调试](../guides/debugging.md)：如何阅读日志并复现失败。
- [运行时、预算与 JIT](../concepts/runtime.md#failures-and-toasts)。
- [限制](limits.md)。
