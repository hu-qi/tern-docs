# Tern 插件 SDK {#tern-plugin-sdk}

Tern 插件是以 Luau 编写的包，用于扩展和改造 Tern。插件可以新增 block
类型（用 Lua 绘制的原生面板）、把 shell 命令的输出读作命令 lens、响应面板生命周期、
添加命令面板项与快捷键、覆盖内置命令、接管文件打开与链接跳转、格式化标签栏、
窗口标题与状态行、用 CSS 重绘应用外观，以及用脚本编排窗口布局。

一个插件就是一个文件夹，内含 `plugin.toml` 清单，以及最多两个 Luau 入口
文件。把它放到 `<config>/plugins/` 下（或用 `tern plugin link` 链接到那里），
它就会改变该机器上的 Tern。

```toml
schema = 1
id = "hello"
name = "Hello"
version = "0.1.0"
host = "host.luau"
window = "window.luau"
```

## 两个半区 {#two-halves}

每个插件最多包含两个半区，各自运行在独立的 Luau VM 中：

| 半区 | 入口 | 运行位置 | 能做什么 |
| --- | --- | --- | --- |
| **Host** | `host = "host.luau"` | 会话守护进程，或没有守护进程时承载面板的窗口 | block、命令 lens、面板钩子、spawn 过滤器、向面板写入 |
| **Window** | `window = "window.luau"` | 每个 Tern 窗口，运行在其 UI 线程 | 命令、快捷键、覆盖、路由、chrome 格式化器、Files 面板按钮、CSS、布局、窗口事件 |

host 半区在面板所在的位置运行，因此它定义的 block 就是普通面板：附着到该会话的
每个窗口都会显示它，窗口退出后它依然存在。window 半区只看到一个窗口，也只改变
这一个窗口。参见
[架构](concepts/architecture.md)。

## 选择一条路径 {#choose-a-path}

- **原生读取命令输出：** [命令 lens](guides/lenses.md)
  用清单里的 glob 认领命令行，把它们的输出变成表格、
  树和徽标。
- **新增面板类型：** [block](guides/blocks.md) 在 Lua 中保存状态，用
  [`tern.ui`](guides/views.md) 渲染视图，并处理按键与点击。
- **改变 Tern 的行为：** [命令、按键与覆盖](guides/commands.md)、
  [路由](guides/routing.md)、[chrome 与样式](guides/chrome.md) 和
  [布局](guides/layout.md) 都在 window 半区运行。
- **响应 shell 的行为：** [host 钩子](guides/hooks.md) 能看到命令
  启动与结束、目录与标题变化，并能改写 shell 的启动方式。
- **让任意程序原生绘制：** 不是插件的 CLI、TUI 或 agent，只要在它的 pty 上讲
  [Surface 协议](protocol/index.md)，就能在输出流中或全屏获得同样的原生元素。
- **查阅节点类型或样式钩子：** [元素](elements/index.md)
  记录了视图可以容纳的每一种类型，[视图样式](styles/index.md)
  记录了样式表可以使用的每个类、属性和变量。
- **脚本化 Tern：** [脚本](scripts/index.md) 可以逐条命令驱动窗口或无头
  运行，从打开面板到截图。
- **改色或重绘 Tern：** [自定义主题](guides/themes.md) 是一个叠加在任意主题上的
  CSS 文件，无需插件。
- **使用别人写的插件：** 官方没有插件仓库；
  [寻找与分享插件](guides/distribution.md#finding-and-sharing-plugins)
  指向社区目录，并说明如何从 GitHub 仓库或其某个文件夹安装插件。

先从[快速开始](guides/getting-started.md)读起，再看
[示例插件](examples/index.md)：每一个都是完整而真实的插件。

## SDK {#the-sdk}

SDK 即 [stencil-hq/tern-sdk](https://github.com/stencil-hq/tern-sdk)
仓库。其中 `plugins/examples/` 存放
[示例插件](examples/index.md)，每个都是一个可安装的文件夹；`plugins/tern.d.luau`
则是它们做类型检查所依据的定义；[Surface 协议 SDK](protocol/sdks.md)
就放在旁边。

```sh
git clone https://github.com/stencil-hq/tern-sdk
```

仓库中的 `tern.d.luau` 与这些文档保持一致；`tern plugin types DIR`
会写出你所安装的 Tern 对应的那一份。

## 文档约定 {#documentation-conventions}

代码即 Tern 运行的 Luau：`--!strict` 可用，`tern plugin types DIR`
会写出 luau-lsp 所需的 `tern.d.luau` 声明。写作 `<config>` 和 `<state>` 的路径
指 Tern 的配置目录与状态目录
（[包与清单](concepts/packages.md#directories)）。[API 参考](reference/api.md)
遵循运行时随附的 `tern.d.luau` 声明；当指南与参考冲突时，以参考为准。

每个页面也都会以 Markdown 形式发布在与自身路径相同的位置，只是扩展名由 `.html`
换成 `.md`（`protocol/surfaces.md`、`index.md`），便于 agent 及其他读取文本的工具
使用。

安装插件就意味着信任它，正如 Neovim 或 WezTerm 插件那样：`tern` API 可以写文件、
启动进程。参见
[信任与安全](concepts/security.md)。