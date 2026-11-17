# 共享 API {#shared-api}

这些成员在 host 与 window 两个上下文中都存在，且行为一致；若某处说明涉及哪个上下文的机器、线程或 `cx`，则以该说明为准。视图构建器（`tern.ui`）与解析器（`tern.parse`）同样共享，另有独立页面：[UI 构建器](ui.md)。

## 身份 {#identity}

### `tern.context` 上下文 {#tern-context}

```lua
tern.context: "host" | "window"
```

此 VM 运行在哪个半区：`host` 入口为 `"host"`，`window` 入口为 `"window"`。可在两个入口都会 `require` 的模块中使用。

### `tern.plugin` 插件信息 {#tern-plugin}

```lua
tern.plugin: PluginInfo

type PluginInfo = {
	id: string,
	name: string,
	dir: string,
	data: string,
}
```

| 字段 | 值 |
| --- | --- |
| `id` | 清单的 `id` |
| `name` | 清单的 `name` |
| `dir` | 包目录的绝对路径（链接安装的包即其链接目标） |
| `data` | 插件数据目录的绝对路径，即 `<state>/plugin-data/<id>`，在入口运行前创建 |

数据目录归插件所有；`tern.kv` 把 `kv.json` 保存在其中，用 `tern.process.run` 启动的进程会把它视为 `TERN_PLUGIN_DATA`。

### `tern.runtime` 运行时信息 {#tern-runtime}

```lua
tern.runtime: RuntimeInfo

type RuntimeInfo = {
	os: string,
	jit: boolean,
}
```

| 字段 | 值 |
| --- | --- |
| `os` | `"macos"`、`"linux"`、`"windows"` 或 `"ios"` |
| `jit` | 此 VM 启用 Luau 原生代码生成时为 `true`；在 iOS 与开发版本中始终为 `false` |

