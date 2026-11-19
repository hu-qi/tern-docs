# 控制命令 {#control-commands}

控制命令通过 `tern ctl` 检查并驱动正在运行的 Tern 窗口或无头服务器。可以用它们检查
插件 UI、查看应用状态、在不重新构建的情况下更改窗口样式，或测量渲染。与普通场景命令
不同，大多数检查命令会立即回复，而不是先让动画稳定。

## 连接与回复 {#connection-and-replies}

| 命令 | 作用 |
| --- | --- |
| `tern serve [--control <endpoint>] [--out <dir>]` | 启动无头控制服务器。 |
| `tern --control <endpoint> [ARGS]` | 打开一个带控制端点的桌面窗口。 |
| `tern ctl [--control <endpoint>] <command...>` | 发送一行并打印其 JSON 回复。 |
| `tern ctl [--control <endpoint>] --file <scenario>` | 在同一个连接上发送每一行非空、非注释的内容，收到上一条回复后再发送下一条。 |

端点是 `127.0.0.1` 上的套接字路径或数字 TCP 端口。端口 `0` 表示由服务器选择一个空闲
端口。默认值在 Unix 上是 `/tmp/tern.sock`，在 Windows 上是用户临时目录中的
`tern.sock`。Windows 套接字端点要求 Windows 10 1803 或更高版本。多个客户端可以连接；
命令一次执行一条。

在 Tern 面板中，不带 `--control` 的 `tern ctl` 不需要端点：会话守护进程会把每一行转给
本机上显示该面板的 Tern 窗口，由该窗口在自身上执行（包括 `state`、world 命令与
`quit`），并像端点那样回复。没有这样的窗口时（该面板只由另一台机器上的窗口显示，或
其窗口已关闭），回复为 `{"ok":false,"error":"…"}`。在面板中执行
`tern ctl --control <endpoint>` 仍会发送到该端点。

线路协议是一行命令后跟一行 JSON 回复：

- 无结果：`{"ok":true}`。
- 对象结果：其字段合并进 `{"ok":true,...}`。
- 其他任意结果：`{"ok":true,"value":...}`。
- 失败：`{"ok":false,"error":"..."}`。

`--file` 打印每条命令及其最多 400 个字符的回复，并在第一条失败的回复处停止。底层回复
不会被截断。Harness 的等待与应用命令的稳定过程决定文件的推进节奏；检查命令不添加
等待。仅限控制的命令不被 `tern shot` 接受。

