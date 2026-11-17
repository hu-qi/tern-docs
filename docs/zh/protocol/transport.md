# 传输 {#transport}

TSP 以 APC 字符串的形式，在面板的 pty 上带内传输。这种方式在 ssh 下可用，与程序写入
的其他每个字节保持顺序，并让 Tern 的会话守护进程无需第二条通道就能保留并重放
Surface。

## 帧结构 {#framing}

```text
ESC _ tsp ; <verb> [; <key>=<value>]* ; <body> ESC \
```

- `verb` 是单个字母（见下），区分大小写。
- 动词之后的片段只有在形如 `key=value`（键为 `[A-Za-z0-9_-]+`，值为除 `;` 之外的
  可打印 ASCII，不含空格）**并且**其后还有另一个 `;` 时才是参数。第一个不符合该形式
  的片段开始正文，因此含 `;` 或 `=` 的 JSON 正文保持完整，而没有参数的消息就是
  `tsp;<verb>;<body>`。
- `body` 是 UTF-8 JSON，`b` 则为 base64。JSON 会转义每个控制字符，因此正文绝不会
  包含 ESC 或 BEL；Tern 把字符串内部 8 位的 `0x9C` 当作载荷而非终止符，所以原始
  UTF-8 是安全的。不是有效 JSON 的正文会得到一个 `error` 事件，
  `{"ev":"error","msg":"malformed f body: …"}`。
