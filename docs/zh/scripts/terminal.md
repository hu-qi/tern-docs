# 终端与面板 {#terminal-and-panes}

这些命令驱动 shell、面板分屏、标签页以及终端的外观。可以用它们布置窗口、等待输出、
触发提醒指示器，或在不运行原程序的情况下回放某个插件 surface。

## Shell 与等待 {#shells-and-waits}

| 命令 | 作用 |
| --- | --- |
| `ready` | 等待活动标签页中每个可见的程序面板到达其 shell 提示符或退出。 |
| `git-read` | 等待聚焦面板所在目录的 git 信息读取完成。 |
| `link-read` | 等待指针下的路径完成存在性检查。 |
| `run "<command>"` | 把命令与回车写入聚焦的 shell。每个 `{fixtures}` 都会替换为文件夹具目录。 |
| `expect "<text>"` | 等待聚焦面板中某个可见终端行上出现子串。 |
| `completing` | 等待补全浮层打开。 |

`run` 给输出 1.2 秒真实时间，随后等待 100 ms 即视为完成；它不会等命令结束。关注完成
状态时，可在其后接 `expect` 或 `ready`。`expect` 不跨行搜索，也不搜索屏幕外的回滚
缓冲区。没有运行中的 shell 时 `run` 失败；没有聚焦终端时 `expect` 失败。活动标签页
为空时 `ready` 视为满足；没有聚焦面板时 `git-read` 视为满足。等待真实工作的命令在
20 秒后失败。

状态：`focused.prompt`、`focused.running`、`focused.last`、`focused.exited` 与
`focused.git` 描述 shell；`term_link` 描述悬停的链接。没有单独的补全或等待中字段。

## 面板、标签页与菜单 {#panes-tabs-and-menus}

| 命令 | 作用 |
| --- | --- |
| `split right\|down` | 把聚焦面板横向或纵向分屏。 |
| `close` | 关闭聚焦面板。 |
| `zoom` | 切换聚焦面板的缩放。 |
| `equalize` | 使活动标签页中的分屏均等。 |
| `focus left\|right\|up\|down\|next\|prev` | 聚焦相邻面板，或在面板之间循环。 |
| `resize-pane left\|right\|up\|down` | 移动分屏边界，以调整聚焦面板的大小。 |
| `tab new\|next\|prev\|close\|<n>` | 新建、循环、关闭或选择标签页；`<n>` 是从 1 开始的正整数。 |
| `rename "<name>"` | 重命名活动标签页。 |
| `palette [<query>...]` | 打开命令面板，给出参数时以该行其余内容过滤（`palette reload settings`）。 |
| `find "<query>"` | 在聚焦面板的回滚缓冲区中打开搜索。 |
| `context pane\|tab` | 打开聚焦面板的菜单或活动标签页的菜单。 |
| `layout rail\|float\|tiles\|studio` | 切换窗口布局。 |

布局名称不区分大小写。面板与标签页操作会等到可见的 shell 提示符就绪后才视为完成；
因此新打开的 shell 可能推迟下一条命令。这里的 `resize` 调整的是面板，而不是窗口
视口：`tern ctl resize W H` 参见[控制命令](control.md)。

状态：`panes` 给出终端尺寸，`focused.id` 标识焦点，`tabs` 给出标题、面板数量、活动
与缩放标志，`decks` 描述排布。`layout`、`palette`、`palette_scope`、`find` 与
`menu` 反映相应的界面。

```text
ready
split right
run "git status"
expect "On branch"
focus left
run "ls"
shot split-status
```

## 字体与窗口控件 {#fonts-and-window-controls}

| 命令 | 作用 |
| --- | --- |
| `font <px>` | 把终端字号设为非负整数，并限制在支持的范围内；跟随终端字号的界面（未设置 `ui-font-size`）也会随之变化。 |
| `ui-font-size [<px>]` | 设置界面的字号，限制方式与 `font` 相同；不带参数则重新跟随终端字号。 |
| `font-family ["<families>"]` | 设置终端常规字体族；不带参数或传空字符串则恢复内置字体。 |
| `font-family bold\|italic\|bold-italic "<families>"` | 设置某种样式的终端字体；空字符串则继承常规字体族。 |
| `font-weight <n>` | 设置终端字重，限制在 100–900。 |
| `adjust-cell-height <px>\|<n>%` | 给终端行高增加整数像素或有限百分比。 |
| `adjust-cell-height ""` | 重置行高调整。 |
| `adjust-cell-width <px>\|<n>%` | 给终端单元格宽度增加整数像素或有限百分比；字形保持原大小。`""` 重置该调整。 |
| `font-thicken on\|off [<strength>]` | 开启或关闭文字加粗（macOS）；带参数时按 0 到 255 的强度开启。 |
| `padding <x> [<y>]` | 设置终端文本与其 block 边缘之间的横向与纵向间距（整数 px，最大 40）；只给一个值则同时设置两者。 |
| `ui-font ["<families>"]` | 设置 UI 字体族；不带参数或传空字符串则恢复内置字体。 |
| `code-font ["<families>"]` | 设置代码字体族；不带参数或传空字符串则恢复内置字体。 |
| `program-icon <program> [<icon>]` | 让 Program icons 设置（`program_icons`）为某个程序键或命令名（`codex`、`nvim`）指定该图标（`provider-openai`）；不带图标则移除该条目。 |
| `decorations system\|lights\|buttons` | 选择系统窗口控件、Tern 红绿灯按钮或标题栏按钮。 |
| `glass <opacity>` | 设置窗口玻璃效果的透明度（0–100 %），并让页面在无头截图中保持半透明，其 PNG 因此带有桌面条件下能透出的 alpha。 |

