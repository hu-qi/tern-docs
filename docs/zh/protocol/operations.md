# 流量控制、持久化与安全 {#flow-control-persistence-and-security}

## 流量控制 {#flow-control}

- **信用额度。** 最多保持 `credits` 个帧（除非 `hello` 回复另有说明，否则为 2）未确认。
  `ack` 携带窗口已绘制的最大帧 `s`，并涵盖直到它的每一帧：Tern 每绘制一帧确认一次，
  因此若某一帧与下一帧被一并应用并绘制，它就不会单独得到确认。等待 `ack` 期间，应持续把变更
  协调进一个待处理操作列表，合并同一 id 上的 `set`、合并 `text` 追加，并在 `ack` 到达
  时发送一个帧。快速窗口能看到每一帧；较慢的窗口、繁忙的守护进程或 ssh 延迟则会看到
  更少、更大的帧，而 pty 永远不会被淹没。信用额度取代了渲染定时器与更新合并。
- **谁发送 ack。** 绘制该 Surface 的窗口发送 `ack`。没有窗口显示该面板时（会话已分离），
  不会有任何 `ack` 到达：应保留待处理的操作，附着上来的窗口会绘制当前文档并对其确认。
  以 `listen:false` 打开的 Surface 不会收到 `ack`，因此发送时不受信用额度限制。
- **流式输出。** 在 `md`、`ansi` 或其他文本节点上以 `text append` 操作流式发送文本：
  链路上传输的字节只有新增部分，而 `md` 节点从最后一个未闭合的 block 起重新渲染。
