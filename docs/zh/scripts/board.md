# Board Block {#board-blocks}

`board` 命令用于打开 Markdown 任务板，并驱动其中的卡片、泳道、行内编辑器与菜单。
用它们来演练任务板工作流、捕获任务板或列表视图，以及检查任务板如何重新加载其文件
被做的改动。

## 打开与重载 {#open-and-reload}

| 命令 | 作用 |
| --- | --- |
| `board fixture <name>` | 把任务板 fixture 复制到一个新的临时项目，并在聚焦面板旁打开它。 |
| `board new` | 打开一个没有任务文件的新临时项目。 |
| `board open <path>` | 在聚焦面板旁打开一个任务文件。 |
| `board write "<markdown>"` | 在磁盘上替换聚焦任务板的文件，然后等待任务板重新加载该内容。 |
| `board wait` | 等待聚焦任务板读完其文件。 |

fixture 来自 `crates/tern/goldens/fixtures/board/<name>.md`。每个 fixture 会被
复制到一个以该 fixture 命名的临时项目中的 `TODO.md`；再次打开它会重置该副本。
`board new` 也会重置它的临时项目。它起始于 Todo、Doing 与 Done 三条泳道；
提交第一张卡片会创建 `TODO.md`。新打开的任务板使用任务板视图并显示已完成的卡片。

打开、`write` 与 `wait` 会等待真实的文件工作，受脚本 20 秒超时约束，然后稳定
350 ms。`wait` 检查的是初始读取已经完成，而不是之后的外部编辑已经到达。`write`
检查所显示的磁盘内容与当前文件一致，或任务板在一次行内编辑或拖动期间看到了该变更
（结束时它与该次编辑一起显示）。在其 Markdown 参数中用 `\n` 表示换行。fixture 复制
与文件写入的错误会让命令失败；始终无法到达所需状态的读取会超时。

`tern ctl state` 在 `board_blocks[]` 中报告每个任务板：`path`、`phase`
（`loading`、`ready` 或 `failed`）、`exists`、`open` 与 `done`，以及它的
泳道与卡片。新建且未保存的任务板其 `exists: false`。

## 视图、选择与菜单 {#view-selection-and-menus}

| 命令 | 作用 |
| --- | --- |
| `board view board\|list` | 设置卡片列视图或章节列表视图。 |
| `board hide-done on\|off` | 隐藏或显示已完成的卡片。 |
| `board select "<text>"` | 选中标题包含该文本的第一张卡片。 |
| `board lane <n>` | 选中一条泳道并清除已选中的卡片。 |
| `board filter ["<text>"]` | 设置过滤器；不给文本即清除。 |
| `board fold <n>` | 在列表视图中折叠或展开某条泳道的章节。 |
| `board menu` | 打开已选中卡片的菜单。 |
| `board menu lane` | 打开当前泳道的菜单。 |

泳道编号从 0 开始。选择使用区分大小写的子串，按文件顺序搜索泳道与卡片，而不只是
当前显示的卡片。没有匹配项、泳道不存在，或在没有选中卡片时打开卡片菜单都会失败。
`fold` 即使任务板视图处于活动状态也会保存折叠状态。

这些命令作用于聚焦的任务板，并稳定 350 ms。除打开之外的命令在没有任务板聚焦时
失败；任务板视图缺失同样会失败。这一组命令没有仅限桌面端或仅限无头端的限制。

状态字段为 `view`、`hide_done`、`cursor`（选中的标题）、`lane`、
`filter` 与 `lanes[].folded`。每条泳道还报告 `title`、`complete`、
`shown` 与 `cards`（每张卡片的 `text` 与 `done`）。菜单内容可用控制命令
`menus` 检查。

## 行内编辑与拖动 {#inline-editing-and-dragging}

| 命令 | 作用 |
| --- | --- |
| `board type ["<text>"]` | 替换当前行内编辑器的文本；不给文本即清空。 |
| `board commit` | 提交当前的行内编辑，类似 Enter。 |
| `board drag <lane> <slot> [hold] "<card>"` | 把标题包含该文本的第一张卡片拖到目标泳道与位置。 |