字体族列表要作为一个参数加引号，例如 `font-family "A, B"`。带样式的形式同时需要样式
和字体族字符串。像素调整接受正负号（`+3`、`-1`）；百分比也接受小数（`-12.5%`）。
得到的行高会取整，并限制在未调整高度的 0.5 倍到 3 倍之间。字号与字重接受无符号整数。

除此之外，无头帧是不透明的，背后没有桌面；把 `glass` 截图合成到壁纸之上，即可呈现
桌面上的窗口效果。

状态：`font`、`ui_font`、`font_family`、`face` 与 `faces` 给出终端与界面的字号，以及
请求的与最终解析出的字体族。`csd` 表示客户端装饰，但无法区分红绿灯按钮与普通按钮。
`opacity` 是玻璃效果的透明度。字重、行高调整以及 UI/代码字体族设置没有专门的顶层
状态字段。

## 主题、滚动与复制 {#themes-scrolling-and-copying}

| 命令 | 作用 |
| --- | --- |
| `theme [dark\|light] "<name>"` | 为具名主题保留其原本的外观，或将其用于显式指定的外观。 |
| `themes ["<name>"]` | 打开主题选择器；给出名称时预览该主题。 |
| `scroll <lines>` | 把聚焦终端按带符号的整数行数向后滚动；负值朝最新输出的一端移动。 |
| `copy` | 复制聚焦面板的选中内容，并显示复制反馈。 |

`theme` 的单个参数总是主题名称，即使写的是 `dark` 或 `light`。更改一种外观的主题
不会影响另一种外观的选择。未知主题名称会导致失败。`themes` 带多个参数时打开选择器
但不选中任何名称；`copy` 忽略参数。

内联 surface 随终端一起滚动。对于独立滚动的 surface 遮盖层或浮层列表，请先
`move X Y`，再 `wheel DX DY`。没有聚焦面板时 `scroll` 会失败；不含终端的面板不会
滚动。没有焦点时 `copy` 不做任何事。

状态：`theme_dark`、`theme_light`、`theme_preview` 与 `theme` 显示主题选择与预览。
`focused.selection` 给出选中的终端文本；没有顶层的滚动位置或剪贴板字段。

## 提醒与总览 {#attention-and-overview}

| 命令 | 作用 |
| --- | --- |
| `alert bell ["<detail>"]` | 在聚焦面板上记录一次响铃；省略或留空 detail 时使用其标签。 |
| `alert done <status> "<command>" [<seconds>]` | 记录命令完成，带符号的退出状态与可选的非负整数秒数。 |
| `alert exited <status>` | 以带符号的状态记录程序退出。 |
| `alert waiting "<message>"` | 记录一次请求提醒。 |
| `alert agent-done` | 使用聚焦面板的标签记录一次 agent 完成。 |
| `inbox` | 打开提醒收件箱。 |
| `inbox go` | 前往选中条目所在的面板。 |
| `inbox clear` | 清空所有条目。 |
| `inbox close` | 关闭收件箱。 |
| `peek [strip\|mission\|close]` | 打开标签条或 Mission Control，或返回终端。默认为 `strip`。 |
| `park` | 把聚焦面板停放到当前会话的停放面板中。 |
| `park hand` | 以静止状态打开停放面板，并选中第一张卡片。 |
| `park pick <n>` | 从 1 开始计数，选中已打开的停放面板中的第 `n` 张卡片。 |
| `park deal` | 把选中的卡片取回到聚焦面板旁（停放面板已关闭时取回第一张）。 |
| `park close` | 关闭静止状态的停放面板。 |
| `park at <percent>` | 把卡片堆停在底边上按百分比定位的位置（50 为正中），效果等同把它滑到那里。 |
| `park size <percent>` | 把卡片堆缩放为其自身大小的 `percent`（50 到 200），效果等同用副键按住卡片上下拖动。 |
| `melt [<progress>]` | 关闭当前会话，并把关闭动效播放到 0–1 的进度。默认为 1。 |

