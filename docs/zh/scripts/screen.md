# 屏幕 block {#screen-blocks}

`screen` 打开主机显示器的视图，并驱动其显示器选择、尺寸模式与主机输入。可用它
捕获屏幕共享布局，或在不寻找工具栏控件的情况下试用远程输入。

## 打开与显示模式 {#opening-and-display-modes}

| 命令 | 作用 |
| --- | --- |
| `screen open` | 在聚焦面板旁打开一个屏幕 block 并聚焦它；若没有打开的标签页，则新建一个标签页。 |
| `screen display <id>\|main` | 共享指定的显示器，或主机的主显示器。 |
| `screen fit` | 让显示器适配 block 内部，只缩小，从不放大。 |
| `screen actual` | 按一个设备像素对应一个帧像素显示，并可滚动。 |
| `screen control on\|off` | 启用主机输入，或让该 block 变为只读视图。 |

新 block 共享当前主机的主显示器，采用适配模式，并开启控制。除 `open` 之外的每条
命令都要求有聚焦的屏幕 block；否则会以 `no screen block has focus` 报错。显示器
ID 来自 `tern ctl state` → `screen_blocks[].displays`。`main` 选择默认显示器，
而不是字面上的显示器 ID。显示器选择与模式在查看同一 block 的多个窗口之间共享。

`open` 会等待首帧显示满 250 ms 的真实时间，或等待共享失败，然后再等待 300 ms 的
应用时间后视为完成。`display`、`fit` 与 `actual` 按下面的输入等待规则等待主机的
下一帧。`control` 只等待 300 ms 的应用时间；它不等待帧，也不等待权限批准。

在 `screen_blocks` 中，`chosen` 记录请求的显示器（`main` 时为 `null`）；`display`
与 `display_name` 描述实际显示器。`actual` 与 `control` 记录所选模式。`frame` 与
`fit` 报告帧尺寸与适配尺寸，`frames` 统计已显示的帧数。

## 主机输入与等待 {#host-input-and-waits}

| 命令 | 作用 |
| --- | --- |
| `screen click <x> <y>` | 在显示器自身像素的浮点坐标处发送一次主键点击。 |
| `screen key <name>` | 按下并松开一个受支持的键，不带修饰键。 |
| `screen type ["<text>"]` | 以输入法提交的方式发送文本；省略文本时发送空字符串。 |
| `screen wait` | 等待主机绘制最后一次发送的输入。 |

键名为小写 `a`–`z`、`0`–`9`、`enter`、`escape`、`backspace`、`tab`、`space`、
`left`、`right`、`up` 与 `down`。其他名称无法解析；`screen key` 不支持修饰键
组合。坐标是显示器像素，而非窗口坐标，在适配模式下含义不变。`type` 把其余单词
作为文本消费；含空格的文本要加引号。其余命令消费其必需参数，并忽略多余单词。
缺少显示器 ID、无效的控制值，以及非数字或缺失的点击坐标，都无法解析。

`click`、`key` 与 `type` 要求存在已开启控制的实时共享连接；否则会以
`the screen block isn't sharing with control` 报错。这些命令与 `wait` 会一直等待，
直到最后一次输入之后有帧到达，且连续 250 ms 的真实时间内没有显示新帧。如果主机
不绘制任何内容，它们在两秒真实时间后结束。共享失败也会结束等待。没有待处理输入时，
`wait` 使用首帧规则。每次等待帧之后都会再等待 300 ms 的应用时间；harness 的 20 秒
超时仍然有效。等待完成并不能证明捕获或输入成功：请检查
`screen_blocks[].failure` 与 `input_refused`。`connected` 报告是否存在实时连接，
`cursor` 报告主机是否已提供光标形状。

## 无头运行与主机权限 {#headless-runs-and-host-permissions}

无头运行使用合成的测试图案，而不捕获或驱动真实桌面。该图案包含编辑器、滚动区域
与照片窗口，并为截图标记输入。要在无头运行之外使用它，请在承载屏幕的主机环境中
设置 `STENCIL_SCREEN_SOURCE=synthetic`。对于本地守护进程，这必须是守护进程启动
时所处的环境，而不只是已连接窗口的环境。

macOS、Windows 与 Linux 支持真实的屏幕托管；iOS 与 Web 查看端可以查看远程主机
的屏幕，但不能托管自己的屏幕。macOS 要求为守护进程的应用授予“屏幕录制”权限才能
捕获，授予“辅助功能”权限才能输入。Wayland 在每个会话中通过桌面门户请求权限；
由门户选择显示器并允许远程控制。X11 不请求任何权限。Windows 无法向完整性级别
更高的窗口（例如以提权方式运行的程序）注入输入。捕获失败会出现在 `failure` 中；
即使已启用控制，输入被拒绝也会出现在 `input_refused` 中。

下面的示例遵循 screen-input 基准场景：点击合成的编辑器，在共享画布中输入，
并在捕获前发送一次文本提交。

```text
ready
screen open
screen click 300 200
click .sc-canvas
type hello
screen type "!"
screen wait
shot screen-input
```

## 另见 {#see-also}

- [脚本](index.md)：语法、运行脚本与时序。
- [远程主机](remote.md)：连接到屏幕被共享的主机。
- [Harness 命令](harness.md)：窗口输入与截图。
- [控制命令](control.md)：检查 `state`。
- [调试](../guides/debugging.md)：驱动正在运行的窗口。
