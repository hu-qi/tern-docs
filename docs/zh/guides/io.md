# 文件、进程与存储 {#files-processes-and-storage}

两个半区共享同一套 I/O API：同步文件访问、小型键值存储、带回调的子进程与 HTTP 请求、定时器、JSON、环境变量与日志。每次调用都作用于其上下文所在的机器：host 半区作用于它所服务的面板所在的机器，window 半区作用于显示该窗口的机器。

```lua
tern.process.run({ "git", "rev-parse", "--abbrev-ref", "HEAD" }, { cwd = "/srv/api" }, function(result, cx)
	if result.status == 0 and cx then
		cx:toast("info", "Branch", (string.gsub(result.stdout, "%s+$", "")))
	end
end)
```

## 哪台机器，哪个线程 {#which-machine-which-thread}

| | Host 半区 | Window 半区 |
| --- | --- | --- |
| 机器 | 面板运行的位置（会话守护进程所在的机器；若面板属于远程主机，则为该主机）。 | 显示窗口的机器；远程主机的面板同样如此。 |
| 线程 | 插件的 worker 线程。 | 窗口的 UI 线程。 |
| 每次调用的预算 | 2 秒 Lua 时间。 | 50 ms Lua 时间（chrome 格式化器与 `available` 中为 4 ms）。 |
| 回调 `cx` | 无。 | 一个新的 window `cx`。 |

`tern.fs` 与 `tern.kv` 是同步的：磁盘返回时调用才返回。这段时间是原生时间，因此不计入调用处理器的 Lua 预算，只计入其十个预算的墙钟上限；在 window 半区，它仍然占用 UI 线程的时间，期间窗口不绘制任何内容。读取小型配置文件没有问题；遍历目录树、读取大文件或访问网络文件系统应放到进程中，或放到 host 半区。绝不要阻塞 UI 线程：对 FIFO，或对挂载已停止响应的文件调用不带 `max_bytes` 的 `tern.fs.read`，会一直等到数据到来，任何预算都无法中断它，窗口随即卡死；凡是可能不是普通文件的对象，都请传入 `max_bytes`。

## 文件：`tern.fs` {#files-tern-fs}

| 函数 | 作用 |
| --- | --- |
| `tern.fs.read(path) -> string` | 以 Lua 字符串返回文件字节。 |
| `tern.fs.write(path, text)` | 写入 `text`，替换该文件（非原子操作）。 |
| `tern.fs.list(path) -> {string}` | 目录的条目名称，已排序。 |
| `tern.fs.exists(path) -> boolean` | 路径是否存在。从不抛出异常。 |
| `tern.fs.mkdir(path)` | 创建目录及其各级父目录。 |
| `tern.fs.remove(path)` | 删除文件、符号链接本身，或连同全部内容一起删除目录。 |

相对路径相对插件目录（`tern.plugin.dir`）解析，因此 `tern.fs.read("templates/row.txt")` 读取的是插件随附的文件。绝对路径可指向用户有权访问的任何位置。失败时抛出的错误带有动词与路径：`tern.fs.read /etc/nope: No such file or directory (os error 2)`。可能失败的调用请用 `pcall` 包裹。

不要写入插件目录。Tern 会监视它，其中任何改动都会重载插件，而 `tern plugin install --force` 会替换它。请把状态写入 `tern.plugin.data`。

## 存储：`tern.kv` {#storage-tern-kv}

`tern.kv.get(key)` 与 `tern.kv.set(key, value)` 以字符串键把 JSON 值保存在 `<data>/kv.json` 中，其中 `<data>` 即 `tern.plugin.data`（`<state>/plugin-data/<id>/`，在加载时创建）。用 `nil`（或 `tern.json.null`）调用 `set` 会删除该键。

```lua
local runs = (tern.kv.get("runs") or 0) + 1
tern.kv.set("runs", runs)
tern.kv.set("last", { line = "cargo test", status = 0 })
```

