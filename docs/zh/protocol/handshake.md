# 握手 {#handshake}

程序只需一次查询，就能知道自己所在的终端是否使用 TSP，以及它支持哪些能力。

## 检测 {#detection}

写出 `hello` 查询，后接一个 DA1 请求（`ESC [ c`），后者每个终端都会应答：

```text
ESC _ tsp;q;{"q":"hello","v":[1],"app":"omp","ver":"14.2.0","features":["edit","undo","send"]} ESC \  ESC [ c
```

使用 TSP 的终端会在 DA1 应答之前回答该查询，方式与任何终端报告一样落在你的输入上。若 DA1 应答之前没有 `tsp;r`，就意味着不支持 TSP：保留你自己的渲染器。

| 字段 | 含义 |
| --- | --- |
| `v` | 你所使用的协议版本。Tern 只支持 `1`：列表中缺少它的查询完全得不到回复，因此会被读作不支持 TSP。 |
| `app` | 你的程序名称。当你的某个 Surface 处于打开并监听状态时，Tern 会把该程序显示为该面板的程序（其图标出现在标签页与命令面板上），即使窗口是在该命令启动之后才附着也是如此。 |
| `ver` | 你的程序版本。Tern 不使用它。 |
| `features` | 你在 v1 之外还处理的能力（见下）。未知名称会被忽略。 |

每个 `hello` 都会取代上一个 `hello` 声明的信息：之后的 `hello` 若不含 `app` 或 `features`，就会清空它们。你的程序消失后（shell 出现下一个提示符、面板进程退出、终端重置），Tern 会忘记这两者；并且只在你的某个 Surface 打开并监听期间应用它们。

程序特性：