用下面的某个任务板操作开始一次行内编辑。当没有行内编辑在进行时，`type` 与
`commit` 会失败；它们稳定 350 ms，而不是等待单独的磁盘读取条件。

拖动的泳道与位置编号从 0 开始。位置按目标中已显示的卡片计数，不含被拖动的卡片。
超出最后一张卡片的位置会把它追加到末尾。不带 `hold` 时，拖动会放下卡片；带 `hold`
时，卡片保持抬起以便截图。卡片缺失、渲染出的卡片缺失或泳道不存在都会失败。拖动稳定
350 ms。从完成泳道移入或移出会更新卡片的完成状态。

状态提供 `editing`、`dragging`、结果中的 `lanes[].cards`，以及
`can_undo` / `can_redo`。

## 任务板操作 {#board-actions}

`board key <id>` 直接调用某个操作：使用下面的标识符，而不是物理按键名或带
`board.` 前缀的写法。未知标识符会失败。操作稳定 350 ms。需要选中卡片的操作通常
在没有选中卡片时不做任何事；不可用的撤销／重做，或在边缘处的移动，同样不做任何事。

| 命令 | 作用 |
| --- | --- |
| `board key up\|down` | 选中上方或下方的卡片。 |
| `board key left\|right` | 选中上一条或下一条泳道中的卡片。 |
| `board key first\|last` | 选中第一张或最后一张卡片。 |
| `board key move_up\|move_down` | 在其泳道内移动选中的卡片。 |
| `board key move_left\|move_right` | 把选中的卡片移到上一条或下一条泳道。 |
| `board key toggle` | 把选中的卡片标记为完成或重新标记为未完成。 |
| `board key edit` | 开始编辑选中卡片的标题。 |
| `board key new_below\|new_above` | 在选中项下方或上方，或在当前泳道中新建一张卡片。 |
| `board key delete` | 删除选中的卡片。 |
| `board key undo\|redo` | 撤销或重做一次任务板变更。 |
| `board key details` | 折叠或展开选中卡片的备注与子任务面板。 |
| `board key filter` | 聚焦过滤器字段。 |
| `board key switch_view` | 在任务板视图与列表视图之间切换。 |
| `board key hide_done` | 切换是否隐藏已完成的卡片。 |
| `board key clear` | 清除详情、过滤器或选择。 |
| `board key new_lane` | 在当前泳道之后新建一条泳道。 |
| `board key rename_lane` | 开始编辑当前泳道的标题。 |
| `board key move_lane_left\|move_lane_right` | 把当前泳道向左或向右移动。 |
| `board key delete_lane` | 删除当前泳道。 |
| `board key done_lane` | 切换当前泳道是否为完成泳道。 |
| `board key open_markdown` | 在任务板旁的一个文件 block 中打开该任务板的文件。 |

在新建或重命名卡片、泳道的操作之后使用 `board type` 与 `board commit`。操作结果
出现在 `board_blocks[]` 里的 `cursor`、`lane`、`editing`、
`details`、`view`、`hide_done`、`filter`、`done_lane`、`lanes`、`can_undo`
与 `can_redo` 中。`open_markdown` 会聚焦一个文件 block；在发送更多任务板命令之前
要先重新聚焦任务板。

## 示例 {#examples}

在新的项目中创建第一个任务：

```text
ready
board new
zoom
shot board-new
board key new_below
board type "Sketch the onboarding flow"
board commit
shot board-new-created
```

把一个 fixture 显示为列表，折叠 Backlog，然后隐藏已完成的任务：

```text
ready
board fixture launch
zoom
board view list
board fold 0
board select "Notarize"
shot board-list
board hide-done on
shot board-list-hide
```

## 另见 {#see-also}

- [脚本](index.md)：运行脚本、计时与 fixture 设置。
- [文件 Block](file.md)：驱动从任务板打开的 Markdown 文件。
- [控制命令](control.md)：检查状态与菜单。
- [测试框架命令](harness.md)：指针输入与截图。
- [调试](../guides/debugging.md)：从脚本驱动窗口。