`alert` 需要聚焦的面板，且不会运行所命名的命令，也不会退出其程序。收件箱已关闭或
没有选中项时 `inbox go` 会失败。`peek` 以静止状态打开，不做过渡动画，并等待其总览
截图就绪。没有聚焦面板时 `park` 失败；没有停放内容时 `park hand` 与 `park deal`
失败；`park pick` 超出最后一张卡片时失败；`park at` 超过 100 时失败；`park size`
超出 50 到 200 时失败；这些命令都会等待卡片图像完成截取。`melt 0` 仍会关闭会话；
该参数只控制动效的时间线。进度取整到千分之一，启用减少动态效果时以淡出代替融化。

窗口失去焦点时（`window-focus off`），`alert waiting` 条目还会发出 id 为 `pane:<id>`
的系统通知；开启 `agents.notify_turn_finished`（设置 › Agents › Notifications）后，
`alert finished` 与 `alert failed` 同样如此；`system` 会在 `notifications` 下列出
它。`notification-click pane:<id>` 会把 Tern 前置到该面板：`system` 的日志出现
`activate-app`，且 `focused` 即为该面板。

状态：`inbox` 给出条目与选中项，`tabs[].alert` 给出标签页的提醒，`peek` 描述总览
层级与卡片，`park` 列出停放卡片及其堆叠与状态、卡片堆的位置、大小（`size`，相对
自身，0.5–2）、显示多少张卡片（`cards`，最多六张）与省略的卡片（`more`），以及
已展开的手牌，`melt` 给出当前动效与进度。`sessions` 反映已关闭的会话。

## 输出与 surface 回放 {#output-and-surface-replay}

| 命令 | 作用 |
| --- | --- |
| `feed "<path>"` | 把文本夹具作为终端输出打印到聚焦面板中。 |
| `surface-play "<path>" [from <frame>] [until <frame>] [paced [<times>]]` | 回放 JSON-lines 的 surface 录制，可选按帧范围限定，或按录制时的节奏播放。 |

这些命令先按给定路径直接读取已存在的文件，否则在夹具根目录下解析该路径。`feed` 以
UTF-8 读取，把行尾转换为 CR LF，去掉最后一个换行，并把字面量 `\e` 与 `\a` 展开为
Escape 与 Bell。两个命令在需要时会用静默的回放程序重启聚焦面板，然后等待它开始
监听；没有焦点或文件无法读取时失败。WebAssembly 版本不提供回放。

帧是无符号序号（`3`），或 surface ID 加序号（`chat#3`）。`from` 不含指定的帧，
并要求聚焦面板中已有回放；`until` 包含该帧。选项可以任意顺序出现，重复的选项会
替换先前的值。录制 JSON 无效时会失败并给出行号。

不带 `paced` 时，回放会一次性灌入输出。`paced` 默认为 1×；`paced 2` 以两倍速播放。
倍率必须是有限正数。按节奏回放不会等待最后一条消息就返回：用 `wait MS` 推进文档
时间。同一面板中上一条按节奏录制仍在播放时，再启动一条会失败；关闭其面板即可停止
播放。

状态通过 `focused` 与 `panes` 给出结果面板，但没有录制进度字段。用 `tree` 或 `dump`
检查渲染出的 surface。

```text
ready
surface-play "goldens/fixtures/omp-chat.jsonl" until 3
wait 300
shot chat
```

## 夹具插件 {#fixture-plugins}

| 命令 | 作用 |
| --- | --- |
| `plugins fixtures` | 加载源码树的测试插件，并重新加载它们的 host 与 window 入口。 |
| `plugins run <action>` | 运行具名键位映射动作，包括 `plugin.hello.ask` 之类的插件动作。 |
| `plugins expect "<text>"` | 等待聚焦终端所属 surface 中出现文本。 |

夹具插件位于 `crates/plugins/fixtures`。加载它们需要夹具根目录；窗口已连接到会话
守护进程时加载会失败，因为后者的插件是单独管理的。该命令会从保存的设置恢复插件的
启用/禁用选择，在无头运行中也是如此。动作语法无效时会失败。`plugins expect` 等待的
是 surface 内容而不是终端行，文本始终未出现时会在 20 秒后超时。

没有专门的插件状态字段。用 `tree` 或 `dump` 检查渲染出的 surface，并用
`plugins expect` 等待其内容。

## 另见 {#see-also}

- [脚本](index.md)：运行、引号、夹具与计时。
- [Harness 命令](harness.md)：输入、截图与文档时间。
- [标签页与导航](navigation.md)：导航与面板布局。
- [会话与 block](sessions.md)：会话与 block 操作。
- [调试](../guides/debugging.md)：从脚本驱动插件。
- [命令行](../reference/cli.md)：管理已安装的插件。