| 特性 | 含义 |
| --- | --- |
| `edit` | 你处理 `edit` 事件，因此 Tern 可以在你的编辑器中保留原生选区（[原生编辑](input.md#native-editing)）。 |
| `undo` | 你处理 `undo` 事件，因此 Tern 可以在其中接管撤销键。 |
| `send` | 你通过输入框的正常提交通路，提交 `send` 事件中提供的文本。这是一种能力，而非就绪状态：目标字段还必须报告 `sendable:true`。 |

快照会先重放 `hello`，因此 `app` 名称与特性在窗口重启后依然保留。

### 在 tmux 内部 {#inside-tmux}

tmux 会由它的面板自行立即应答 DA1，并且默认把每个 APC 体设为该面板的标题，因此上面的探测在那里无法工作。Tern 会绘制运行在 Tern 面板中的普通 tmux 里的 TSP 程序，并在这样做时设置 tmux 会话选项 `@tern-tsp`。在 tmux 内部（已设置 `TMUX`）时：

1. 运行 `tmux show-options -qv @tern-tsp`。没有输出，或执行失败，意味着没有 TSP：Tern 并未绘制该会话。
2. 在你的第一个 TSP 字节之前运行 `tmux set-option -p -t "$TMUX_PANE" allow-set-title off`。
3. 发送不带 `ESC [ c` 的 `hello`，并最多等待一秒的回复；没有回复即表示不支持 TSP。
4. 每当你停止使用 TSP（退出时，或未收到回复时），把标题还给该面板：`tmux set-option -pu -t "$TMUX_PANE" allow-set-title`。

## 回复 {#reply}

```json
{"r":"hello","v":1,"term":"tern","ver":"0.4.3",
 "kinds":["col","row","card","section","rule","spacer","text","md","code","diff","ansi","math",
  "image","media","kv","stats","table","tree","json","badge","kbd","icon","spinner","shimmer","elapsed","progress",
  "rate","list","item","tabs","editor","input","button","status","seg","overlay","toast","rows","picker","prefs",
  "tool","checklist","agent","chart","meter","block","effort","select","switch","slider","field","otp",
  "buttons","avatar","avatars","breadcrumb","pager","empty","skeleton","calendar","date","menu","menubar",
  "nav","split","scroll","carousel","message","attachment","trace","stacktrace","suggestions","questions","el"],
 "features":["blobs","settle","adopt","dock","reduce-motion","aside","scroll","styles","flow","font"],
 "apc":65536,"credits":2,
 "cols":120,"cell":{"w":8,"h":17},"dark":true,"reduceMotion":false,"hour12":false}
```

| 字段 | 含义 |
| --- | --- |
| `v` | 终端从你的列表中选定的版本（`1`）。 |
| `term`, `ver` | 终端及其版本：`tern`，且版本与 `TERM_PROGRAM_VERSION` 相同。 |
| `kinds` | 它绘制的每一种节点类型（[元素](../elements/index.md)）。按类型回退：未列出的类型可以用其他方式描述，或以预渲染的 `rows` 描述。 |
| `features` | 仅有类型本身无法推断的行为（见下）。 |
| `apc` | 单条消息可发送的最大体（65536 字节）；更大的请[分块](transport.md#chunking)。 |
| `credits` | 你可以有多少帧尚未确认（2；[流控](operations.md#flow-control)）。 |
| `cols`, `cell` | 面板的列宽，以及以像素为单位的单元尺寸。只有 `rows` 回退与 ANSI 宽度判断需要它们；`resize` 事件会更新它们。 |
| `dark` | 终端是否以深色外观显示（`theme` 事件会更新它）。 |
| `reduceMotion` | 是否开启了“减弱动态效果”（`motion` 事件会更新它）。此时你可以丢弃仅用于动态效果的节点。 |
| `hour12` | 用户的系统是否读取 12 小时制时间（`3:05 PM`）而非 24 小时制（`15:05`）：由窗口的区域设置决定（macOS 的 24 小时制、Windows 的短时间格式、GNOME 或 Cinnamon 的时钟格式，Linux 上则用 `LC_TIME`），即使你的程序运行在另一台机器上也是如此。用它格式化你显示的时间（JavaScript 的 `toLocaleTimeString` 中的 `hour12`）；你自己进程的区域设置可能并不知道。 |

终端特性：

| 特性 | 含义 |
| --- | --- |
| `blobs` | `b` 动词与 `blobs` 查询。 |
| `settle` | `settle` 操作是有用的提示（[帧操作](documents.md#frame-ops)）。 |
| `adopt` | 带 `adopt:true` 的 `o` 会重新打开已关闭的 Surface（[Surface](surfaces.md#open-and-close)）。 |
| `dock` | `dock` 区域贴在面板底部（[区域](surfaces.md#regions)）。 |
| `reduce-motion` | 会报告 `reduceMotion` 与 `motion` 事件。 |
| `aside` | 内联 Surface 的 `layer` 中的 `prefs` 节点停靠在面板旁（[区域](surfaces.md#regions)）。 |
| `scroll` | `scroll` 操作（[帧操作](documents.md#frame-ops)）。 |
| `styles` | `s` 动词（[样式表](theme.md#stylesheets)）。 |
| `flow` | `mode:"flow"` 的 Surface（[模式](surfaces.md#modes)）与 `listen:false`（[打开与关闭](surfaces.md#open-and-close)）。 |
| `font` | `o` 接受 `font:"sans"`，以 UI 字体绘制 Surface（[打开与关闭](surfaces.md#open-and-close)）。不支持该特性的 Tern 以等宽字体绘制每个 Surface。 |

## 其他查询 {#other-queries}

`blobs` 询问 Tern 已经拥有哪些 blob，使重启后的程序只重发缺失的部分：

```text
→ ESC _ tsp;q;{"q":"blobs","ids":["9f86d0…","2c26b4…"]} ESC \
← ESC _ tsp;r;{"r":"blobs","have":["9f86d0…"]} ESC \
```

`ids` 是 blob id，即每个 blob 字节的小写十六进制 SHA-256（[blob](transport.md#blobs)）。`have` 按你询问的顺序列出 Tern 持有的那些：它们可能在内存中，也可能在其磁盘上的 blob 缓存中，后者随后会被加载。询问即算一次使用：当 Tern 驱逐未被引用的 blob 时，最近最少使用的最先驱逐，而你刚询问过的会排在最后。

Tern 不应答其他查询：未知的 `q` 得不到回复。体不是有效 JSON 的 `q`（或任何消息）会收到 `error` 事件，例如 `{"ev":"error","msg":"malformed q body: …"}`。

## 不等待回复的启动 {#starting-without-waiting}

等待回复会让首次绘制延迟一个往返。当环境指明是 Tern（`TERM_PROGRAM=tern`）且你不在多路复用器内部（含 tmux）时，你可以一次发送 `o` 与首个 `f`，按假定为 v1 的能力：所有类型、`apc` 65536 与 `credits` 2、`cols` 取自终端尺寸、`reduceMotion` 与 `hour12` 为 false。在查询发出之前把 tty 切换为原始输入，以免 Tern 的事件被已处理的 tty（cooked tty）回显。回复到达时仍然有决定权：它的 `kinds`、`apc`、`credits` 与外观会取代这些假定。若 DA1 有应答却得不到回复，或一秒内没有回复到达，则关闭该 Surface（带 `keep:false` 的 `x`），并用自己的渲染器绘制。omp 就是这样启动的。

## 环境变量与关停选项 {#environment-and-opt-outs}

- Tern 为每个面板设置 `TERM_PROGRAM=tern` 与 `TERM_PROGRAM_VERSION`：在窗口中、在会话守护进程中，以及通过 `tern remote` 访问的守护进程中。环境不会在 ssh 之后留存；查询则会，因此起作用的是握手。
- Tern 的 “Native program surfaces” 设置会关闭 TSP：此后 Tern 从不应答 `hello`，并忽略每一条 TSP 消息。插件 block 与 canvas 属于 Tern 自身，仍会继续绘制。
- `TERN_BLOB_DIR` 指明你程序所运行机器上 Tern 的 blob 缓存文件夹，用于在不经 pty 的情况下移交 blob（[通过 Tern 的 blob 缓存](transport.md#through-terns-blob-cache)）。
- screen 与 zellij 会吞掉 APC 字符串。在它们内部不要探测。
- 在 tmux 内部，仅当会话设置了 `@tern-tsp` 选项时才探测（[在 tmux 内部](#inside-tmux)）。
- 给你的用户一个他们自己的开关，用来强制使用你的 ANSI 渲染器（omp 有 `PI_TUI_NATIVE=0`）。
