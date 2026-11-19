# 画中画 {#pictures-in-picture}

`pip` 命令在当前标签页中创建并排列浮动在属主 block 之上的 block。借助这些命令，
无需依赖指针坐标，就能捕获浏览器卡片、聚焦与展开视图、堆叠的牌堆，或一次拖拽的落点。

## 创建与摆放卡片 {#creating-and-placing-cards}

| 命令 | 作用 |
| --- | --- |
| `pip float [<corner>]` | 把聚焦的拆分 block 浮动到接管其空间的那个 block 之上。 |
| `pip new [<corner>] ["<address>"]` | 在聚焦 block 之上创建浏览器卡片。省略地址会打开空白浏览器。 |
| `pip corner [#<n>] <corner>` | 把卡片移到其属主的另一个角位。 |

角位为 `tl`、`tr`、`bl` 与 `br`。`float` 默认使用属主上距该 block 原中心最近的角位；
`new` 默认使用右下角。浏览器地址可以是 URL，也可以是 `example.com` 这样的裸主机名；
可选角位之后的所有单词共同组成地址。

`float` 在聚焦 block 无法浮动时报错：它需要另一个符合条件的 block 作为属主。
创建浏览器卡片则需要有一个可供浮于其上的 block。

带 `[#<n>]` 的命令按卡片在当前标签页列表中的位置选择卡片，位置从 1 开始：`#1`
是最早创建的那张。在脚本中要加引号写成（`"#1"`），以免被当作注释。不带序号时，
命令选择聚焦的卡片，否则选择最近一次提升的卡片。`#0` 无法解析；序号超出最后一张
卡片会以 `no picture in picture to act on` 报错。裸数字不是卡片选择器。

`tern ctl state` 在 `pips` 中暴露当前标签页的卡片：`id`、`owner`、`corner`、`slot`
与 `rect` 描述其摆放位置。

## 聚焦、尺寸与停靠 {#focus-size-and-docking}

| 命令 | 作用 |
| --- | --- |
| `pip focus [#<n>]` | 聚焦卡片，将其放大并铺平以便交互。 |
| `pip expand` | 在聚焦时的常规尺寸与填满其框架之间切换聚焦卡片。 |
| `pip resize [#<n>] <w> <h>` | 按卡片当前模式设置其速览尺寸或聚焦尺寸。 |
| `pip dock [left\|right\|up\|down]` | 把聚焦卡片恢复为其属主旁的拆分；若没有聚焦卡片，则先选择默认卡片。 |

尺寸为非负整数 CSS 像素；显示的卡片会被约束在其框架内。速览尺寸与聚焦尺寸分别存储。
没有聚焦卡片时，`expand` 不做任何事。不带方向时，`dock` 在可以恢复时回到原拆分位置，
否则使用卡片角位所朝的一侧。停靠会把卡片从 `pips` 中移除。

状态字段 `mode`、`size`、`focus_size`、`rect` 与 `stage_frame` 描述尺寸与呈现方式。
`mode` 为 `glance`、`focus`、`expanded` 或 `hidden`。

## 移动与释放 {#moving-and-releasing}

| 命令 | 作用 |
| --- | --- |
| `pip fling [#<n>] <vx> <vy>` | 把卡片从静止状态抬起，并以给定速度释放。 |
| `pip drag [#<n>] <dx> <dy> [steps <k>]` | 按偏移量移动已抬起的卡片，并让它保持被按住的状态。 |
| `pip release [<vx> <vy>]` | 释放被按住的卡片；除非同时给出两个分量，否则使用拖拽中采样的速度。 |

偏移量为整数 CSS 像素，速度为整数 CSS 像素每秒。x 为正表示向右；y 为正表示向下。
拖拽默认使用 8 步；步数必须为正整数。用 `pip release 0 0` 可在无动量情况下落定。
落定可能改变角位、把卡片重新绑定到另一个属主、将其停靠，或把它收存到边缘。

所选卡片未显示时，`drag` 与 `fling` 报错。除非有正在进行的拖拽，否则 `release` 会以
`no picture in picture is held` 报错。落定会更新 `pips.owner`、`corner`、`stashed`
与 `flying`；`pip_commits` 统计已完成的落定手势。`pips` 中没有表示拖拽按住状态的字段。

## 收存、牌堆与检查 {#stashing-decks-and-inspection}

| 命令 | 作用 |
| --- | --- |
| `pip stash [#<n>] left\|right` | 把卡片隐藏到指定边缘，留下一张标签页以便取回。 |
| `pip unstash [#<n>]` | 把已收存的卡片取回。 |
| `pip stash-all` | 在当前标签页中，于收存与可见两种状态之间切换所有卡片。 |
| `pip fan [#<n>]` | 展开所选卡片的角位牌堆，并让指针在逻辑上保持在其上方。 |
| `pip see [#<n>]` | 让速览卡片半透明并可穿透点击，如同在其上按住 Option 键。 |
| `pip menu [#<n>]` | 在卡片上边缘附近打开其上下文菜单。 |

`see` 只影响速览卡片。移开指针或松开 Option 键会清除穿透效果。`stash-all` 不要求
先选中卡片。其余命令在没有可选卡片时报错。

状态字段 `stashed`、`tab`、`crowded`、`deck`、`slot` 与 `rect` 暴露已收存的标签页与
牌堆布局。完成布局后，`deck` 为 `whole`、`peek<n>` 或 `hidden`。穿透效果与已打开的
菜单在 `pips` 中没有专门字段；可检查渲染树，或使用控制端点的 `menus` 命令。

## 时序与解析 {#timing-and-parsing}

这些命令在无头场景与受控窗口中均可工作；没有一条仅限无头运行。它们会等待 650 ms
的动画时间后视为完成，`drag` 例外，它等待 50 ms 并让卡片保持按住状态。它们不等待
浏览器页面加载，也没有单独的实时超时。当一次捕获需要特定的页面标题或 URL 时，
使用 `webview` 上报。

一行必须严格匹配上述某种形式：缺少或多出单词，或某个参数无法解析（角位、侧、方向、
卡片序号，或超出有符号 32 位整数的数字），都会报错，并在错误中给出可用形式或该参数。
`new` 之后第一个不是角位的单词属于地址的一部分。

## 示例 {#examples}

聚焦并展开一个浏览器卡片，如同 `pip-focus` 场景：

```text
ready
run "git log --oneline -30 --color=always"
split right
run "ls -G"
pip new br "example.com"
webview ".tn-pane.pip .kit-web-page" title "Example Domain"
focus left
wait 500
pip focus
wait 700
shot pip-focus
pip expand
wait 700
shot pip-expanded
```

把卡片拖到另一个面板上以重新绑定，如同 `pip-rebind`：

```text
ready
run "ls -G"
split right
run "git log --oneline -12 --color=always"
split down
focus left
pip new br "example.com"
focus left
pip drag 640 -380 steps 12
wait 60
pip release 0 0
wait 700
shot pip-rebind
```

## 另见 {#see-also}

- [浏览器 block](browser.md)：导航并检查浏览器卡片。
- [终端与面板](terminal.md)：拆分并聚焦作为属主的面板。
- [Harness 命令](harness.md)：浏览器上报与动画捕获。
- [控制命令](control.md)：检查状态与菜单。
- [调试](../guides/debugging.md#driving-a-window-from-a-script)：驱动正在运行的
  窗口。