- **settle。** 只要之后还可能修改某个节点，就保留它的 *id*，但不必保留其完整描述。
  `settle` 之后，停止对比该子树并丢弃其缓存的描述；后续的修改以按 id 定位的操作发送
  （`set`、`text replace`，或 `del` 加重新构建子树的 `add`）。这样内存占用与文档的
  活跃部分成正比，而不是与其历史成正比。对已 settle 的子树的后续操作会清除它触及的
  节点及其每个祖先上的标记，因此在用完之后要再次 `settle` 顶层 block，否则
  [保留策略](#retention)无法将其驱逐。
- **时长。** 时长以 age 的形式传输，因此不需要保持同步的时钟
  （[时间与动画](documents.md#time-and-animation)）。

## 保留策略 {#retention}

Surface 的锚点是一行网格，因此仅凭回滚缓冲区的长度无法界定它。Tern 为每个面板设定
Surface 预算：默认 64 MiB 的文档状态，估算方式为每个节点的 id 与 props 加上固定的
每节点开销，再对该面板的每个 Surface 与命令 block 求和。每帧、每个样式表或每次关闭
若使面板超出预算，就按以下顺序驱逐：

1. 已关闭的 Surface 与已结束的命令 block，整体驱逐，最旧的优先。
2. 打开的 Surface 中，`main` 下最旧的、已 settle 的顶层子节点。只有本身被 settle 的
   子节点才算，带已 settle 后代的节点不算。当该 Surface 监听时，Tern 用 `gone` 事件
   （`{"ev":"gone","sf":…,"ids":[…]}`）逐个报告，之后对已被驱逐的 id 的操作会作为
   未知节点被拒绝。

没有可驱逐的已 settle 内容时，面板会保持超出预算。已关闭的 Surface 在其锚定行离开
回滚缓冲区时也会被整体驱逐。

应用一个帧的耗时与它的操作数成正比，布局按已改动的子树增量进行，很长的 `main`、
`list`、`code`、`ansi` 与 `md` 内容会被虚拟化：对回滚缓冲区上方第 10 000 个 block
的操作在应用时不会布局它与视口之间的任何内容。

## 持久化 {#persistence}

- 面板的屏幕拥有这些 Surface 文档。在 Tern 会话中，由会话守护进程的屏幕持有它们，
  每个附着的窗口都收到相同的字节，因此文档会像网格内容那样在窗口重启后依然存在。
- 附着到运行中面板的窗口会得到一个快照，它经由正常解析器重放：先是一个携带程序
  `app` 与 `features` 的 `hello`，然后是每个 Surface（已关闭的在前）作为合成的 `o`
  （带有其模式、`listen`、`closable`、`title` 与 `role`）、其样式表（`s`），以及
  一个帧，其中以程序最后一次 `s` 添加整个文档，随后是对已 settle 节点的 `settle`、
  焦点，以及挂起时的 `suspend`。已关闭的 Surface 在其后得到自己的 `x`（`keep:true`）。
  Tern 计时得到的每个 age（`elapsed`、`tool` 与 `agent` 定时器，包括倒计时）都会改写
  为快照时间。Tern 对这次重放的任何回复都不会到达程序。
- 分离并重新附着时，活动 Surface 会继续：程序仍在信用额度之内向 pty 写入，新窗口
  绘制当前文档。
- 守护进程停止（崩溃或重启）后还原的面板会启动一个新的 shell。其内联与 flow Surface
  以及命令 block 会以已关闭、只读的形式回到回滚缓冲区中原锚定行的位置；`screen`
  Surface 不会回来。
- Blob 以其 SHA-256 保存在磁盘上（Tern 的缓存目录 `blobs/`），因此快照或还原的面板
  无需程序重发就能显示其图像，而重启的程序可通过 `blobs` 查询在那里找到它们。
- 仅与视图有关的状态（折叠、控件开关、滚动位置）属于窗口，不在快照中。应将重要的
  部分镜像到 props 中。

## 调试 {#debugging}

- **记录。** 把写入与读取的每条 TSP 消息连同时间戳记入日志，采用 JSONL 行
  `{"t":ms,"dir":"out"|"in","verb":"f","params":{…},"body":{…}}`（omp 通过
  `PI_TUI_TSP_RECORD=<file>` 写出这类记录）。
- **重放。** Tern 的场景命令
  `surface-play "<file.jsonl>" [from <frame>] [until <frame>] [paced [<times>]]`
  把记录中的 `out` 消息（`o`、`t`、`s`、`f`、`x`、`b`）送入聚焦的面板。`<frame>`
  是帧的 `s`，或某个 Surface 的 `<sf>#<s>`；`until` 在其之后停止，`from` 在其之后
  开始，因此第二次播放可以接着第一次继续。没有 `paced` 时整个范围落在一个帧中；
  `paced` 按记录时的节奏播放，`<times>` 表示倍数（默认 1）。手写的
  `{"dir":"out","verb":"osc","body":"2;Title"}` 行按普通 OSC 播放，`pty` 行的正文
  原样打印，因此记录可以包含 Surface 周围的输出。首次播放会把面板重启为一个替身
  程序，它读取并忽略 Tern 的回复。运行场景与控制套接字的说明见
  [调试](../guides/debugging.md)。
- **检查。** 控制套接字的 `tree` 命令列出某个 Surface 的元素，这些元素通过其区域
  携带的 `o` `role`（即 `data-surface`）来定位（`tree "[data-surface='omp.session']"`）；
  `css` 列出已安装的样式表，其中程序自己的以 `tsp:<scope>:<name>` 形式列出，
  `<scope>` 是该视图的 `data-scope` 记号（`sf1`、`sf2` 等）。

## 安全与限额 {#security-and-limits}

- 不使用脚本，也不使用原始 HTML。`el` 从固定的标签列表与属性允许列表构建元素
  （[HTML 元素](../elements/el.md)）；Markdown 中的原始 HTML 会作为字面文本绘制。
- 程序的 CSS 只能作用于自己的 Surface 内部，且不能加载任何内容（`url()`）、逃出面板
  （`position: fixed`）或引入字体：Tern 丢弃 `url()` 与 `position: fixed` 声明并用
  `error` 事件报告，同时忽略 `@font-face` 规则（[样式表](theme.md#stylesheets)）。
  Span 与 props 只接受记号，绝不接受原始颜色。
- 链接的行为类似 OSC 8 超链接：悬停时显示，仅在明确的操作下打开。`file://` 链接
  限于路径；任何情况都不会执行命令。
- 事件只携带程序创建的 id，以及用户选择的值。键入的文本以 pty 输入的形式到达，绝不
  作为事件到达，只有两个需显式启用的例外：原生编辑的 `edit` 事件（`edit` 特性），
  以及用户或 Carly 请求的 `send`（`send` 特性）（[输入与事件](input.md#native-editing)）。

| 限额 | 值 |
| --- | --- |
| 单个 blob | 解码后 16 MiB（更大的会被拒绝并给出 `error`） |
| 每个屏幕保留的 blob | 256 MiB；超过后未引用的 blob 会被移除，最久未使用的优先 |
| 磁盘上保留的 blob | 1 GiB；守护进程启动时移除最久未显示的 |
| 每个 Surface 的节点数 | 200 000，含根节点（触及该上限的 `add` 会被拒绝并给出 `error`） |
| 深度 | 64 层 |
| 每个 Surface 的样式表 | 所有样式表合计 256 KiB 的 CSS（超过上限的样式表整体被拒绝） |
| 单个 APC 字符串 | 262 144 字节；更长的会被 Tern 静默放弃。按 `hello` 的 `apc`（65 536）切分正文 |
| 单个分块消息 | 帧拼接后 400 000 000 字节，其他消息 24 MiB；序列闲置 1 秒或被另一条 TSP 消息打断即被丢弃并给出 `error` |
| 每个面板的 Surface 状态 | 默认 64 MiB（[保留策略](#retention)） |
