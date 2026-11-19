# 限制 {#limits}

插件运行时施加的每一项固定上限、超时与默认值，连同其取值以及到达边界时的行为。
这些值都不可配置。概念页面解释每一项为何存在；本页是速查表。

## 包与清单 {#packages-and-manifests}

| 限制 | 取值 | 到达限制时 |
| --- | --- | --- |
| `plugin.toml` 大小 | 64 KiB | 报错 `plugin.toml is larger than 64 KiB` |
| 清单 schema | `1` | 报错 `unsupported schema N` |
| 插件、block 与 lens 的 id | `^[a-z][a-z0-9-]{0,31}$`（1–32 字节） | 报错 `invalid id …`、`invalid block id …`、`invalid lens id …` |
| 插件 `name` | 1–64 个 Unicode 字符 | 报错 `name must be 1-64 characters` |
| lens 的 `match` 模式 | 每个 lens 至少 1 个 | 报错 `lens "x" needs at least one match pattern` |
| `styles` 总大小 | 拼接之后为 256 KiB | 报错 `styles are larger than 256 KiB` |
| 每个 host 的插件数 | 64 个有效包，按 id 计 | 第 64 个之后的每个插件都报错 `too many plugins` |
| `tern.command` 的 id、`tern.css` 的名称 | ASCII 字母、数字、`_`、`-`；非空；不是 `bind` / `styles` | 在调用处抛出 |
| 默认图标 | `puzzle` | 用于未知或缺失的图标 |

参见[清单参考](manifest.md)。

## VM 与预算 {#vms-and-budgets}

| 限制 | 取值 | 到达限制时 |
| --- | --- | --- |
| 每个 VM 的内存 | 256 MiB | 执行分配的调用抛出 Luau 内存错误 |
| host 调用预算 | 每次调用 2 s 的 Lua 时间，包含运行 `host.luau` | 抛出 `tern: <hook> exceeded 2000 ms`；该钩子在该 VM 中暂停 |
| window 调用预算 | 每次调用 50 ms 的 Lua 时间，包含运行 `window.luau` | 抛出 `tern: <hook> exceeded 50 ms`；钩子暂停 |
| chrome 格式化器与 `available` | 每次调用 4 ms 的 Lua 时间 | 抛出 `tern: <hook> exceeded 4 ms`；钩子暂停 |
| 每次调用的墙钟时间，含原生调用 | 10 倍预算（20 s、500 ms、40 ms） | 抛出 `tern: <hook> exceeded <n> ms, native calls included`；钩子暂停 |
| 嵌套调用 | 若外层调用的截止时间更早，则以它为准 | |
| 暂停的钩子 | 首次触发后 5 s；在上次暂停结束后 10 min 内再次触发则翻倍，最多 5 min；10 min 内没有触发则回到 5 s。重载会结束暂停 | 调用被跳过：`tern: <hook> is paused for <n> s after exceeding its budget`，以 debug 级别记录；到期的定时器、进程、fetch 与 await 回调在暂停结束时运行 |