控制语法与[场景语法](index.md#syntax)不同：`dump`、`tree` 与 `webreports` 把该行剩余的
全部内容作为选择器，且不去除引号。`webcall` 把第一个 `{` 之前的所有内容作为选择器，并
把其余部分解析为 JSON。`css` 把第一个词作为样式表名称，把该行其余内容作为路径，路径
可以包含空格。不要给这些参数添加脚本引号或行尾注释。

## 检查窗口 {#inspecting-a-window}

| 命令 | 作用 |
| --- | --- |
| `dump [<selector>]` | 返回截图布局 JSON：元素路径、边框与计算几何；选择器把它限制为具有几何信息的匹配项。 |
| `tree [<selector>]` | 返回可见元素树，或带文本、值、焦点与网页视图地址/标题的可见匹配项。 |
| `pick <x> <y>` | 返回视口某点处的元素及其几何信息与相关样式。 |
| `state` | 返回 Tern 的应用状态。 |
| `stats` | 返回时钟、帧、文档大小、视口/缩放、指针、解析后的鼠标光标、动画、文本光标、下一个计时器、拖出操作与网页视图。 |
| `layers` | 按绘制顺序返回 `count` 与 `layers`，含深度、边界、不透明度、变换、裁剪、遮罩、滤镜与背景效果。 |
| `a11y` | 返回以窗口为根的辅助功能树。 |
| `menus` | 返回原生菜单栏、Dock、托盘与已打开的上下文菜单行。 |
| `system` | 返回系统集成状态与最近的一次性请求。 |

坐标与辅助功能边界使用视口 CSS 像素。`pick` 恰好接受两个数值。无效选择器会使回复失败。
不带参数的命令拒绝参数；带参数的 `a11y` 则执行 harness 辅助功能操作，见
[Harness 命令](harness.md)。

辅助功能节点有 `id`、`role`，以及可选的 `name`、`description`、`value`、
`placeholder`、`states`、`level`、`posinset`、`setsize`、`bounds`、`actions` 与
`children`。空字段与文本框内的文本段会被省略。菜单操作包含 id、标签、启用/选中状态与
加速键；子菜单包含 `items`。`system` 包含对话框、通知、徽章、进度、标题、已编辑/表示
的文档、最近文档、快捷键、睡眠、安全输入、强调色、显示器、密钥与请求日志。无头系统
集成是模拟的；检查它们不会回应对话框。

这些快照描述 UI 与 host 状态，而不是单独的 Tern `state` 字段。例如，指针或拖出操作用
`stats`，原生菜单用 `menus`，待处理的对话框用 `system`。

### Tern 状态字段 {#tern-state-fields}

`state` 把以下顶层字段合并进成功的回复。已关闭或未启用的功能可能为 `null` 或为空。

| 字段 | 描述 |
| --- | --- |
| `tabs`, `focused`, `panes`, `sessions`, `decks`, `tabs_out` | 标签页、聚焦终端、面板网格尺寸与会话/导航布局。 |
| `palette`, `palette_scope`, `find`, `menu`, `picker`, `pane_drag`, `focused_element` | 已打开的导航 UI、搜索与元素焦点。 |
| `theme_dark`, `theme_light`, `theme_preview`, `theme` | 已选主题与预览。 |
| `layout`, `tab_orientation`, `tab_badges`, `status_bar`, `pane_headers` | 面板与标签页的呈现。 |
| `material`, `opacity`, `blur`, `glass_hud`, `density`, `viewport`, `csd` | 窗口外观、视口与装饰。 |
| `font`, `ui_font`, `font_family`, `face`, `faces` | 终端与界面字号、请求的字体族以及按样式解析出的字体面。 |
| `inbox`, `hosts`, `prefs`, `peek`, `pips`, `pip_commits`, `files` | 功能特定状态。 |
| `file_blocks`, `task_manager_blocks`, `screen_blocks`, `sqlite_blocks`, `board_blocks`, `profile_blocks` | block 特定状态。 |
| `quicklook`, `lightbox`, `term_link`, `gate`, `melt` | 预览、链接、账户门槛与屏幕效果状态。 |
| `git_blocks`, `notebook_blocks`, `carly` | 仅桌面端的 block 与助手状态；在 web 与 iOS 上不存在。 |
| `update` | 更新状态；在 iOS 上不存在。 |

`focused` 包含面板 id、标签、工作目录、git 状态、正在运行的命令、忙碌状态、上一条
命令/状态、退出/错误状态、提示符就绪状态与选中的终端文本。`viewport` 反映尺寸调整；
CSS 补丁、性能剖析与 web 调用没有专门的 Tern 状态字段。

## CSS 补丁 {#css-patches}

| 命令 | 作用 |
| --- | --- |
| `css` | 按层叠顺序列出带 `name` 与 `rules` 的 `sheets`。 |
| `css <name> <path>` | 读取一个 CSS 文件并替换同名样式表，或追加一个新补丁。 |
| `css <name>` | 丢弃该名称的所有样式表，包括内置样式表。 |
| `css reload [<dir>]` | 重新读取每个样式表的文件，并换入有变化的那些。 |

`tern ctl` 发送的路径为绝对路径，按其运行所在目录解析；通过原始连接发送时，相对路径按
运行中应用的工作目录解析。`css reload` 从 `<dir>` 或其父目录查找内置样式表的文件（即它
在 Tern 源码树中的路径，只有开发者构建才会记录），因此请在检出目录中运行
`tern ctl css reload`。它回复 `reloaded`（每个样式表及其 `errors`）、`failed`（无法读取
的文件）与 `unchanged` 计数。

替换样式表会保留其层叠位置；新样式表排在最后，并胜过优先级相同但更早的规则。加载回复
`sheet`、`rules` 与 `errors`（`file`、`line`、`column`、`message`）。无效的 CSS 规则会被
丢弃，但其余规则仍然生效：解析错误不会使回复失败。无法读取的文件则会使回复失败。丢弃时回复
`dropped`。成功的补丁会调度一个实时帧或绘制一个无头帧；它不会等待动画结束。检查补丁
请使用 `css` 或 `dump`，而不是 `state`。

## 测量帧与 trace {#measuring-frames-and-traces}

| 命令 | 作用 |
| --- | --- |
| `perf` | 返回自上次重置以来的帧计时。 |
| `perf on` | 开始一次新的采集，在可用时包含 GPU 时间戳。 |
| `perf off` | 停止无头计时；桌面窗口保留 CPU 计时。 |
| `perf reset` | 重新开始现有采集。 |
| `perf mark` | 开始为 `perf since` 统计后续帧。 |
| `perf since` | 返回自标记以来的计时，包括 `settled`。 |
| `trace` | 返回 `recording`、一个 trace 路径或 `null`。 |
| `trace start [<directives>]` | 启动进程级 Chrome trace 并返回 `path`。 |
| `trace stop` | 结束 trace 并返回 `path`、`events` 与 `bytes`。 |

在 `perf`、`perf mark` 或 `perf since` 之前，必须用 `perf on` 启用无头计时；`perf reset`
不会启用它。实时模式下的 `on`、`off` 与 `reset` 会重置采集并回复 `gpuTiming`；`off` 关闭
GPU 计时。没有标记时 `perf since` 失败。在某一帧不再请求后续帧之前，其 `settled` 为
`null`，之后报告截至该帧的累计帧数、时间与工作量。它只观察稳定过程；不会等待它。

Trace 指令过滤记录的时间段/事件；不给指令时，默认记录 Stencil 时间段、粗粒度的 git
时间段与依赖警告。例如 `trace start stencil_ui=trace,warn`。在 `ui.perfetto.dev` 中打开
生成的 trace。在已录制时启动、无效指令与文件错误都会失败；没有录制时停止会失败。这些
测量是单独的回复，不是 Tern 状态。

## 视口与生命周期 {#viewport-and-lifetime}

| 命令 | 作用 |
| --- | --- |
| `resize <width> <height>` | 设置无头视口或实时窗口的内容尺寸，不等待稳定。 |
| `thaw` | 恢复被 `freeze-anims` 或 `motion-at` 停止的文档时间线。 |
| `quit` | 停止无头服务器或关闭实时应用。 |

`resize` 恰好要求两个数值，且都不小于 1 CSS 像素。无头尺寸调整会保留设备缩放并绘制
一帧。在控制端点处，它指的是窗口尺寸调整，而不是 Tern 的面板调整命令。`thaw` 是
harness 命令，不是仅限控制的检查命令；它不接受参数。时间线/帧活动请使用 `stats`，视口
尺寸请使用 `state.viewport`。

以下序列遵循 bell-ripple 基准；用 `ctl --file` 发送它，以捕获一个按住的效果及其静止帧：

```text
ready
freeze-anims
feed "goldens/fixtures/bell.txt"
motion-at 120
shot bell-held
thaw
wait 1300
shot bell-rest
stats
```

## 驱动网页 {#driving-web-pages}

| 命令 | 作用 |
| --- | --- |
| `webcall <selector> <json>` | 在第一个嵌入网页视图的匹配元素中调用该页面；回复其答案。 |
| `webreports <selector>` | 在 `reports` 中返回最近的受驱动页面报告，最旧的在前。 |

两者都需要实时窗口；无头会话会以“a headless session shows no pages”失败。页面缺失或
选择器无效会失败。`webcall` 按真实时间等待原生页面的答案，使用 Tern 的 20 秒条件超时；
其答案只发送给控制客户端。`webreports` 只保留跨页面最近的几百条报告。报告包含消息、
帧、对话框、选择框、下载、响应、已提交/已加载的导航与被阻止的请求。检查调用请使用这些
回复，而不是 `state`。

JSON 对象要求 `op`。可选字段可以缺省或为 `null`，另有说明者除外。未知操作、无效名称、
缺少必需字段或字段类型错误都会失败。下面列出所有接受的操作；括号中的字段名是可选的。

| 命令 | 作用 |
| --- | --- |
| `webcall <selector> {"op":"eval","function":<string>}` | 求值一个函数表达式；可选 `args` 数组（默认 `[]`）、`world`（`page\|isolated`，默认 `page`）与 `frame` 字符串。回复 `value`，JavaScript `undefined` 时无值。 |
| `webcall <selector> {"op":"capture"}` | 捕获一张图像；可选 `rect`（`x`、`y`、`width`、`height`）、`full`（false）、`scale`（1）、`format`（`png\|jpeg\|jpg`，默认 `png`）与 `quality`（80）。JPEG 质量会取整并限制在 1–100。回复 base64 `data`、`mime`、`width`、`height`。 |
| `webcall <selector> {"op":"pdf"}` | 回复 base64 `data` 与 `mime`。 |
| `webcall <selector> {"op":"input","events":<array>}` | 用下述事件形式注入页面输入。 |
| `webcall <selector> {"op":"edit","action":<copy\|cut\|paste\|selectAll\|undo\|redo>}` | 执行一个页面编辑操作。 |
| `webcall <selector> {"op":"cookies"}` | 回复 `cookies` 数组。 |
| `webcall <selector> {"op":"setCookie","cookie":<object>}` | 设置 cookie，必需 `name`、`value`、`domain`；可选 `path`（`/`）、`expires`（Unix 秒）、`httpOnly`（false）、`secure`（false）与 `sameSite` 字符串。 |
| `webcall <selector> {"op":"deleteCookie","name":<string>,"domain":<string>}` | 删除一个 cookie；可选 `path` 默认为 `/`。 |
| `webcall <selector> {"op":"scripts","scripts":<array>}` | 替换注入的脚本：每项需要 `source`；可选 `world`（`page\|isolated`，默认 `page`）、`frames`（`main\|all`，默认 `main`）与 `at`（`start\|end`，默认 `start`）。 |
| `webcall <selector> {"op":"agent"[,"value":<string\|null>]}` | 覆盖用户代理，或清除该覆盖。 |
| `webcall <selector> {"op":"media"[,"value":<string\|null>]}` | 覆盖媒体，或清除该覆盖。 |
| `webcall <selector> {"op":"appearance"[,"value":<dark\|light\|null>]}` | 覆盖页面外观，或清除该覆盖。 |
| `webcall <selector> {"op":"dialogs","report":<bool>}` | 启用或禁用对话框报告。 |
| `webcall <selector> {"op":"dialog","accept":<bool>}` | 回应页面对话框；可选 `text` 提供提示文本。 |
| `webcall <selector> {"op":"files"[,"paths":<array\|null>]}` | 提供选择框路径，或取消。 |
| `webcall <selector> {"op":"downloads"[,"dir":<string\|null>]}` | 设置或清除下载目录。 |
| `webcall <selector> {"op":"allow"[,"hosts":<array\|null>]}` | 设置或清除允许的主机列表。 |
| `webcall <selector> {"op":"credentials"[,"username":<string>,"password":<string>]}` | 设置身份验证凭据；两者都缺省/为 null 则清除，只给一个则失败。 |
| `webcall <selector> {"op":"insecure","value":<bool>}` | 更改不安全连接的许可。 |

没有列出结果的操作只返回成功。页面输入接受：

- `{"type":"mouse","action":"move|down|up","x":N,"y":N}`；
  可选 `button` 为 `left|right|middle`（默认 `left`），`clicks` 在移动时默认为 0，其他
  情况为 1，并限制、截断到 0–16。
- `{"type":"wheel","x":N,"y":N}`，可选 `dx`、`dy`（均为 0）。
- `{"type":"key","action":"down|up","key":"..."}`，可选字符串 `code` 与 `text`。
- `{"type":"text","text":"..."}`。

鼠标、滚轮与按键事件接受 `mods`，即由 `shift`、`ctrl|control`、`alt|option` 与
`meta|cmd|command` 组成的数组（默认空）。原生页面能力因平台而异；一次调用能通过解析，并不
保证 host 支持它。页面在 macOS、Linux 与 Windows 上都能被驱动。在 Windows（WebView2）
上，由其他进程渲染的帧（例如跨站帧）无法触达：对其执行带 `frame` 的 `eval` 会失败，其
消息也不会被报告；`credentials` 只回应 HTTP basic 身份验证。Tern 的 `snapshot` 与
`act` 等浏览器操作在此不被接受；请使用 [浏览器 block](browser.md)。

## 另见 {#see-also}

- [脚本](index.md)：运行、夹具与时机。
- [Harness 命令](harness.md)：输入、截图与时间线控制。
- [浏览器 block](browser.md)：Tern 的浏览器专用驱动。
- [调试](../guides/debugging.md#driving-a-window-from-a-script)：插件 UI 工作流。
