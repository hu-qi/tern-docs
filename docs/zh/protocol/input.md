# 输入与事件 {#input-and-events}

按键一如既往地以 pty 输入的形式到达程序。指针在 surface 中执行的操作，以及面板中发生的变化，则以事件的形式返回。

## 按键 {#keys}

按键以 pty 输入的形式到达程序：kitty 键盘协议、括号粘贴。获得焦点的 `editor` 或 `input`（`focus` op）会显示 Tern 的光标，但文本模型由程序负责：需要用 `text` 或 `splice` op 以及新的 `cursor` 来应答按键。IME 组字发生在 Tern 的隐藏文本区，以预编辑文本绘制在字段光标处，并作为键入文本提交到 pty。

例外是下面的原生编辑：作用于 Tern 选区的按键会变为 `edit` 事件，撤销键变为 `undo` 事件。另外，在内联 surface 中，当焦点是位于 `dock` 的 `editor`（聊天应用的输入框）且其光标处没有锚定的 `overlay` 时，普通的 PgUp 与 PgDn 会翻动面板，正如聊天应用的消息输入框翻动其历史：`main` 随面板滚动，因此这类按键在那里永远不会到达程序。带 `typeahead` 的字段会暂存键入内容，直到程序能够读取它（[预输入](#typeahead)）。

## 原生编辑 {#native-editing}

当 `hello` 中声明了 `edit` 程序特性时，Tern 会在 `editor` 与 `input` 字段中维护自己的选区，如同 GUI 文本字段那样，除非该字段带有 `mode`（Vim 模式）或是 `readonly`。用户可以关闭此行为（Settings › Terminal › Native composer editing）。对于没有 `edit` 的程序，所有按键都归程序所有，因为作用于 Tern 选区的按键若发给程序，只会变成一个被它丢弃的事件。

- ⇧ 加方向键（按词使用 ⇧⌥ 或 ⇧⌃ ←/→，按行使用 ⇧⌘ ←/→ 或 ⇧Home/End，按整段文本使用 ⇧⌘ ↑/↓），或者拖动、双击、三击可选中；⌘A 全选。在 PC 键盘上，Ctrl 相当于 ⌘，与其文本字段的习惯一致（Ctrl+A、Ctrl+C、Ctrl+X、Ctrl+V、Ctrl+⇧←/→、Ctrl+⇧Home/End）；Alt 与 Windows/Super 组合键仍归程序与应用所有。
- 在文本改变之前，Tern 绘制自己的选区，而不绘制程序的 `cursor` 与 `anchor`。存在选区时，键入、粘贴、IME 提交、⌫、⌦（及其按词、按行变体）以及 ⌘X 或 ⌃X 会替换选区，⌘C 在本地复制选区，普通方向键会取消选区。没有选区时，只有下面列出的选择按键与按绘制行移动的按键归 Tern：⌘C、⌘X、⌃X、删除键，以及 PC 键盘上的 Ctrl+V 仍归程序。空字段没有可选内容，因此其中所有按键都归程序（撤销除外）。
- 在已聚焦的字段中点击会放置光标：即 `from == to` 的 `edit` 事件，且仅在光标移动时发送。在未聚焦的字段中点击则发送 `focus`（[事件](#events)）。
- 只有 Tern 知道文本在哪里软换行，因此单独按 ↑ 或 ↓ 会把光标移到上方或下方的绘制行（x 坐标取连续按键起始处），⌘← 或 ⌘→（Home、End）会移到绘制行的行首或行尾。这些按键都以一个 `edit` 事件发给程序，而不会以按键形式发送。
- 除此之外，所有按键一如既往归程序：在首个绘制行按 ↑、在最后一个绘制行按 ↓（程序的历史记录），光标处锚定的 `overlay` 打开时按 ↑ 与 ↓（其列表）。在 PC 键盘上，没有选区时，Ctrl+Home/End（文本开头或结尾）与 Ctrl+Backspace/Delete 也归程序。
- 在标记为 `typo` 的拼写错误上，上下文菜单会优先列出平台拼写检查器给出的候选；选择其一会发送 `edit`。

**撤销。** 若同时具备 `undo` 特性，在原生编辑的字段中按 ⌘Z 或 ⌃Z（PC 键盘为 Ctrl+Z），会以一个 `undo` 事件而非按键发给程序，无论有无选区、字段是否为空皆如此，因此清空的草稿可以恢复。历史记录由程序维护，每个 `edit` 事件为一步。在 Vim 模式下、关闭原生编辑时，或没有 `undo` 时，⌃Z 仍归程序。

**发送。** 具备 `send` 特性时，Tern 可以把提示词原子地提交到程序的输入框（给 agent 的初始提示词、Carly 向它提问）：这是一个 `send` 事件，而不是一次粘贴加回车。字段只在报告 `sendable:true`（且不是 `readonly`、`disabled` 或 `hidden`）时才接受，这意味着其所有者、提交处理程序以及它们所依赖的条件都已就绪。可写文本与焦点是两回事：程序启动期间，已聚焦、可编辑的字段仍可能是 `sendable:false`。就绪时发送一帧设置 `sendable:true`，即使其他内容没有变化；在此之前 Tern 会暂存其提示词。

**回复。** 当已聚焦的 `editor` 位于 `dock`（聊天应用的输入框）时，在面板内的选区上打开上下文菜单会提供 Reply with Selection。它把选中文本作为 Markdown 引用粘贴进来（每行前加 `> `，空行只加 `>`，其后再加一个空行），与任何粘贴到达程序的方式相同：括号粘贴，或作为模式为 5522 的 paste 事件。不会发送任何内容；该引用是程序可编辑、可撤销的草稿，面板接管按键，以便用户在其下方输入回复。

## 预输入 {#typeahead}

尚不能读取输入的程序（仍在启动、事件循环繁忙）可以在其已聚焦的 `editor` 或 `input` 上设置 `typeahead: true`，如同终端的行规程在程序读取之前先回显键入内容。设置期间，Tern 会把键入该字段的内容保留下来，而不写入 pty，并在程序的 `cursor` 处绘制，仿佛这些文本已在程序中：键入的文本与 IME 提交（不含换行或其他控制字符），以及对所保留文本按 ⌫。程序重新读取按键后即清除该属性：Tern 会把保留的内容按键入顺序写入 pty，并继续绘制，直到某帧改变字段的 `text`。

其他任何按键（回车、方向键、快捷键、粘贴）会在保留内容之后照常发往 pty：程序按键入顺序读取两者。该按键可能消费掉文本（回车发送草稿）并保持 `text` 不变，因此先于某个按键写入的文本会持续绘制，直到某帧改变 `text` 或清除该属性。当 Tern 保留文本时，原生编辑让位。带 `mode` 或 `readonly` 的字段不保留任何内容；字段保留的内容会在节点或 surface 消失时丢失。不支持 typeahead 的 Tern 会忽略该属性：按键按键入原样到达 pty。

## 指针动作 {#pointer-actions}

通用的 `actions` 属性说明指针在节点上执行什么操作。它是一个按手势给出动作的对象，`{"click": act, "dblclick": act, "menu": [act…]}`，每个键都可选：

```json
{"id": "row", "k": "text", "p": {"text": "build.log",
  "actions": {"click": "open-log", "dblclick": "copy", "menu": ["rerun", "sort=name"]}}}
```

| 动作 | 运行位置 | 事件 |
| --- | --- | --- |
| `toggle` | Tern 立即折叠或展开该节点（可折叠的 `card`、`section`、`tool`、`agent`、`checklist`） | `{"ev":"toggle","id","collapsed","key?"}` |
| `copy` | Tern 复制节点的文本（`md` 取 Markdown 源码，`code`、`ansi` 与 `text` 取原始文本，`block` 取原始输出，有 `href` 时取 `href`），闪烁该节点并显示 Copied | 无 |
| `open` | Tern 打开节点的 `href` 或 `path` | 无 |
| `zoom` | Tern 在其查看器中将 `image` 放大显示，可依次浏览旁边的图片 | 无 |
| `select` | 程序 | `{"ev":"select","id","item","values?"}` |
| `activate` | 程序 | `{"ev":"activate","id","item","values?"}` |
| 其他任何名称 | 程序 | `{"ev":"action","id","act","value?","item?","mods?","checked?","values?"}` |

- `click` 与 `dblclick` 会给节点加上 `.sf-act` 和手形指针光标。用于打开链接的点击（⌘-点击，或在 Settings › General › Links 设为普通点击即打开时，对行内链接的普通点击）会打开链接，而不会运行 `click`。
- `menu` 列出上下文菜单项，标签由动作名生成（`open-file` 显示为 Open file），除非列表本身指定了 `copy`，否则会附加 Tern 的 Copy。条目也可以是 `"-"`（分隔线）、`{"header"}`（分区标题），或带有 [`menu`](../elements/lists.md#menu) 行各字段的条目对象：`id`（动作）、`label`、`icon`、`keys`、`detail`、`checked`、`radio`、`disabled`、`danger` 与 `items`（子菜单）。选中某项会像点击一样运行该动作，但不带 `mods`；勾选行或单选行的动作还会带上 `checked`，即其新状态。
- `toggle` 的 `key` 仍是节点自身的 `key` 属性（若有）；事件不会用父节点对其加以限定。Tern 按该 key 在节点的同级之间记住本地折叠状态，而不是按整个 surface 记住。一次 `del` 之后紧跟一个 `add`，只要新节点 id 不同而同一父节点下的 key 相同，折叠状态就会保留；同一 key 在另一个父节点下则拥有独立状态。没有 key 时，本地状态使用节点的 id。
- 对于 `list` 中 `item` 上的 `select` 与 `activate`，`id` 是列表，`item` 是该条目；对于 `table` 行，`id` 是表格，`item` 是行的 `id`；对于下面其他会选中某项的类型（nav 条目、面包屑、预设、帧、建议、问题），`id` 是节点，`item` 是被选中的内容；对于其他任何节点，两者都是节点 id。
- `action` 上的 `item` 指明按钮单元格或行 `menu` 条目所作用的表格行、选中某行所属的 `menubar` 菜单，或 `questions` 步骤留下的问题；其他动作没有该字段。
- 带 `=` 的自定义名称会拆分为 `act` 与 `value`（`"sort=name"`）。`mods` 按 `shift`、`ctrl`、`alt`、`meta` 的顺序列出按住的修饰键（⌘ 为 `meta`），没有修饰键时不出现。
- 当节点位于 `el` 的 `form` 中时会带有 `values`（[表单值](#form-values)）。

悬停、滚动、文本选择、工具提示与上下文菜单由 Tern 自行处理。某些类型无需 `actions` 属性也会发送自己的事件：

| 类型 | 事件 |
| --- | --- |
| `list` 条目 | 单击时为 `select`，双击时为 `activate`，`id` 为列表（[列表](../elements/lists.md#item)）；条目自身的 `click` 或 `dblclick` 动作会替换对应的那个 |
| 带 `selectable` 的 `table` | 单击行时为 `select`，双击时为 `activate`，`id` 为表格，`item` 为该行（[数据](../elements/data.md#table)） |
| 带 `sortable` 的 `table` | 点击表头时为 `action` `sort`，`value` 为 `{"col","dir"}`（[数据](../elements/data.md#table)） |
| 带 `multi` 的 `table` | `change`，`value` 为选中的行 id；其 `bar` 按钮触发 `action`，`value` 为选中的 id（[数据](../elements/data.md#table)） |
| `table` 按钮单元格、行 `menu` | `action`，`act` 为单元格的 `act` 或菜单条目，`item` 为该行 |
| `button` | `action`，`act` 为其 `actions.click`，否则为 `"click"`（[输入与按钮](../elements/input.md#button)） |
| `select` | `change`，`value` 为选中的选项；指针打开或关闭其菜单时为带 `open` 的 `toggle`（[输入与按钮](../elements/input.md#select)） |
| `switch` | `change`，`value` 为新状态，即 `true` 或 `false`（[输入与按钮](../elements/input.md#switch)） |
| `slider` | 释放时为 `change`，`value` 为数值，区间则为 `[lo, hi]`（[输入与按钮](../elements/input.md#slider)） |
| `otp` | `action` `focus`，`value` 为光标移入的单元格（[输入与按钮](../elements/input.md#otp)） |
| `calendar` | `change`，`value` 为 `"YYYY-MM-DD"` 形式的日期或 `[from, to]` 区间；`select`，`item` 为预设的 id；`action` `month`，`value` 为 `"YYYY-MM"`（[输入与按钮](../elements/input.md#calendar)） |
| `date` | 带 `collapsed` 的 `toggle`（打开时为 `false`），之后是与 `calendar` 相同的 `change` 与 `action` `month`（[输入与按钮](../elements/input.md#date)） |
| `tabs` | `select`，`item` 为标签页的 id（[标签页](../elements/lists.md#tabs)） |
| `menu` | `action`，`act` 为行的 id，勾选行或单选行还带 `checked`；带 `open` 的 `toggle`（[菜单](../elements/lists.md#menu)） |
| `menubar` | `action`，`act` 为行的 id，`item` 为菜单的 id，另有 `checked?`；带 `item`（菜单的 id）与 `open` 的 `toggle`（[菜单](../elements/lists.md#menubar)） |
| `nav` | `select`，`item` 为条目或子条目（[导航](../elements/lists.md#nav)） |
| `breadcrumb` | `select`，`item` 为面包屑（[导航](../elements/lists.md#breadcrumb)） |
| `pager` | `change`，`value` 为页码（从 1 开始）；`action` `more`（[导航](../elements/lists.md#pager)） |
| `tree` | `toggle`，`key` 为条目（[数据](../elements/data.md#tree)） |
| `split` | 释放时为 `change`，`value` 为每个面板的占比，合计为 1（[布局](../elements/layout.md#split)） |
| `carousel` | `change`，`value` 为当前显示的幻灯片索引（[数据](../elements/data.md#carousel)） |
| `attachment` | `action`，`act` 为 `remove`、`retry` 或其 `actions` 之一（[数据](../elements/data.md#attachment)） |
| `picker` | `select`、`activate` 与 `action`（[选择器事件](../elements/lists.md#events)） |
| `prefs` | `select`、`activate`、`action`、`focus`，以及带 `item` 与 `value` 的 `change`（[prefs](../elements/work.md#prefs)） |
| `checklist`（hud） | 其 pill 打开或关闭时为 `activate`，`item` 为 `"hud"`（[checklist](../elements/work.md#checklist)） |
| 带 `confirm` 的 `tool` | `action` `allow`、`deny` 或 `always`，有作用域时 `value` 为该作用域（[tool](../elements/work.md#tool)） |
| `trace` | 带 `open` 的 `toggle`，`item` 为该行的 id（头部没有）（[trace](../elements/work.md#trace)） |
| `message` | `change`，`value` 为表情回应标签的文本，另有 `on`；来自其操作按钮的 `action`（[message](../elements/work.md#message)） |
| `suggestions` | `activate`，`item` 为条目的 `id`，否则为条目文本（[suggestions](../elements/work.md#suggestions)） |
| `questions` | `change`，`item` 为问题，`value` 为其答案；`action` `next`、`back` 或 `skip`，带 `item`，`submit` 的 `value` 为所有答案；在 `list` 中为带 `item` 的 `select`（[questions](../elements/work.md#questions)） |
| `stacktrace` | `select` 与 `activate`，`item` 为帧的索引（[stacktrace](../elements/work.md#stacktrace)） |
| `el` 复选框、单选框 | `change`（[HTML 元素](../elements/el.md#the-change-event)） |
| `editor`、`input` | `focus`、`edit`、`undo`（见上文） |
| `input` 附加按钮 | `action` `clear`、`inc` 或 `dec`，或所附加按钮的 act（[输入与按钮](../elements/input.md#addons)） |

## 事件 {#events}

终端 → 程序的每条消息都是一个 `e` 事件，即 `ESC _ tsp;e;{…} ESC \`
（通过 Windows ConPTY 时为 OSC 877，参见[传输](transport.md#windows)）。关于某个 surface 的事件以 `sf` 携带其 id：下文除 `theme`、`motion` 以及应答 `adopt` 的 `gone` 之外的每个事件都如此；`error` 在被拒绝的消息指定了 surface 时才带上它。

| 事件 | 负载 | 时机 |
| --- | --- | --- |
| `ack` | `s` | 已应用*并已绘制*的最高帧；每个显示帧最多一个（[流量控制](operations.md#flow-control)）。 |
| `resize` | `cols`、`cell`（`{"w","h"}`）、`visible` | 面板的活动 surface 首次绘制时，或面板的列宽、单元格尺寸发生变化时。在多个窗口（另一台电脑、手机、浏览器）中显示的面板只有一个宽度，即用户最后操作的窗口的宽度，且只报告该宽度；最先的那个窗口此后可能只在宽度发生变化时才上报，在此之前以 `hello` 应答中的 `cols` 为准。仅在决定 `rows` 与 ANSI 宽度时需要。 |
| `theme` | `dark` | 外观发生切换。 |
| `motion` | `reduce` | 「减弱动态效果」被切换。 |
| `visible` | `visible` | 面板被隐藏（切换到其他标签页）或重新显示：此时应暂停开销大的工作。 |
| `toggle`、`select`、`activate`、`action` | 见上文（`item` 用于列表条目、标签页、表格行以及上述类型所选中的内容；`checked` 来自勾选行或单选菜单行；来自 `select`、`menu`、`menubar` 或 `trace` 的 `toggle` 携带 `open` 而非 `collapsed`） | 一次用户操作。 |
| `change` | `id`、`value`、`checked`、`name?`、`values?`；来自 `prefs` 时：`id`、`item`、`value`；来自上述其他类型时：`id`、`value`（`questions` 还会带 `item`，`message` 还会带 `on`） | 用户切换了 `el` 复选框或单选框（[HTML 元素](../elements/el.md#the-change-event)）、修改了 `prefs` 行的值，或改变了某个控件类型的值（下拉选择、开关、滑块、日历或日期、分页器的页码、分割面板的尺寸、轮播的幻灯片、`multi` 表格的选中项、表情回应、答案）。 |
| `focus` | `id` | 一次点击请求把按键交给该节点：发生在并非当前焦点的 `editor` 或 `input`（且不是 `readonly`）中，或发生在 `prefs` 节点中而焦点位于其外部的字段时。请把焦点移过去（并用 `focus` op 应答），或忽略它：模态 overlay 会保留按键。 |
| `edit` | `id`、`from`、`to`、`text`、`cursor`、`len` | 原生编辑：用 `text` 替换字段 `id` 文本中的 UTF-16 范围 `[from, to)`（一步撤销），然后把光标放到 `cursor`。`from == to` 且 `text` 为空时只移动光标。`len` 是 Tern 所见的文本长度：如果自那之后程序文本已改变（按键还在途中），请忽略该事件。仅在具备 `edit` 特性时出现。 |
| `undo` | `id` | 通过程序自身的撤销历史撤销字段 `id` 的最近一次改动；没有可撤销内容时什么也不做。它与前后的按键按顺序写入。仅在具备 `undo` 特性时出现。 |
| `send` | `id`、`text` | 通过输入框 `id` 的常规提交路径提交 `text`，保留多行文本、命令与附件。只会发给具备 `send` 特性的程序中存活、可编辑且报告 `sendable:true` 的字段；其他情况一律丢弃。 |
| `error` | `s`、`op`、`msg`；或 `msg`（已知时带 `s`）；或 `sheet`、`msg`；或 `id`、`msg` | 帧 `s` 中被拒绝的 op（`op` 为其索引）；被拒绝的消息或被丢弃的数据块；来自视图的样式表解析错误（`sheet`，各条消息以 `; ` 连接），或标签未知的 `el`（`id`）。 |
| `gone` | `ids` | Tern 因保留预算丢弃了这些节点；丢弃了锚定行已离开的 surface（滚出回滚缓冲区、回滚缓冲区被清空、退出备用屏幕），此时 `ids` 为该 surface 自身的 id；或 `adopt` 未找到任何内容。请停止引用它们。 |

## 表单值 {#form-values}

当 `action`、`select`、`activate` 或 `change` 事件的节点位于 `el` 的 `form` 中时，事件会携带 `values`：该表单中每个启用且具名的控件在当时的值。单选组给出被选中单选按钮的 `value`（没有选中时为 `null`），单独的复选框给出 `true` 或 `false`，同名复选框给出按文档顺序排列的选中值数组。提交表单的那次点击会携带所选项，因此无需再询问：

```json
{"ev":"action","sf":"pick","id":"go","act":"submit","values":{"size":"l","notify":true,"tags":["a","c"]}}
```

算法与一个完整示例见 [HTML 元素](../elements/el.md#form-values)。

## 仅发给正在监听的程序 {#only-to-a-listening-program}

终端写入 pty 的任何内容对 shell 而言都是键入文本，因此 Tern 只发送程序会读取的内容：

- Tern 自身产生的事件（`ack`、`resize`、`visible`、`theme`、`motion`、指针与视图事件）只在面板中至少有一个 surface 打开期间发出；指定了某个 surface 的事件只在该 surface 打开期间发出。
- 以 `listen:false` 打开的 surface 什么也听不到：不会有与它相关的 ack、事件或错误，且在其 `o` 之后不会收到任何应答，直到程序下一次 `q` 或监听态的 `o`。
- 对程序所发内容的应答（`q` 的回复、`error`、`gone`）会发出，除非已知程序已经结束：在 shell 提示符出现之后、面板进程退出之后，或 RIS 之后，直到有内容发起询问（`q`）或打开 surface（`o`）。迟到的 `f`，或提示符已丢弃的 surface 的 `x`，不会得到应答。用 `x` 关闭自身 surface 的程序仍会收到关于其错误的应答，因为它可能仍在读取（[离开](surfaces.md#open-and-close)）。