- 每条消息都以 7 位 ST `ESC \` 结束。Tern 的解析器也会像 kitty 那样在 BEL 处结束
  任何字符串，但 TSP 只定义 ST：绝不要发送以 BEL 终止的 TSP。
- 未知的动词与未知的 JSON 字段在双向都被忽略（未知动词不会得到 `error`）。新字段
  永远是可选的；不兼容的变更会提升协议版本（见[握手](handshake.md)）。

Tern 读取的参数：

| 参数 | 所在动词 | 含义 |
| --- | --- | --- |
| `c`, `m` | 任意动词 | [分块](#chunking) |
| `mime` | `b` | 该 blob 的 MIME 类型（[Blob](#blobs)） |
| `key`, `buf`, `seeded` | `o` | 保留给 Tern 的会话守护进程所重放的快照，且只在那里读取：在程序的 `o` 中它们被忽略。 |

| 动词 | 方向 | 含义 |
| --- | --- | --- |
| `q` | 程序 → 终端 | 一次查询：`hello`、blob 是否存在（[握手](handshake.md)） |
| `o` | 程序 → 终端 | 打开一个 Surface（[Surface](surfaces.md)） |
| `f` | 程序 → 终端 | 一个帧：文档操作的原子批次（[文档与帧](documents.md)） |
| `b` | 程序 → 终端 | 一个 blob（见下） |
| `t` | 程序 → 终端 | 已废弃；被忽略（[样式表与图标](theme.md)） |
| `s` | 程序 → 终端 | 一个样式表（[样式表与图标](theme.md#stylesheets)） |
| `x` | 程序 → 终端 | 关闭一个 Surface（[Surface](surfaces.md)） |
| `r` | 终端 → 程序 | 对 `q` 的回复 |
| `e` | 终端 → 程序 | 一个事件（[输入与事件](input.md)） |

终端 → 程序的消息走在 pty 的*输入*一侧，就像对 DA 或 OSC 11 的回复，每条都是一个
`ESC _ tsp;<verb>;<json> ESC \` 字符串且不带参数：Tern 从不分块发送它们。读取输入时
应使用能接收任意长度完整 APC 字符串的转义序列缓冲区（携带表单值的事件可能很长），
并在按键处理之前把 `ESC _ tsp;` 字符串转交给 TSP 代码。绝不要回显或打印它们。

一个追加流式 Markdown 并把卡片标记为完成的帧：

```text
ESC _ tsp;f;{"sf":"s1","s":812,"ops":[["text","a41","append"," and then the parser"],["set","t9",{"tone":"success","status":"done"}]]} ESC \
```

## 分块 {#chunking}

正文超过协商的 `apc` 上限（除非 `hello` 回复另有说明，否则为 65 536 字节）时，会
拆分到动词相同的多条消息中，每块携带 `c=<chunk-id>`（自行选择的记号），并且除最后
一块外每块都带 `m=1`。Tern 在解析前按字节拼接正文，因此切分点可能落在 UTF-8 字符
内部，但不能落在下一块正文将以形似参数的片段开头的位置（见下）。拼接后的消息保留
第一块的其他参数（blob 的 `mime`）；后续各块的参数被忽略：

```text
ESC _ tsp;f;c=k7;m=1;{"sf":"s1","s":9,"ops":[["text","log","append","…first 65 000 bytes… ESC \
ESC _ tsp;f;c=k7;…the rest…"]]} ESC \
```

Tern 一次只拼接一个序列，因此一条消息的各块要连续发送。以下任一情况都会丢弃该序列
并给出 `error` 事件
（`{"ev":"error","msg":"chunked f message c=k7 dropped: interrupted"}`）：任何不是其
下一块的 TSP 消息到达（没有 `c`、另一个 `c` 或另一个动词）；1 秒内没有收到下一块
（`timed out`）；或拼接后的正文将超过其上限（帧为 400 000 000 字节，其他消息为
24 MiB，`over 25165824 bytes`）。因超出大小而被丢弃的序列，其余部分会被跳过，直到
最后一块。RIS 会静默丢弃它。打断某个序列的消息仍会按自身的语义处理。

不要为了适应上限而拆分帧：其上限远高于面板的保留预算，超出预算的文档会被裁剪
（[保留策略](operations.md#retention)），因此还原长对话记录的帧会整体发送。

每一块都会像其他消息一样解析参数，因此块正文本身不能以形似参数的片段开头：以
`x=1;y…` 开头的 JSON 块会把 `x=1` 静默地当作参数丢掉。切分点若会产生这样的前缀，
就移到别处：紧挨 `;` 之前切分，或在除 `A`–`Z`、`a`–`z`、`0`–`9`、`_` 与 `-` 之外的
任何字节之前切分，总是安全的。Base64 中没有 `;`，因此 blob 的分块是安全的。Tern
自己的分块器（用于重放会话守护进程的快照）遵循同一规则。

Tern 的解析器会放弃超过 262 144 字节的 APC 字符串（`ESC _` 之后的一切，包括参数）
且不给出 `error`，该字符串的其余部分随后会作为文本显示在屏幕上。Tern 接受不超过该
大小的单个字符串，但每块都应保持在 `apc` 之内。

## Blob 数据 {#blobs}

`b` 一次性发送二进制数据，即 `image` 节点所显示的图像：

```text
ESC _ tsp;b;mime=image/png;<base64> ESC \
```

- 正文是标准 base64（`+/`、`=` 填充，无换行）。Tern 拒绝错误的 base64 并给出
  `error` 事件。
- blob 的 id 是其解码后字节的小写十六进制 SHA-256（64 位数字）。它不会被发送：Tern
  对到达的字节计算哈希，而程序需自行对字节计算哈希，以便在 `image` 节点或 `blobs`
  查询中为 blob 命名。Tern 忽略 `id` 参数。
- `mime` 是可选的。
- 一个 blob 解码后最大 16 MiB，并像其他消息一样分块（`mime` 放在第一块）。
- Blob 按内容寻址，由面板的各 Surface 共享，并由 Tern 保存在磁盘上，因此还原的屏幕
  无需重发就能显示其图像；当另一个面板发送过某个 blob，而本面板从未收到、却有
  `image` 节点命名它时，会从磁盘副本绘制。可用 `blobs` 查询询问还需要发送哪些
  （[握手](handshake.md#other-queries)）。

### 经由 Tern 的 blob 缓存 {#through-terns-blob-cache}

与 Tern 的 blob 缓存同处一台机器的程序，可从 `TERN_BLOB_DIR` 找到该缓存的目录：Tern
为它启动的每个面板设置该变量，而 ssh 不会把它传递过去。可以改用下面的方式，而不通过
pty 发送 blob 字节：

1. 把它们写入 `$TERN_BLOB_DIR/<id>`，id 是该 blob 的小写十六进制 SHA-256：先在该
   目录写入 `<id>.tmp<pid>`，然后重命名，这样 Tern 绝不会读到不完整的文件。若
   `<id>` 已存在，跳过此步。
2. 用 `blobs` 查询该 id。Tern 读取文件，校验其字节的哈希与文件名一致，并把该 id
   列入 `have`；它从这些字节判断图像类型。
3. 对 `have` 中缺少的每个 id，照常用 `b` 发送。

可以在回复到达之前就发送显示该图像的帧。

## Windows 平台 {#windows}

在 Windows 上，pty 是 ConPTY，其 host（`OpenConsole.exe` 或 conhost）在双向都位于
Tern 与程序之间。

**终端 → 程序。** ConPTY 的输入解析器会丢弃 APC 字符串，因此 `ESC _ tsp;…` 形式的
输入永远到不了程序。它原样透传 OSC 字符串，所以 Tern 把终端 → 程序的消息写入 ConPTY
时采用

```text
ESC ] 877 ; tsp ; <verb> [; <key>=<value>]* ; <body> ESC \
```

正文除 U+0080–U+009F 之外逐字节相同：解析器会接受字符串内部的 C1 控制字符，而
U+009C 会结束该字符串，因此这些码位（只会出现在 JSON 字符串内部）以其 JSON 转义
`\u0080`…`\u009f` 传输。两种帧结构以及以 BEL 终止的 OSC 877 都应接受，并按同一方式
处理。OSC 877 只用于终端 → 程序方向；macOS 与 Linux 上的终端仍使用 APC。

**程序 → 终端。** 消息仍使用 APC。Windows 自带的 conhost 会重新渲染程序的输出并
丢弃 APC，因此 TSP 需要 Tern 随附的 ConPTY（`conpty.dll` 与 `OpenConsole.exe`，
安装在 `tern.exe` 旁边）。该 host 把程序的输出原样写入终端，并把 DA1 之类的查询留给
终端，所以 `hello` 及其 DA1 哨兵会按顺序到达 Tern，并按顺序得到回复。