参见[运行时、预算与 JIT](../concepts/runtime.md#jit)。

## 日志 {#logging}

### `tern.log` 日志 {#tern-log}

```lua
tern.log.debug: (...any) -> ()
tern.log.info: (...any) -> ()
tern.log.warn: (...any) -> ()
tern.log.error: (...any) -> ()
```

按给定级别向 Tern 的日志写入一条记录，目标为 `tern::plugin`，字段 `plugin` 设为插件 id。参数用 `tostring` 转换并以制表符连接，与 `print` 相同。全局 `print` 即 `tern.log.info`。

```lua
tern.log.warn("cache miss", key, #entries)
```

不返回任何值，也不会抛出异常。Tern 的默认日志过滤器是 `warn,stencil=info`，因此只保留 `tern::plugin` 的 `warn` 与 `error` 记录；设置 `STENCIL_LOG=warn,stencil=info,tern::plugin=debug` 可保留 `info`（含 `print`）与 `debug`。日志所在位置参见[调试](../guides/debugging.md)。

## JSON 转换 {#json}

同一套转换也承载视图树、block 状态、`kv` 值与事件，因此凡是将 Lua 值变为 JSON 之处，这些规则都适用。

| Lua | JSON |
| --- | --- |
| `nil`、`tern.json.null` | `null` |
| 布尔值 | 布尔值 |
| 整数，或 ±2^53 范围内无小数部分的浮点数 | 整数 |
| 其他有限浮点数 | 数值 |
| 字符串 | 字符串（非法 UTF-8 会被替换） |
| 键恰为 `1..n`、`n > 0` 的表 | 数组 |
| 由 `tern.json.array` 标记、或由 `[]` 解码得到的空表 | `[]` |
| 未标记的空表 | `{}` |
| 其他任何表 | 对象，键会排序；数字键转为对应文本 |

函数、`tern.json.null` 之外的 userdata、线程、NaN 与无穷大无法编码；嵌套超过 128 层表（循环引用即会达到该深度）会被拒绝。

### `tern.json.encode` 编码 {#tern-json-encode}

```lua
tern.json.encode: (value: any, pretty: boolean?) -> string
```

| 参数 | 类型 | 含义 |
| --- | --- | --- |
| `value` | `any` | 要编码的值 |
| `pretty` | `boolean?` | 是否缩进输出（默认 `false`） |

返回 JSON 文本。

会抛出 `cannot encode a <type> as JSON`、`cannot encode a <type> key as JSON`、`cannot encode <n> as JSON`（非有限数值）或 `cannot encode tables nested this deep (or cyclic) as JSON`。

### `tern.json.decode` 解码 {#tern-json-decode}

```lua
tern.json.decode: (text: string) -> any
```

解码 `text`。数组返回为带数组标记的表（因此即使为空也会重新编码为数组）；数组内的 `null` 变为 `tern.json.null`；值为 `null` 的对象成员会被丢弃。整数仍为整数。

JSON 非法时会抛出 `tern.json.decode: <parser message>`。

```lua
local cfg = tern.json.decode(tern.fs.read("config.json"))
local port = cfg.port or 8080
```

### `tern.json.array` 数组标记 {#tern-json-array}

```lua
tern.json.array: (<T>(t: T) -> T) & (() -> { any })
```

把 `t`（或新建的空表）标记为 JSON 数组并返回，因此空表会编码为 `[]` 而不是 `{}`。键为 `1..n` 的非空表无论是否带标记都会编码为数组。

```lua
tern.json.encode({ items = tern.json.array() })  --> {"items":[]}
```

### `tern.json.null` null 值 {#tern-json-null}

```lua
tern.json.null: JsonNull
```

在 Lua `nil` 无法表达之处（数组项、对象中的显式 null）代表 JSON `null` 的值。

## Base64 编解码 {#base64}

### `tern.base64` 编解码 {#tern-base64}

```lua
tern.base64.encode: (bytes: string, opts: { url: boolean? }?) -> string
tern.base64.decode: (text: string) -> string
```

在二进制字符串与 base64 文本之间相互转换，用于 HTTP API、令牌与文件。两个半区以及 Carly 的 VM 都具备该功能。

| 函数 | 行为 |
| --- | --- |
| `encode(bytes)` | 标准字母表（`+`、`/`），带 `=` 填充 |
| `encode(bytes, { url = true })` | URL 安全字母表（`-`、`_`），无填充，JWT 与 Gmail 的 `raw` 即如此 |
| `decode(text)` | `text` 用任一字母表编码出的字节（同一文本中不会混用两种），填充可选；ASCII 空白（MIME 正文的换行）会被忽略 |

除上述情况外，`decode` 会抛出 `tern.base64.decode: <reason>`：``invalid character `<c>` ``, `invalid byte 0x<hh>`, `misplaced padding`,
`truncated input` 或 `nonzero trailing bits`。

```lua
local auth = "Basic " .. tern.base64.encode(user .. ":" .. password)
local body = tern.base64.decode(part.body.data) -- URL-safe, unpadded
```

## 时间与环境 {#time-and-environment}

### `tern.now` 当前时间 {#tern-now}

```lua
tern.now: () -> number
```

单调时钟上的毫秒数，带小数部分。其原点是进程中的第一次调用，因此只有差值有意义。

### `tern.getenv` 读取环境变量 {#tern-getenv}

```lua
tern.getenv: (name: string) -> string?
```

此上下文所在进程中环境变量 `name` 的值；未设置或不是合法 Unicode 时为 `nil`。host 上下文读取会话守护进程的环境（没有守护进程运行时读取窗口的环境）；window 上下文读取 Tern 应用的环境。

### `tern.timer` 定时器 {#tern-timer}

```lua
tern.timer: (ms: number, fn: (cx: WindowCx?) -> ()) -> TimerHandle

declare extern type TimerHandle with
	function cancel(self): ()
end
```

| 参数 | 类型 | 含义 |
| --- | --- | --- |
| `ms` | `number` | 延迟的毫秒数；负值按 0 处理 |
| `fn` | function | 延迟结束后调用一次 |

返回一个句柄；`handle:cancel()` 会移除定时器，而在定时器已触发或 VM 已销毁后调用则什么也不做。

回调在拥有该 VM 的线程上运行，作为 hook `timer`，在上下文的常规预算下执行，绝不会与同一插件、同一上下文的另一个处理程序并发。在 window 上下文中它会收到一个新的窗口 `cx`；在 host 上下文中不接收任何参数。host 定时器出错时，会在每个窗口弹出 toast 提示。

若在 VM 被销毁后调用（例如来自存活超过一次重载的回调），会抛出 `the plugin is gone`。

```lua
local function tick(cx)
	cx:toast("info", "Still here")
	tern.timer(60000, tick)
end
tern.timer(60000, tick)
```

定时器不会重复触发；需在回调中重新调度。重载会随 VM 一起丢弃所有待触发的定时器。

### Awaitable 与 `tern.sleep` {#awaitables-and-ternsleep}

```lua
type Awaitable<T> = {
	kind: string,
	id: number,
	next: (self: Awaitable<T>, fn: (result: T?, err: string?, cx: WindowCx?) -> ()) -> (),
}
tern.sleep: (ms: number) -> Awaitable<nil>
```

awaitable 持有异步操作在 VM 本地的标识与结果。`a:next(fn)` 以 hook `await` 把 `fn(result, err, cx?)` 排入 VM 所属线程，按常规回调预算执行。成功时 `err` 为 nil；失败时 `result` 为 nil，`err` 为字符串。window 回调会收到一个新的 `cx`。完成之后注册的回调仍会入队，绝不会内联调用。多个回调可以观察同一结果。

`tern.sleep(ms)` 在有限且非负的毫秒数之后以 nil 完成。所有者把它与普通定时器一同调度；它不会阻塞 VM。

```lua
tern.sleep(100):next(function(_, err, cx)
	if err then error(err) end
	cx:toast("info", "Finished waiting")
end)
```

Carly 的 `lua` 调用使用 `await(a)` 而非回调。她的 VM 会捕获 `print`，内存上限为 64 MiB，并暴露 `loadstring`。`require("name")` 加载已保存的片段；若要使用任意路径的源码，请改用 `tern.fs.read` 与 `loadstring`。她的环境、文件系统、进程与网络 API 具备普通 window 插件的能力，异步回调中同样如此。相对文件系统路径按她 VM 的工作目录解析；插件注册类 API 仍然不可用。常规的参数校验、操作失败、截止时间与资源预算依然适用。普通插件的全局变量与预算保持不变。

## 存储 {#storage}

### `tern.kv` 键值存储 {#tern-kv}

```lua
tern.kv.get: (key: string) -> any
tern.kv.set: (key: string, value: any) -> ()
```

`<data>/kv.json` 中 JSON 值的持久化映射。它就是普通文件：window 半区把凭据保存在 [`tern.secrets`](api-window.md#ternsecrets) 中。

| 函数 | 行为 |
| --- | --- |
| `get(key)` | `key` 下保存的值，从 JSON 转换而来；没有则为 `nil` |
| `set(key, value)` | 保存 `value`；`nil`（或 `tern.json.null`）会删除该键。整个文件以原子方式重写（临时文件加重命名），并做美化输出 |

存储不存在时视为空映射。存储无法读取或包含非法 JSON 时，`get` 与 `set` 都会抛出异常；这类失败不会静默返回 `nil`，也不会覆盖原有内容。最后一次成功加载的缓存会保留，但不会作为成功结果返回：下一次调用会重新尝试加载。`set` 还会抛出 [JSON](#json) 一节列出的转换错误，以及在文件无法写入时抛出 `tern.kv.set: <io error>`。

两个半区以及每个窗口的 window 半区共享同一个文件。每个 VM 在内存中保留该映射，并在 `kv.json` 的修改时间或长度发生变化时重新读取，因此 `get` 能看到其他 VM 的写入，`set` 修改的是当前映射，而不是写回过期副本。两个 VM 同时调用 `set` 会竞争；最后一次重命名生效。

```lua
local runs = (tern.kv.get("runs") or 0) + 1
tern.kv.set("runs", runs)
```

### `tern.fs` 文件系统 {#tern-fs}

```lua
tern.fs.read: (path: string, max_bytes: number?) -> string
tern.fs.write: (path: string, text: string) -> ()
tern.fs.list: (path: string) -> { string }
tern.fs.exists: (path: string) -> boolean
tern.fs.mkdir: (path: string) -> ()
tern.fs.remove: (path: string) -> ()
```

在此上下文所在机器上的同步文件访问。相对路径按插件目录（`tern.plugin.dir`）解析，而不是按某个面板的工作目录；`~` 不会展开。

| 函数 | 行为 | 抛出 |
| --- | --- | --- |
| `read(path, max_bytes?)` | 原始字节（不校验 UTF-8）；可选的字节上限必须为非负整数，且要求是常规、非符号链接文件 | `tern.fs.read <path>: <error>` |
| `write(path, text)` | 创建或截断文件并写入 `text`；父目录必须已存在 | `tern.fs.write <path>: <error>` |
| `list(path)` | 目录中的条目名称，已排序，以数组返回 | `tern.fs.list <path>: <error>` |
| `exists(path)` | 路径是否存在（跟随符号链接） | 从不抛出 |
| `mkdir(path)` | 创建目录及缺失的父目录；目录已存在也可以 | `tern.fs.mkdir <path>: <error>` |
| `remove(path)` | 删除文件或符号链接，或连同其中全部内容删除目录 | `tern.fs.remove <path>: <error>` |

错误信息中的路径为解析后的绝对路径。

对不受信任的小文件请使用 `tern.fs.read(path, 64 * 1024)`。设置上限后，目录、FIFO、设备以及末级路径的符号链接/重解析点都会被拒绝。校验的是已打开的句柄，而不只是先前的一次路径 stat：替换竞争无法把读取重定向到会阻塞的 FIFO 或设备。超出大小的文件会在分配或读取其内容之前被拒绝；校验之后发生的增长通过最多缓冲 `max_bytes` 字节加一次一字节探测来发现。Unix 与 Windows 上均有此实现。祖先目录中的符号链接仍会正常解析。不设上限时，`read` 保持普通文件系统读取语义，包括跟随符号链接与无上限的内存分配。上限不是墙钟截止时间：慢速磁盘或网络文件系统上的常规文件读取仍可能阻塞。

每次调用都会阻塞上下文的线程。在 window 上下文中，那就是预算为 50 ms 的 UI 线程：请保持读取量小，并把繁重或缓慢的工作交给 `tern.process.run`。

```lua
local notes = tern.plugin.data .. "/notes"
tern.fs.mkdir(notes)
tern.fs.write(notes .. "/today.md", "# Today\n")
```

## 进程 {#processes}

### `tern.process.run` 运行进程 {#tern-process-run}

```lua
tern.process.run: ((argv: { string }, opts: ProcessOptions?, cb: (result: ProcessResult, cx: WindowCx?) -> ()) -> ())
	& ((argv: { string }, cb: (result: ProcessResult, cx: WindowCx?) -> ()) -> ())
	& ((argv: { string }, opts: ProcessOptions?) -> Awaitable<ProcessResult>)

type ProcessOptions = {
	cwd: string?,
	env: { [string]: string }?,
	stdin: string?,
	timeout_ms: number?,
}

type ProcessResult = {
	status: number,
	stdout: string,
	stderr: string,
	timed_out: boolean,
}
```

在此上下文所在的机器上，以 `argv[2..]` 为参数直接启动 `argv[1]`（不经 shell），并立即返回。进程退出且其输出读取完毕后，`cb` 作为 hook `process` 在该 VM 的线程上运行。

不传 `cb` 时，`run(argv, opts?)` 返回 `Awaitable<ProcessResult>`。在插件中用 `:next(function(result, err, cx) ... end)`，在 Carly 的 `lua` 工具中用 `await(tern.process.run(argv, opts))`。启动失败仍在调用处抛出；进程本身的失败由结果的 status 表示，而不是 await 错误。

| 参数 | 类型 | 含义 |
| --- | --- | --- |
| `argv` | `{ string }` | 程序与参数；程序会在 `PATH` 中查找 |
| `opts` | `ProcessOptions?` | 可整体省略：`run(argv, cb)` |
| `cb` | function | 接收结果；在 window 上下文中还会收到一个新的窗口 `cx` |

| 选项 | 默认值 | 含义 |
| --- | --- | --- |
| `cwd` | 插件目录 | 工作目录；相对路径按插件目录解析 |
| `env` | 无 | 追加到继承环境中的变量 |
| `stdin` | 空 | 写入 stdin 的字节，随后关闭 stdin |
| `timeout_ms` | 无 | 经过该毫秒数后终止进程（小于等于 0 的值表示不限制） |

| 结果字段 | 含义 |
| --- | --- |
| `status` | 退出码；因超时被终止或因信号结束时为 `-1` |
| `stdout` | 捕获的标准输出，最多 16 MiB（其余内容会被读取并丢弃） |
| `stderr` | 捕获的标准错误，最多 16 MiB |
| `timed_out` | `timeout_ms` 已到且进程被终止时为 `true` |

每个进程还会获得 `TERN_PLUGIN_DATA`，其值为 `tern.plugin.data`。在 window 上下文中，它还会获得 `TERN_WINDOW_KEY`，其值为该窗口的 key（[`cx:window_key()`](api-window.md#window-cx)），因此它运行的 `tern …` 命令会作用于该窗口的会话；`opts.env` 可以覆盖两者中的任一个。

在调用处抛出：

- 参数不是 `(argv, cb)`、`(argv, opts, cb)` 或 `(argv, nil, cb)` 时，抛出 `tern.process.run(argv, opts?, cb): bad arguments`；
- `tern.process.run: argv is empty`；
- 程序无法启动（找不到、不可执行、`cwd` 无效）时，抛出 `tern.process.run <program>: <error>`；
- 在 iOS 上，无论何种情况都抛出 `tern.process is not available on iOS`。

非零退出不是错误：请检查 `status`。VM 被销毁（例如重载）时，待处理的回调会被丢弃；进程本身会继续运行到结束。host 回调出错时，会在每个窗口弹出 toast 提示。

```lua
local repo = (tern.getenv("HOME") or "") .. "/src/project"
tern.process.run({ "git", "rev-parse", "--abbrev-ref", "HEAD" }, { cwd = repo, timeout_ms = 2000 }, function(r, cx)
	if r.status == 0 then
		cx:toast("info", "On branch " .. r.stdout:gsub("%s+$", ""))
	end
end)
```

（此示例为 window 入口；在 host 入口中 `cx` 为 `nil`。）

## 网络 {#network}

### `tern.fetch` 发起请求 {#tern-fetch}

```lua
tern.fetch: ((url: string, opts: FetchOptions?, cb: (result: FetchResult, cx: WindowCx?) -> ()) -> ())
	& ((url: string, cb: (result: FetchResult, cx: WindowCx?) -> ()) -> ())
	& ((url: string, opts: FetchOptions?) -> Awaitable<FetchResult>)

type FetchOptions = {
	method: string?,
	headers: { [string]: string }?,
	body: string?,
	timeout_ms: number?,
}

type FetchResult = {
	status: number,
	headers: { [string]: string },
	body: string,
	error: string?,
	timed_out: boolean,
}
```

从此上下文所在的机器上，在自己的线程中发送一个 HTTP/1.1 请求，并立即返回（带回调时不返回内容，不带回调时返回 awaitable）。在 host 上下文中，即会话守护进程所在的机器，因此远程 host 的插件从该 host 发起请求；在 window 上下文中，即显示该窗口的机器。整个响应读取完毕或请求失败后，`cb` 作为 hook `fetch` 在该 VM 的线程上运行。与 `tern.process.run` 不同，它在 iOS 上可用。

不传 `cb` 时，`fetch(url, opts?)` 返回 `Awaitable<FetchResult>`。网络错误仍会设置 `result.error`；参数非法仍在调用处抛出。带回调的形式保留原有签名与 hook。

| 参数 | 类型 | 含义 |
| --- | --- | --- |
| `url` | `string` | 绝对 `http://` 或 `https://` URL，且已做百分号编码（不会代为编码任何内容） |
| `opts` | `FetchOptions?` | 可整体省略：`fetch(url, cb)` |
| `cb` | function | 接收结果；在 window 上下文中还会收到一个新的窗口 `cx` |

| 选项 | 默认值 | 含义 |
| --- | --- | --- |
| `method` | `"GET"` | 任意 HTTP 方法 token，不区分大小写（发送时转为大写），因此 `"propfind"` 也可用 |
| `headers` | 无 | 请求头，名称 → 值；除非在此设置，`User-Agent` 为 `Tern` |
| `body` | 无 | 请求体字节，随 `Content-Length` 发送。不设 `body` 则不发送请求体；`""` 发送空请求体 |
| `timeout_ms` | `30000` | 整个交换过程（连接、TLS、发送、响应头与响应体、每一次重定向）必须在此时间内完成，否则请求以 `timed_out = true` 失败。小于等于 0 的值表示使用默认值；`math.huge` 表示不设实际限制 |

| 结果字段 | 含义 |
| --- | --- |
| `status` | HTTP 状态码。任何状态码都是响应：404 或 500 不算错误。设置 `error` 时为 `0` |
| `headers` | 按小写名称索引的响应头；同名头出现多次时其值以 `", "` 连接。设置 `error` 时为空 |
| `body` | 响应体字节（不校验 UTF-8），最多 16 MiB。设置 `error` 时为 `""` |
| `error` | 完整收到响应时为 `nil`；否则说明原因（无此主机、连接被拒绝、TLS 失败、超时、重定向过多、响应体超过 16 MiB 等） |
| `timed_out` | `timeout_ms`（或默认的 30 s）结束了请求时为 `true` |

`error` 文本来自 HTTP 客户端（例如 `timeout: global`、`too many redirects`、`io: Connection refused (os error 61)`）；直接展示即可，不要解析。

在调用处抛出（网络失败从不抛出，而是出现在 `result.error` 中）：

- 参数不是 `(url, cb)`、`(url, opts, cb)` 或 `(url, nil, cb)` 时，抛出 `tern.fetch(url, opts?, cb): bad arguments`；
- 使用其他协议、相对 URL 或没有主机时，抛出 `tern.fetch <url>: not an absolute http or https URL`；
- URL、方法、某个头名称或头值格式非法时，抛出 `tern.fetch <url>: <reason>`；`<reason>` 来自 HTTP 库（例如 `invalid uri character`、`invalid HTTP method`、`invalid HTTP header name`、`failed to parse header value`）。

重定向会被跟随，最多 10 次（更多则失败并设置 `error`）。重定向之后不会再次发送 `Authorization` 头。带请求体的请求遇到 307 或 308 重定向时会失败并设置 `error`，而不是重发请求体。

HTTPS 证书按操作系统的信任库校验。上下文进程的代理变量（`ALL_PROXY`、`HTTPS_PROXY`、`HTTP_PROXY`、`NO_PROXY`，大小写均可）会被采用。不请求压缩，请求之间也不保留 cookie。连接会保持存活，并在同一 VM 的各请求之间复用。并发请求数量没有上限。

VM 被销毁（例如重载）时，待处理的回调会被丢弃；请求本身会运行到结束。host 回调出错时，会在每个窗口弹出 toast 提示。

```lua
tern.fetch("https://api.github.com/repos/neovim/neovim/releases/latest", {
	headers = { Accept = "application/vnd.github+json" },
	timeout_ms = 10000,
}, function(r, cx)
	if r.error then
		tern.log.warn("release check failed", r.error)
	elseif r.status == 200 then
		cx:toast("info", "Neovim " .. tern.json.decode(r.body).tag_name)
	end
end)
```

（此示例为 window 入口；在 host 入口中 `cx` 为 `nil`。）

```lua
tern.fetch("https://hooks.example.com/build", {
	method = "POST",
	headers = { ["Content-Type"] = "application/json" },
	body = tern.json.encode({ status = "done" }),
}, function(r)
	if r.error or r.status >= 300 then
		tern.log.warn("webhook failed", r.error or r.status)
	end
end)
```

## 相关页面 {#related-pages}

- [UI 构建器](ui.md)：`tern.ui` 与 `tern.parse`。
- [文件、进程与存储](../guides/io.md)：基于这些成员构建的模式，包括 `tern.fetch`。
- [限制](limits.md)：此处提到的每一处上限。
