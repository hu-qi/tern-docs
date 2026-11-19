# 画布 block {#canvas-blocks}

`canvas` 命令用于打开画布 block 并在其上绘制：墨迹、形状、箭头与文本，可用任意
画布组合键。用它为截图构建一块画布，或检查编辑是否到达画布的 host 及其其他
block。

## 打开与等待 {#open-and-wait}

| 命令 | 作用 |
| --- | --- |
| `canvas new` | 在当前 host 上、聚焦 block 的旁边打开一个新的空画布。 |
| `canvas second` | 在聚焦 block 的画布上、其旁边打开另一个 block。 |
| `canvas wait` | 等到每个画布 block 都显示其画布，且其 host 已接收所有编辑。 |

`new` 与 `second` 会等到新 block 的画布打开（或失败），然后稳定 350 ms；`wait`
等待各 host 的确认，受脚本的 20 秒超时限制。

## 绘制 {#draw}

| 命令 | 作用 |
| --- | --- |
| `canvas tool <name>` | 选择工具：`select`、`hand`、`draw`、`highlight`、`eraser`、`arrow`、`line`、`rect`、`ellipse`、`diamond`、`triangle`、`hexagon`、`parallelogram`、`star`、`cylinder`、`pill`、`bracket`、`brace`、`polygon`、`curve` 或 `text`。 |
| `canvas draw <x,y> <x,y> …` | 在第一个点按下，然后用当前工具拖过其余各点。 |
| `canvas rect <x> <y> <w> <h>` | 绘制矩形（先用矩形工具，再拖动）。 |
| `canvas text <x> <y> "<text>"` | 用文本工具点击，并输入文本。 |
| `canvas key <chord>` | 按 id 运行画布组合键（`undo`、`group`、`copy`、`zoom_to_fit`；参见 [`canvas.*`](../reference/actions.md#canvas-blocks-canvas)），或按下由画布自身接收的按键：`escape`、`delete`、`enter`、`space`、`tab`、`left`、`right`、`up`、`down`。 |
| `canvas select-all` | 选中所有形状。 |
| `canvas look clean\|mono\|sketch` | 设置画布的外观样式。 |

坐标是画布自其左上角起的视口像素；初始时画布以 100% 显示其原点，因此它们同时也
是页面单位。拖动以不超过 6 px 的步长移动，每 8 ms 采样一次，且从不停顿，因此墨迹
不会被吸附成形状。这些命令作用于聚焦的画布 block，并稳定 350 ms；没有画布 block
获得焦点时它们会失败。

## 状态 {#state}

`tern ctl state` 在 `canvas_blocks[]` 中报告每个 block：`id`、`canvas`
（`canvas:<id>`）、`phase`（`loading`、`ready` 或 `failed`，并附 `error`）、
`synced`（host 已接收所有编辑）、`focused`、`saved_camera`，以及编辑器的 `tool`、
`toolLocked`、`selection`、`focus`、`camera`、`shapes`、`canUndo`、`canRedo`、
`editing`、`look` 与 `paper`。
