# SDK {#sdks}

四个库分别以 Rust、Python、Go 与 TypeScript 实现 TSP。它们位于
[stencil-hq/tern-sdk](https://github.com/stencil-hq/tern-sdk) 仓库中，在传输线路上
逐字节一致。

每个 SDK 都用带类型的 props 构造每一种类型：[`button`](../elements/input.md#button)、
[`stats`](../elements/data.md#stats)、可选择的 [`table`](../elements/data.md#table)
（含文本、徽标、按钮与迷你折线单元格）、带控件的 `card` 头部、分段式 `tabs`，
以及 `open` 的 `font` 选项。在用它构建应用之前，请先阅读
[设计视图](../guides/design.md)：其中说明该选用哪一种，让你的程序无需样式表
就看起来像 Tern 自己的界面。

| 语言 | 包 | 构造器 |
| --- | --- | --- |
| Rust | crate `tern-sdk`（[`rust/`](https://github.com/stencil-hq/tern-sdk/tree/main/rust)） | `ui::card().head("…").child(…)`，处理器即你的消息类型 |
| Python | `tern-sdk`，`import tern_sdk`（[`python/`](https://github.com/stencil-hq/tern-sdk/tree/main/python)） | `ui.card(…, head="…")`，处理器即可调用对象 |
| Go | `github.com/stencil-hq/tern-sdk/go/tern`（[`go/tern/`](https://github.com/stencil-hq/tern-sdk/tree/main/go/tern)） | `ui.Card{Head: ui.T("…")}`，处理器即函数 |
| TypeScript | `@stencil-hq/tern`（[`typescript/`](https://github.com/stencil-hq/tern-sdk/tree/main/typescript)） | TSX：`<card head="…">`，处理器即 props |

同一张卡片，在 Tern 中保留在回滚缓冲区里，在其他任何地方则打印为纯文本：

```rust
tern_sdk::print(
	ui::card().head("cargo test").status(ui::Status::Done).child(ui::md("All **42** tests pass.")),
	PrintOptions::new(),
)?;
```

```python
tern_sdk.show(ui.card(ui.md("All **42** tests pass."), head="cargo test", status="done"))
```

```go
tern.Print(ctx, tern.Main(ui.Card{
	Head:     ui.T("cargo test"),
	Status:   ui.Done,
	Children: ui.Nodes(ui.Md{Text: "All **42** tests pass."}),
}), tern.PrintOptions{})
```

```tsx
await print(
   <card head="cargo test" status="done">
      <md>{'All **42** tests pass.'}</md>
   </card>
);
```

## 它们为你做什么 {#what-they-do-for-you}

| 协议部分 | SDK 的作用 |
| --- | --- |
| [传输](transport.md) | 为每条消息分帧，在 Tern 的解析器能完整读回每一片的 `apc` 上限处切分消息体，并对二进制块编码，返回为每个块命名的 SHA-256 id。其输入解析器从 pty 输入中分离出 `tsp;r` 与 `tsp;e`（APC 或 OSC 877）并放行按键；括号粘贴中的文本永远不会被当作 TSP 读取。 |
| [握手](handshake.md) | 把 tty 置为 raw 模式，随 DA1 发送 `hello`，并在 `TERN_TSP=0`、没有 tty、处于 screen 或 zellij 中，或 DA1 先行应答与一秒后才应答时，报告不使用 TSP。在 tmux 内部，只有当 Tern 绘制该会话时才探测，且仅发送 `hello`，并在探测停止前关闭面板的 `allow-set-title`（[在 tmux 内部](handshake.md#inside-tmux)）。保持 `cols`、`dark` 与 `reduceMotion` 为最新值，并暴露 `hour12`（对于不发送该值的终端为 false）。 |
| [Surface](surfaces.md) | 打开、设置样式并关闭 surface；关闭时先发送最后一个待处理的帧，再发送 `x`，撤销其终端模式并排空输入，使任何回复都不会到达 shell。 |
| [文档与帧](documents.md) | 渲染完整视图，只发送差异，id 由键推导，方式与 Tern 的[插件 worker](../guides/blocks.md#regions-node-ids-and-keys)完全一致：`main.<key or index>…`。以追加后缀方式增长的文本会作为 `append` 发出。 |
| [输入与事件](input.md) | 解码按键（传统 xterm、kitty `CSI u`、粘贴），并按每个事件所属的 surface 与节点 id 将其路由到该节点上的处理器；其余事件进入你的循环。 |
| [流控](operations.md#flow-control) | 最多保留 `credits` 个未确认的帧，并把等待期间产生的每次渲染合并为一个帧。 |
| [调试](operations.md#debugging) | `TERN_TSP_RECORD=<file>` 把每条消息记录为 JSONL，供 `surface-play` 使用。 |

两个辅助函数覆盖了大多数 CLI：`print`（在 Python 中为 `show`）在 `flow` surface
中绘制静态视图，作为命令输出留存；`ask` 显示表单，并返回提交该表单的动作及其
`values`。`plain` 把任意视图渲染为纯文本，用于回退。

每个 SDK 都附带同样的五个示例：`table`（用 `print` 输出的目录列表）、`ask`
（[上文会话](index.md#a-whole-session)中的表单）、`progress`（运行中卡片里的
流式构建日志）、`chat`（带停靠编辑器的内联 surface，由程序根据按键驱动）以及
`dashboard`（使用无衬线字体的全屏应用，汇集了[设计指南](../guides/design.md)
中的配方：一行头部、一条扁平的 stats 数据瓦片带、覆盖三个视图的标签页，每个视图
都是全宽可选表格配上承载主操作的详情卡片，停靠区中还有确认条与按键图例，并带
实时更新）。

在 Tern 之外，`plain` 把每种类型都写成文本：`button` 写成 `[Label]`，`stats`
每个瓦片写成 `label: value (sub)`，表格单元格写成其文本（按钮单元格写成
`[Label]`，迷你折线写成 `▁▂▅` 方块）。