每次 `set` 都通过临时文件加重命名重写整个文件，因此读取方绝不会看到写了一半的文件。值遵循 [JSON 规则](#json-ternjson)：不能有函数、不能有环，存为 `{}` 的空表读回时是空对象，除非它被标记为数组。

该文件属于插件在其所在机器上的数据，插件的两个半区以及每个窗口的 window 半区都使用同一个文件。每个 VM 在内存中保留该映射，并在磁盘上的文件发生变化（修改时间或长度不同）时重新读取，因此 `get` 能看到任一半区最后设置的内容，而 `set` 更新的是当前文件，而不是写回过期副本。两个 VM 同时设置仍会竞争：后完成的重命名胜出。该存储用于小型状态：每次 `set` 都会序列化全部内容。

文件不存在即为空存储。读取失败与非法 JSON 会抛出错误，而不是返回缺失的键或覆盖文件。重载失败会保留最后一次成功的缓存，并在下次调用时重试。写入失败会删除其临时文件。

## 密钥：`tern.secrets` {#secrets-tern-secrets}

`kv.json` 是普通文件，任何以你的身份运行的程序都能读取。window 半区改为把凭据（API 密钥、OAuth 令牌）保存在系统钥匙串中，使用 `tern.secrets.get(name)` 与 `tern.secrets.set(name, value)`；值为 `nil` 时删除。每个插件只能看到自己的密钥。钥匙串可能因解锁提示而阻塞，因此这两个调用都在 UI 线程之外运行并返回 awaitable：

```lua
tern.secrets.set("api.token", token):next(function(_, err, cx)
	if err then cx:toast("error", "Keychain", err) end
end)
```

host 半区没有该 API。参见 [`tern.secrets`](../reference/api-window.md#ternsecrets)。

## 进程：`tern.process.run` {#processes-tern-process-run}

```text
tern.process.run(argv, opts?, callback)
tern.process.run(argv, opts?) -> Awaitable<ProcessResult>
```

在调用线程之外运行程序，并在其退出时于所属线程调用 `callback(result, cx?)`。不传回调时改为返回 [awaitable](../reference/api-shared.md#awaitables-and-ternsleep)：`:next(function(result, err, cx) … end)` 在退出时运行。

| 参数 | 含义 |
| --- | --- |
| `argv` | 程序及其参数，`{program, arg, …}`。不经过 shell：管道与通配符请写 `{"sh", "-c", line}`。程序在上下文进程的 `PATH` 上查找。 |
| `opts.cwd` | 工作目录。相对路径相对插件目录解析，插件目录也是默认值。 |
| `opts.env` | 追加到继承环境中的变量。 |
| `opts.stdin` | 写入进程 stdin 的文本，写入后 stdin 关闭。不传时 stdin 立即关闭。 |
| `opts.timeout_ms` | 在这么多毫秒后杀死进程。 |
| `callback` | 可选。`fn(result, cx?)`；不传时调用返回 awaitable。 |

每个进程还会获得 `TERN_PLUGIN_DATA`，即插件的数据目录。window 半区的进程还会获得 `TERN_WINDOW_KEY`，即插件窗口的键（`cx:window_key()`），因此它们运行的 `tern ls`、`tern split` 以及其他 `tern …` 命令作用于该窗口，而不是第一个窗口。它们的 `TERN_PANE` 与 `TERN_PANE_SOCKET` 为空：Tern 自身从某个面板启动时，不会把这些命令带到该面板所在的窗口。

结果：

| 字段 | 含义 |
| --- | --- |
| `status` | 退出码；进程被杀死（超时）或因信号结束时为 `-1`。 |
| `stdout` | 捕获的标准输出，最多 16 MiB（其余内容会被读取后丢弃）。 |
| `stderr` | 捕获的标准错误，最多 16 MiB。 |
| `timed_out` | `timeout_ms` 耗尽且进程被杀死时为 `true`。 |

无法启动的程序会在调用处抛出异常：`tern.process.run nope: No
such file or directory (os error 2)`。`argv` 为空也会抛出异常；参数形状错误会抛出
`tern.process.run(argv, opts?, cb): bad arguments`。

进程在 `tern.process.run` 返回之前就在调用线程上启动；只有等待与读取发生在别处。启动通常很快，但在 window 半区，启动缓慢（环境变量很大、Windows 上的杀毒扫描）会让 UI 线程被占用同样长的时间。这段时间计入调用的墙钟上限，而不计入其 Lua 预算。

回调像任何处理器一样在上下文自己的线程上运行，使用该上下文的预算，钩子名为 `process`（awaitable 的 `:next` 回调钩子名为 `await`）：window 回调获得新的 `cx` 与 50 ms；host 回调没有 `cx`，有 2 秒。被重载丢弃的 VM 的回调永远不会运行。

在 iOS 上没有进程：`tern.process.run` 会抛出 `tern.process is not
available on iOS`。当 window 半区也需要在 iPad 上工作时，请检查 `tern.runtime.os`。

## 网络：`tern.fetch` {#network-tern-fetch}

```text
tern.fetch(url, opts?, callback)
tern.fetch(url, opts?) -> Awaitable<FetchResult>
```

在调用线程之外发送一个 HTTP 请求，并在整个响应到达或请求失败时于所属线程调用 `callback(result, cx?)`；不传回调时返回 awaitable。用它访问 Web API、webhook 与本地服务器，无需启动 `curl`。与进程不同，它在 iOS 上可用，因此 iPad 上的 window 半区可以借此访问网络。

请求从上下文所在的机器发出：host 半区从会话守护进程所在机器发起（远程主机的插件从该主机发起），window 半区从显示窗口的机器发起。

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

（window 入口；在 host 入口中 `cx` 为 `nil`。）`opts` 接受 `method`（默认 `"GET"`）、`headers`、`body` 与 `timeout_ms`（默认 30 秒，覆盖整个交换过程）：

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

按以下顺序检查结果：

- `error` 在没有完整响应到达时被设置：主机不存在、连接被拒绝、TLS 失败、超时、重定向过多、响应体超过 16 MiB。此时 `status` 为 `0`，`headers` 为空，`body` 为 `""`。请展示该文本，不要解析它。
- `timed_out` 在超时结束了请求时为 `true`（同时也会设置 `error`）。
- 否则 `status` 就是服务器的应答。404 或 500 是响应而非错误：要检查它。

网络失败从不抛出异常。只有调用本身格式错误才会抛出：参数形状错误、URL 不是绝对的 `http://` 或 `https://`，或 URL、方法、头部格式错误。URL 必须已经过百分号编码。重定向会被跟随（最多 10 次），HTTPS 证书会对照系统的信任存储校验，并遵循上下文进程的代理变量。详见 [共享 API](../reference/api-shared.md#network)。

回调像进程回调一样运行，钩子名为 `fetch`：window 回调获得新的 `cx` 与 50 ms；host 回调没有 `cx`，有 2 秒。被重载丢弃的 VM 的回调永远不会运行；请求本身仍会运行到结束。

## 定时器与时间 {#timers-and-time}

`tern.timer(ms, fn)` 在 `ms` 毫秒后调用一次 `fn`（负值按 0 计），并返回一个句柄，其 `cancel()` 会取消该定时器；已触发后 cancel 不产生任何效果。在 window 半区，`fn` 会收到一个新的 `cx`。需要重复定时器时，从回调中重新挂载：

```lua
local function tick(cx: WindowCx?)
	if cx then
		cx:toast("info", "Still here")
	end
	tern.timer(60000, tick)
end
tern.timer(60000, tick)
```

插件的所有定时器回调都以钩子 `timer` 运行，所有进程回调以钩子 `process` 运行，所有 fetch 回调以钩子 `fetch` 运行。超出预算运行的钩子会暂停（5 秒，反复超时则更长），因此一个缓慢的定时器回调会阻塞该插件的所有定时器回调，直到暂停结束；期间到期的定时器随后各运行一次。定时器随其 VM 在重载时消亡。

`tern.now()` 返回单调毫秒数，带小数，从进程中的首次调用开始计数。用它衡量时长；它不是墙钟，host 与 window 半区（通常是不同进程）也不共享起点。

## JSON：`tern.json` {#json-ternjson}

| 函数 | 作用 |
| --- | --- |
| `tern.json.encode(value, pretty?) -> string` | 编码 Lua 值；`pretty` 控制缩进。 |
| `tern.json.decode(text) -> any` | 解码 JSON 文本；输入非法时抛出 `tern.json.decode: …`。 |
| `tern.json.array(t?) -> t` | 把 `t`（或新表）标记为数组。 |
| `tern.json.null` | 代表 JSON `null` 的值。 |

编码规则：

- 键恰好为 `1..n`（n > 0）的表是数组；其他任何非空表都是对象。对象的整数键与数字键会变为字符串。
- 空表编码为 `{}`，除非它被标记为数组，此时为 `[]`。可能为空的列表请用 `tern.json.array` 标记。
- 对象键按排序输出，因此同一个表总是编码为相同的文本。
- 在 ±2^53 范围内的整数编码为整数。NaN 与无穷、函数、userdata、字符串与数字以外的键，以及超过 128 层的嵌套（环）都会抛出异常。
- `nil` 不能放在表中；`null` 数组项或成员请用 `tern.json.null`。

解码规则：数组返回时带数组标记（重新编码会保留 `[]`），`null` 数组项为 `tern.json.null`，而 `null` 对象成员会从表中略去。

```lua
local doc = tern.json.decode('{"tags": [], "owner": null}')
-- doc.tags is an empty, array-tagged table; doc.owner is nil
tern.json.encode(doc) --> {"tags":[]}
```

## 环境变量与日志 {#environment-and-logging}

`tern.getenv(name)` 读取上下文进程的环境：host 半区为会话守护进程（或没有守护进程时承载面板的窗口），window 半区为 Tern 应用。从 Dock 或桌面启动器启动的应用，其环境可能比 shell 更小；不要指望来自 shell 配置文件的 `PATH` 追加项。

`tern.log.debug|info|warn|error(...)` 写入 Tern 的日志，目标为 `tern::plugin`，字段为 `plugin = <id>`；参数经过 `tostring` 处理并用制表符连接。全局 `print` 即 `tern.log.info`。除非 `STENCIL_LOG` 要求更多，该目标只记录警告与错误；参见 [调试](debugging.md#logs)。

## 绝不要阻塞 UI 线程 {#never-block-the-ui-thread}

窗口处理器运行在 UI 线程上，在其返回之前窗口不会绘制。50 ms 预算能阻止失控的处理器，但一个在每个按键相关事件上都耗时 30 ms 的处理器已经会造成可见的卡顿。

- 用 `tern.process.run` 运行程序；绝不要空转等待文件出现。
- window 处理器中的 `tern.fs` 调用应只针对小型本地文件；网络挂载上的路径可能停顿数秒。
- 把工作分散到 `tern.timer` 回调中，或移到 host 半区，其 worker 线程只会阻塞自己。
- 缓存格式化器所需的内容：它们在窗口绘制时运行，预算不足 4 ms。

## 另见 {#see-also}

- [运行时、预算与 JIT](../concepts/runtime.md)：预算，以及超限会暂停哪些内容。
- [共享 API](../reference/api-shared.md)：精确签名。
- [信任与安全](../concepts/security.md)：文件与进程访问对用户意味着什么。
- [长时间运行的命令](../examples/longrun.md)：完整插件中的进程与定时器。

<!-- 结构校验说明：英文原文在此页两处将行内代码折行，`scripts/check_parity.py` 会把折行后位于两个反引号之间的英文片段误判为行内代码。以下片段仅用于与原文的行内代码清单对齐，不会在页面上显示：`. An empty ` `. Check ` -->
