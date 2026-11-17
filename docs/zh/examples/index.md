# 示例插件 {#example-plugins}

七个完整插件随 [SDK](../index.md#the-sdk) 一同发布，位于
[`plugins/examples/`](https://github.com/stencil-hq/tern-sdk/tree/main/plugins/examples)。
每个插件都端到端地解决一个真实问题，并且针对当前 API 编写，因此也可作为各部分
如何协同工作的参考。每个页面先解释设计取舍，再附上完整源码。

## 示例一览 {#the-examples}

| 示例 | 作用 | 半区 | 演示的 Surface |
| --- | --- | --- | --- |
| [Terraform Plans](terraform.md)（`terraform`） | 把 `terraform plan` 与 `tofu plan` 显示为汇总徽标、诊断信息，以及按操作分组的资源；点击即可复制地址 | Host | 带 `match` glob 的命令 lens、逐行解析、徽标色调、可折叠区块、通过 lens 的 `event` cx 触发点击操作、按角色限定的清单 CSS |
| [Review Queue](review-queue.md)（`review-queue`） | 列出等待审查的拉取请求，每两分钟通过 `gh` 轮询一次 | Host、window | 带按键、事件与保存状态的 block；带超时的 `tern.process.run`；`tern.timer` 轮询；错误视图；用 `cx:new_block` 打开该 block 的命令面板命令与快捷键 |
| [JSON Explorer](jsonx.md)（`jsonx`） | 以可折叠树浏览 JSON 文件，并复制 jq 路径 | Host、window | 以 `files` glob 与启动参数为文件来源的 block；带大小检查的 `tern.fs.read`；列表选中与滚动；保存状态；`tern.route.open`，其开关保存在 `tern.kv` 中 |
| [Long-Running Commands](longrun.md)（`longrun`） | 在慢命令结束时弹出 toast，并保留其历史 | Host、window | `command_started`/`command_finished` host 钩子、toast、带实时时钟的历史 block、状态段、由两个半区共享的模块 |
| [Directory Variables](dirvars.md)（`dirvars`） | 把 `.tern-env` 文件加载到每个新 shell 的环境中 | Host | `spawn` 过滤器及其时间限制、在文件变化时给出提示的 `cwd` 钩子、解析器模块 |
| [Project Workspaces](workspaces.md)（`workspaces`） | 打开项目在 `.tern/workspace.json` 中描述的标签页与分屏 | Window | `cx.layout:tab` 布局、`window_start`、`new_tab` 覆盖、状态段、清单 CSS |
| [Canvas Dashboard](../reference/api-window.md#canvas-cx)（`canvas-demo`） | 维持一个带 Refresh 操作的常驻仪表盘 | Window | `cx.canvas` 所有权、副本读取、带键补丁，以及仅所有者可用的 `canvas_action` 处理器 |

## 该读哪个示例 {#which-example-to-read}

| 目标 | 从这里开始 |
| --- | --- |
| 把命令的输出变成原生视图 | [Terraform Plans](terraform.md) |
| 构建带按键与保存状态的交互式 block | [JSON Explorer](jsonx.md)，然后看 [Review Queue](review-queue.md) |
| 在没有 host worker 的情况下显示常驻内容 | [Canvas Dashboard](../reference/api-window.md#canvas-cx) |
| 在后台运行程序并保持视图实时刷新 | [Review Queue](review-queue.md) |
| 接管某类文件的打开方式 | [JSON Explorer](jsonx.md) |
| 在每个面板中响应命令 | [Long-Running Commands](longrun.md) |
| 改变新 shell 的启动内容 | [Directory Variables](dirvars.md) |
| 安排标签页与面板，或替换内置命令 | [Project Workspaces](workspaces.md) |

## 试用示例 {#trying-one}

每个示例都是一个插件文件夹，内含 `plugin.toml`、其 Luau 文件以及 `README.md`。
可直接从 [SDK](../index.md#the-sdk) 安装一份副本：

```sh
tern plugin install github.com/stencil-hq/tern-sdk/plugins/examples/jsonx
```

或者克隆 SDK 并链接该文件夹，这样每次在其中保存文件时，Tern 都会重新加载插件：

```sh
git clone https://github.com/stencil-hq/tern-sdk
tern plugin link tern-sdk/plugins/examples/jsonx
```

`tern plugin list` 显示插件是否已加载，`tern plugin unlink jsonx` 或
`tern plugin remove jsonx` 可将其移除。每个示例都以 `--!strict` 开头，并针对
`tern plugin types DIR` 写出的定义文件进行类型检查；luau-lsp 的设置参见
[快速开始](../guides/getting-started.md)。

在 SDK 之外编写的插件也以相同方式从其各自的仓库安装；社区目录参见
[寻找与分享插件](../guides/distribution.md#finding-and-sharing-plugins)。
