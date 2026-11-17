# Harness 命令 {#harness-commands}

Harness 命令驱动窗口本身：输入、视口、时间、截图以及模拟的系统事件。把它们与 Tern
命令配合使用，可以复现一次用户交互、截取某个过渡过程，或提供无头窗口无法从操作系统
收到的事件。

## 视口、时间与截图 {#viewport-time-and-capture}

| 命令 | 作用 |
| --- | --- |
| `size <W> <H> [scale]` | 以 CSS 像素设置视口；可选择设置无头设备缩放。 |
| `wait <MS>` | 让时间流逝，单位为毫秒。 |
| `freeze-anims` | 停止文档时间线，包括计时器。 |
| `thaw` | 恢复已停止的时间线。 |
| `motion-at <MS>` | 停止时间，并把每个运行中的动画定位到其自身运行的指定毫秒处。 |
| `shot <name>` | 写出 PNG 及配套的布局 JSON。 |
| `record start <name> [fps N] [speed X]` | 开始把窗口录制到 `<name>.mp4`。 |
| `record speed <X>` | 从下一帧起以另一速度录制。 |
| `record stop` | 结束视频，并报告其路径、帧数、发生变化的帧数（`encoded`）、时长与大小。 |

省略 `scale` 会保留当前缩放。该值必须为正；实时窗口会忽略它。`size` 会等待缩放调整
完成；控制命令 `resize` 不会。`wait` 在无头环境中推进模拟时间，在实时窗口中等待真实
时间。它不是等待 shell、文件或网络结果：这类等待请使用相应命令族中的等待命令。在
[总览](index.md#timing)中描述的真实工作等待会在 20 秒后失败。

`motion-at` 要求时间非负。如果中间的等待会提前结束某个运动，请把 `freeze-anims` 放在
启动该运动的操作之前。冻结的时间不会触发运动结束计时器。`shot` 名称只能包含 ASCII
字母、数字、`_`、`.` 与 `-`，且不能为空。截图写入运行器的输出目录。

`record` 录制无头运行（`shot`、`serve`），并要求 `PATH` 中存在 `ffmpeg`。它在脚本时间
的每 `X × 1000 / N` 毫秒取一帧，因此每次 `wait`、键入、手势与稳定过程都会按其
发生时的样子呈现：`fps` 默认为 60（不超过 240 的整数），`speed` 默认为 1，即真实
时间。较高的速度生成延时摄影（`speed 20` 把 20 秒压缩为 1 秒），较低的速度生成慢动作
（`speed 0.25`）。等待真实工作的命令，例如 `run` 后接 `expect`，会按真实节奏录制。视频
与截图放在一起，命名方式相同（暗色运行中带 `-dark`），并显示聚焦文本框的光标。与前一
帧完全相同的帧不会再次编码：前一帧保留在屏幕上，因此静止窗口几乎不产生开销，而
`.mp4` 使用可变帧率。脚本结束时，仍在进行的录制会停止。
在 `serve` 中，命令之间的空档会被略去。录制期间调整窗口大小会使录制失败；同一时间只能
有一个录制。

```text
size 1280 800
ready
record start palette-demo
palette theme
wait 600
key Escape
wait 400
record stop
record start steps fps 30 speed 10
run "for i in $(seq 1 20); do echo step $i; sleep 0.5; done"
expect "step 20"
record stop
```

状态：`viewport` 报告尺寸与缩放；`panes` 报告终端尺寸。`melt` 报告正在播放的屏幕效果
及其进度。`tern ctl state` 中没有通用的动画时钟或截图字段；时钟信息请用 `stats`，截图
路径见截图的回复。

## 指针与滚动 {#pointer-and-scrolling}

| 命令 | 作用 |
| --- | --- |
| `move <X> <Y>` | 移动指针，包括按住按钮时的移动。 |
| `down [X Y]` | 按下主按钮，可选择先移动。 |
| `up [X Y]` | 释放主按钮，可选择先移动。 |
| `click <X> <Y> [right\|middle] [ctrl] [meta] [alt] [shift]` | 按坐标单击，可带次级按钮或中键以及修饰键。要求粘贴主选区的中键单击，会在 Linux 上粘贴系统主选区，在无头环境中则从会话自身的主选区粘贴。 |
| `click <selector> [right\|middle] [ctrl] [meta] [alt] [shift]` | 单击第一个匹配元素的中心。 |
| `dblclick <X> <Y> [right\|middle] [ctrl] [meta] [alt] [shift]` | 单击两次，第二次按下标记为双击。 |
| `dblclick <selector> [right\|middle] [ctrl] [meta] [alt] [shift]` | 双击第一个匹配元素。 |
| `hover <selector>` | 移动到第一个匹配元素的中心。 |
| `wheel <DX> <DY> [ctrl] [meta] [alt] [shift] [lines] [phase <phase>] [momentum <phase>]` | 在当前指针位置滚动。 |

坐标是视口 CSS 像素。不给坐标时，`down` 与 `up` 使用当前指针。单击修饰键与 `right`
可以按任意顺序出现在末尾；当选择器最后一个词会被当作选项时，请为该选择器加引号。
单击与悬停的选择器也可以由多个不加引号的词组成，这些词以空格连接。选择器必须非空且
匹配某个元素。`hover` 本身不会等待工具提示：请在其后跟上 `wait 700`。

滚轮增量默认为精确像素；`lines` 选择按行增量。两个 phase 都默认为 `none`。各自接受
`none`、`began`、`changed`、`ended`、`canceled` 或 `maybegin`；滚轮选项可以按任意
顺序出现。输入在送达之前会先关闭已打开的上下文菜单。

状态：`focused_element` 标识 DOM 焦点，`focused.selection` 报告终端选区，`pane_drag`
报告面板拖拽。指针位置与滚轮 phase 不是状态字段；指针请查看 `stats`。

## 键盘与输入法组合 {#keyboard-and-composition}

| 命令 | 作用 |
| --- | --- |
| `key <combo>` | 按下并释放一个组合键。 |
| `keydown <combo>` | 只发送按键按下。 |
| `keyup <combo>` | 只发送按键释放。 |
| `type <text>` | 向聚焦元素键入文本。 |
| `preedit <text>` | 提供输入法组合文本，光标位于末尾。 |
| `commit <text> [combo]` | 提交输入法文本，可选择附带结束组合的按键。 |
| `window-focus on\|off` | 使窗口获得或失去键窗口焦点。 |

文本与组合键都是单个参数：含空格的文本需要加引号。按键名称使用 `Meta+k`、
`Shift+Tab`、`Escape`、`ArrowLeft`、`F1` 与 `[` 这类形式。未知的按键或修饰键会失败。
`preedit ""` 结束组合。带组合键时，`commit` 在该键按下时提交并把该键继续传递下去，与
输入法处理 Enter、Tab 或 Escape 的方式相同。`type` 发送字符输入，而不是 shell 命令；
`run` 负责命令及其提示符等待。

状态：`focused_element`、`focused`、`palette`、`find` 与 `file_blocks` 反映接收该输入
的控件发生了哪些变化。没有单独的输入法或键窗口焦点字段。

## 手势与触摸 {#gestures-and-touch}

| 命令 | 作用 |
| --- | --- |
| `pinch <X> <Y> <scale> [steps N]` | 在指定点锚定，发送分阶段的捏合。 |
| `rotate <X> <Y> <degrees> [steps N]` | 发送分阶段旋转，正值表示顺时针。 |
| `smart-magnify <X> <Y>` | 发送双指双击。 |
| `swipe left\|right [X Y] [discrete]` | 发送双指导航滚动，或一次离散的三指轻扫。 |
| `swipe up\|down [X Y] [discrete]` | 发送三指轻扫，可选择离散形式。 |
| `swipe up\|down [X Y] [fingers] [to P] [hold]` | 把三根手指一起移动到指定进度。 |
| `swipe left\|right [X Y] fingers [to P] [hold]` | 把三根手指水平移动到指定进度。 |
| `force-click <X> <Y>` | 按下，发送 Force Touch 压力阶段 1、2、1，然后释放。 |
| `force-click <selector>` | 对第一个匹配元素执行 Force 单击。 |
| `touch down\|up <ID> <X> <Y>` | 放置或抬起触摸屏手指。 |
| `touch move <ID> <X> <Y> [steps N]` | 在插值的步进中移动按住的手指。 |
| `touch cancel <ID>` | 取消按住的手指。 |

捏合的缩放必须为正。捏合与旋转默认使用八个变化步进；触摸移动默认为一个。`N` 必须是
1 到 4294967295 之间的整数。手势步进相隔一个 120 Hz 帧，因此回复等待手势回放，而不是
单独的真实工作超时。

轻扫使用当前指针，除非给出了坐标点。水平非离散滚动轻扫移动视口宽度的 60%，在没有内容
滚动时转为导航。手指轻扫的进度默认为 1；`P` 必须位于 `(0, 1]`。`hold` 省略结束事件，
用于捕获按住状态的手势。`discrete` 不能与 `fingers`、`to` 或 `hold` 组合。纵向手指
轻扫也接受显式的 `fingers` 词。Force 单击的选择器遵循与单击选择器相同的规则，但不接受
按钮或修饰键选项。

触摸 ID 是 0 到 4294967295 之间的整数。最初按下的手指是主指针。把已按住的 ID 复用于
`down`，或移动、抬起、取消一个未按下的 ID，都会失败。长按即 `touch down`、`wait 600`，
然后 `touch up`。

状态：效果取决于接收的 surface（例如 `panes`、`pane_drag`、`file_blocks`）。没有手势
进度或触摸 ID 字段。

## 拖放 {#drag-and-drop}

| 命令 | 作用 |
| --- | --- |
| `drop <X> <Y> [file PATH]... [text TEXT] [url URL]... [copy\|move\|link] [hold]` | 在坐标处发送一个来自系统的进入拖拽。 |
| `drop <selector> [file PATH]... [text TEXT] [url URL]... [copy\|move\|link] [hold]` | 在第一个匹配项的中心发送一个进入拖拽。 |
| `drag-end [copy\|move\|link\|none]` | 结束一次拖出窗口的拖拽。 |

一次放置必须携带至少一个文件、文本或 URL。文件与 URL 可以重复；文本与操作只能出现
一次。载荷选项、操作与 `hold` 可以按任意顺序出现。选择器是一个参数。默认操作由目标
自行选择；指定操作则把来源限制为该操作。拒绝接收的目标不会收到放置，命令随之失败。
回复报告 `at` 与所选的 `op`；`hold` 还会报告 `held: true` 并让拖拽保持悬停。下一次
`drop` 会继续移动它。`drag-end` 默认为 `none`（取消），在没有进行中的拖出操作时失败。

状态：打开的文件出现在 `file_blocks` 中；终端插入出现在接收的终端里。没有通用的进入
拖拽状态字段；`stats` 报告拖出操作。以下基于 `file-drop-split` 基准：

```text
size 1280 800
ready
drop 1230 450 file crates/tern/goldens/fixtures/files/sample.rs hold
wait 300
shot file-drop-split-over
drop 1230 450 file crates/tern/goldens/fixtures/files/sample.rs
file wait
shot file-drop-split
```

## 外观与辅助功能偏好 {#appearance-and-accessibility-preferences}

| 命令 | 作用 |
| --- | --- |
| `appearance light\|dark` | 更改模拟的系统外观。 |
| `reduce-motion on\|off` | 使动画与过渡直接跳到结束状态。 |
| `battery on\|off` | 机器使用电池供电（默认关闭）：仅重绘的无限动画（不透明度、颜色、阴影、滤镜）按 50 ms 节拍步进；其余运动保持平滑。在实时模式下，它为目标窗口覆盖系统的电源状态，直到该窗口关闭。 |
| `reduce-transparency on\|off` | 更改会话的“降低透明度”偏好。 |
| `increase-contrast on\|off` | 更改会话的“增加对比度”偏好。 |
| `differentiate-without-color on\|off` | 更改会话的“不依赖颜色区分”偏好。 |

这些设置影响会话，而不是全局操作系统设置或已保存的 Tern 偏好。无头环境中的外观与辅助
功能更改会作用于每个文档；实时输入则送往目标窗口。状态：`theme` 反映解析后的 Tern
外观。辅助功能偏好标志没有专门的状态字段；请用 `shot` 或 `dump` 查看渲染结果。

## 文档、菜单与辅助技术 {#documents-menus-and-assistive-technology}

| 命令 | 作用 |
| --- | --- |
| `target <name>` | 把后续输入与检查路由到指定名称的文档或实时窗口。 |
| `menu <id>` | 选择一个已启用的上下文、菜单栏、Dock 或托盘操作。 |
| `menu-close` | 关闭已打开的上下文菜单。 |
| `a11y click\|focus\|blur\|scroll-into-view\|scroll-up\|scroll-down\|scroll-left\|scroll-right\|show-context-menu\|expand\|collapse\|increment\|decrement <selector>` | 执行一个不带值的辅助技术操作。 |
| `a11y set-scroll-offset <selector> <X,Y>` | 设置滚动偏移。 |
| `a11y set-scroll-offset <selector> <X> <Y>` | 用分开的数值设置同一偏移。 |
| `a11y set-text-selection <selector> <anchor,focus>` | 在字段中设置以字符索引表示的选区端点。 |
| `a11y set-text-selection <selector> <anchor> <focus>` | 用分开的索引设置同一选区。 |
| `a11y set-value\|replace-selected-text <selector> <text>` | 设置字段的值，或替换其选中的文本。 |

`main` 是第一个文档。未知目标会失败并列出可用名称；目标必须已经存在。菜单 ID 来自
`menus`。未知或已禁用的菜单操作会失败；选择上下文操作会关闭该菜单。没有打开的上下文
菜单时 `menu-close` 失败。

该操作的选择器是一个参数。若匹配项未暴露、缺少所请求的操作或未执行该操作，辅助功能
操作会失败。不带值的操作拒绝多余的值。成对的值接受逗号或空白分隔，也包括带引号的
成对值。文本操作还接受多个不加引号、以空格连接的词；`""` 清除值。

状态：`focused_element` 与接收功能的字段反映操作结果。Tern 的 `menu` 字段是其自身的
应用菜单，不是完整的原生菜单列表；检查请使用 `menus` 与不带参数的 `a11y`。Tern 的
应用状态中没有目标字段。

## 对话框与系统事件 {#dialogs-and-system-events}

| 命令 | 作用 |
| --- | --- |
| `dialog [ID] open <PATH>...` | 用一个或多个路径回应待处理的文件选择器。 |
| `dialog [ID] save <PATH>` | 用一个路径回应待处理的保存对话框。 |
| `dialog [ID] cancel` | 取消待处理的对话框。 |
| `dialog [ID] button <N> [checked\|unchecked]` | 选择消息框按钮，并可选设置其复选框状态。 |
| `haptic-reply [ID] submitted` | 确认待处理的触觉反馈请求。 |
| `haptic-reply [ID] unsupported` | 报告不支持触觉反馈。 |
| `haptic-reply [ID] failed <message>` | 报告触觉反馈失败。 |
| `notification-click <ID> [action]` | 单击已发布的通知或其操作按钮。 |
| `global-shortcut <accelerator>` | 按下已注册的全局快捷键。 |
| `open-files <PATH>...` | 发送系统打开文件的请求。 |
| `open-url <URL>` | 发送系统打开 URL 的请求。 |
| `second-instance [arg...]` | 传递第二次启动带来的参数。 |
| `power suspend\|resume\|lock\|unlock` | 发送电源或会话变更事件。 |
| `share-finish [service\|cancel]` | 完成或取消已显示的分享界面。 |

`dialog`、`haptic-reply` 与 `share-finish` 仅限无头环境。实时窗口需要改用其原生对话框、
触觉反馈后端或分享界面。这些命令回应已经待处理的请求；它们不会等待请求出现。不带
`ID` 时，对话框与触觉反馈回复会回应最早的待处理请求。ID 与待处理请求来自 `system`。
对话框按钮索引从零开始。请求不存在、回复类型错误、按钮不可用，或单文件选择器收到过多
路径，都会失败。保存待处理的文件保存请求会写入该文件。触觉反馈的 `submitted` 回复确认
已提交，而不是已实际送达；只有 `failed` 接受消息。

通知 ID 或操作未知时，通知单击失败。全局快捷键使用 `CmdOrCtrl+Shift+K` 这类加速键
语法，未注册则会失败。`open-files` 至少需要一个路径。第二次启动事件会携带接收进程的
工作目录；无头环境中的 `--open-url` 与 `--open-file` 参数也会产生各自的打开事件。电源
变更会送达所有无头文档。分享完成默认为 `cancel`，在没有显示分享界面时失败。

状态：系统请求与注册不是 `tern ctl state` 的字段；对话框、触觉反馈、通知、快捷键与
分享请使用 `system`。应用效果出现在相应的字段中，例如 `file_blocks` 与 `tabs`。

## 网页视图与拼写检查 {#web-views-and-spelling}

| 命令 | 作用 |
| --- | --- |
| `webview <selector> title <text>` | 报告嵌入式页面的标题。 |
| `webview <selector> url <URL>` | 报告其显示的地址。 |
| `webview <selector> loading <P>` | 报告从 0 到 1 的加载进度。 |
| `webview <selector> failed <message>` | 报告一次加载失败。 |
| `webview <selector> history <true\|false> <true\|false>` | 报告是否存在后退与前进历史。 |
| `webview <selector> focus on\|off` | 报告页面的键盘焦点。 |
| `webview <selector> new-window <URL>` | 报告页面请求新建窗口。 |
| `webview <selector> inspector-page <URL>` | 报告页面的 Web Inspector 以页面形式在此地址提供。 |
| `webview <selector> inspector-unavailable <message>` | 向用户报告页面的 Web Inspector 在何处，而不是将其打开。 |
| `webview <selector> security-key` | 报告引擎拒绝了页面的安全密钥或通行密钥（WebAuthn）请求。 |
| `webview <selector> media-blocked <hint>` | 报告引擎无法加载页面的音频或视频，并说明用户可采取的措施。 |
| `spelling [WORD[=GUESS,...]...]` | 把这些词精确标记为拼写错误，并可附带替换建议。 |
| `spelling off` | 关闭拼写检查。 |

网页视图的选择器是一个参数，必须匹配带有网页视图的元素。文本、URL 与失败载荷都是单个
参数。这些命令报告页面事件；它们不会导航，也不会等待真实页面。无头窗口没有页面，因此
脚本以这种方式提供它们的报告。浏览器报告没有专门的 `tern ctl state` 字段；请用 `tree`
或 `dump` 检查其工具栏。文件的网页视图会影响 `file_blocks`。`stats` 会列出嵌入的网页
视图。

拼写检查匹配词时不区分大小写。不带参数时，`spelling` 不标记任何内容。无头会话以此为
空词典启动；实时窗口用它替换平台的拼写检查器。建议出现在字段的上下文菜单中。没有
拼写词典状态字段；请检查该字段或其菜单。以下基于 `browser-toolbar` 基准：

```text
ready
browser open "example.com"
webview ".tn-pane.on .kit-web-page" url "https://example.com/"
webview ".tn-pane.on .kit-web-page" title "Example Domain"
webview ".tn-pane.on .kit-web-page" history true false
webview ".tn-pane.on .kit-web-page" loading 1
browser address
shot browser-toolbar
```

## 另见 {#see-also}

- [脚本](index.md)：运行、引号、时机与夹具。
- [控制命令](control.md)：检查、时钟与系统状态。
- [终端与面板](terminal.md)：shell 命令与提示符等待。
- [文件 block](file.md)：文件编辑与文件就绪。
- [浏览器 block](browser.md)：打开并控制浏览器 block。
- [调试](../guides/debugging.md#driving-a-window-from-a-script)。