Lua 时间不包含原生调用（Tern 的 API、`tern.fs`、`tern.kv`、启动进程、编译模块、
耗时较长的内建函数），也不包含等待 CPU 的时间。预算在 Luau 的中断点检查
（函数调用、返回与循环迭代）：一次原生调用会在检查之前完成，而永不返回的调用
（对 FIFO 做无界的 `tern.fs.read`）会挂住它的线程。参见
[运行时、预算与 JIT](../concepts/runtime.md#budgets)。

## Host worker {#host-workers}

| 限制 | 取值 | 到达限制时 |
| --- | --- | --- |
| `spawn` 过滤器等待 | 每个插件 50 ms | 该插件的应答被丢弃；记录 `plugin spawn filter took over 50 ms; skipped` |
| 重载时让 worker 退役 | 3 s 内释放它的 block | 记录 `plugin worker didn't retire in time`；重载继续进行 |
| 一次调用之后的 `cx` 请求轮次 | 8 | 仍在排队的请求（调用了 `cx:render` 的 `view`）被丢弃；记录 `plugin keeps re-rendering; requests dropped` |
| 每个插件的 lens 捕获状态 | 256 | 先丢弃已完成的捕获，最近最少使用的优先；被丢弃的捕获会在其下一个事件时从 block 的输出重建 |
| host 记住其插件的 lens block | 4096 | 最旧的被遗忘；它们的事件通过重新认领该 block 的命令来路由 |
| `tern plugin reload` 等待 | 60 s | `the session daemon did not answer`，退出码 124 |

## Lens {#lenses}

| 限制 | 取值 | 到达限制时 |
| --- | --- | --- |
| 命令运行期间的视图 tick | 每个 block 每 250 ms 一次 `view`，且仅在有新行之后 | 行会累积到下一个 tick；`finish` 总会触发最后一次 `view` |
| 每条命令捕获的输出 | 16 MiB | 捕获被放弃；输出保持为普通终端文本 |
| 等待其 block 的 lens 视图 | 5 s | 若视图在窗口显示其 lens block 之前到达窗口，则会重试直到该 block 出现，之后在 5 s 后或面板消失时被丢弃 |
| `tern.parse.json_tree` 的节点 | 5000 | 其余部分由一行溢出提示概括 |

Tern 内置的 lens 也在 5000 行处停止，并添加 `tern.ui.overflow(n)`
的那一行；`tern.ui.table` 之类的插件构建器不做截断，因此长视图需要自行限定上限。

## Block {#blocks}

| 限制 | 取值 | 到达限制时 |
| --- | --- | --- |
| 帧消息大小 | 64 KiB | 更大的帧被拆成块，由 Surface 协议重新组装 |
| 来自面板的待处理输入 | 16 MiB | 超过此大小的不完整序列被丢弃 |
| CSI 或 SS3 按键序列 | 64 字节 | 更长的序列被丢弃 |

## Window 半区 {#window-half}

| 限制 | 取值 | 到达限制时 |
| --- | --- | --- |
| chrome 格式化器缓存 | 每个格式化器 256 个输入 | 缓存被清空并重新填充 |
| Lua 中的面板与标签 id | host 自身的 id 低于 2^44；远程 host 的标记高于此值 | id 在 Lua 数字中保持精确 |
| Carly 导出参数与应答 | 1 MiB 编码后的 JSON | 更长的字符串应答被截断，并以 `[… N bytes cut]` 结尾；其他内容则失败 |
| `call:fail` 消息 | 16 KiB | 其余部分被丢弃 |
| `tern.secrets` 的值 | 64 KiB | awaitable 失败 |
| `tern.secrets` 的名称 | `[a-z0-9][a-z0-9._-]{0,63}` | awaitable 失败 |

## 共享 API {#shared-api}

| 限制 | 取值 | 到达限制时 |
| --- | --- | --- |
| `tern.process.run` 输出 | 每个流 16 MiB | 其余部分被读取后丢弃 |
| `tern.process.run` 超时 | 未给出 `timeout_ms` 时无 | 进程被杀死，`timed_out = true`，`status = -1` |
| `tern.fetch` 响应体 | 16 MiB | 请求以 `error` 失败（不做截断） |
| `tern.fetch` 超时 | 未给出 `timeout_ms` 时 30 s | 请求以 `timed_out = true` 失败 |
| `tern.fetch` 重定向 | 10 | 请求以 `error` 失败 |
| `tern.json.encode` 嵌套 | 128 层 | 抛出 `cannot encode tables nested this deep (or cyclic) as JSON` |
| JSON 中的整数 | 精确到 2^53 | 更大的整数值以浮点数编码 |
| iOS 上的 `tern.process` | 不可用 | 抛出 `tern.process is not available on iOS` |

定时器、进程、进行中的请求、`tern.kv` 的键与 `tern.fs` 的读取都没有自身的数量或大小
上限；VM 的内存限制与调用预算约束着它们。

## 监听与重载 {#watching-and-reload}

| 限制 | 取值 | 含义 |
| --- | --- | --- |
| 变更批处理 | 300 ms | 此窗口内的变更只导致一次重载 |
| 回退轮询间隔 | 2 s | 在没有原生监听生效之处（iOS、网络卷、inotify 耗尽） |
| 轮询指纹深度 | 8 个目录层级 | 更深处的变更不会被轮询发现 |
| 轮询指纹大小 | 10,000 个条目 | 超过此数量的条目不会被轮询发现 |

参见[生命周期与重载](../concepts/lifecycle.md#watching)。

## 日志 {#logs}

| 限制 | 取值 | 含义 |
| --- | --- | --- |
| 默认过滤器 | `warn,stencil=info` | 除非 `STENCIL_LOG` 启用 `tern::plugin`，否则 `tern.log.info`、`debug` 与 `print` 被丢弃 |
| 日志文件轮转 | 每个文件 16 MiB，保留两个旧文件 | 适用于插件写入的整个 Tern 日志 |

参见[运行时、预算与 JIT](../concepts/runtime.md#logs)。

## 相关页面 {#related-pages}

- [运行时、预算与 JIT](../concepts/runtime.md)
- [错误](errors.md)：这些限制产生的消息。
