# 支持矩阵 {#support-matrix}

插件在 macOS、Linux 与 Windows 桌面上完整运行。iOS 客户端只运行 window 半区，Web 标签页完全不运行 Lua；两者仍会显示其 host 的插件所产生的 block 与 lens 视图。本页按能力逐项拆解。

## 各平台能力 {#capabilities-by-platform}

| 能力 | macOS | Linux | Windows | iOS | Web 标签页 |
| --- | --- | --- | --- | --- | --- |
| Host 半区（`host` 入口） | 是，在守护进程中 | 是，在守护进程中 | 是，在守护进程中 | 否；跳过 host 入口 | 否 |
| Window 半区（`window` 入口） | 是 | 是 | 是 | 是 | 否 |
| 原生代码生成（`tern.runtime.jit`） | 是，在 Luau 代码生成器支持的 CPU 上 | 相同 | 相同 | 否；始终以解释方式执行 | 不适用 |
| `tern.process.run` | 是 | 是 | 是 | 抛出 `tern.process is not available on iOS` | 不适用 |
| `tern.fetch` | 是 | 是 | 是 | 是 | 不适用 |
| 插件 block 可见 | 是 | 是 | 是 | 是，来自所附着的 host | 是，来自提供服务的 host |
| Lens 视图可见 | 是 | 是 | 是 | 是，来自所附着的 host | 是，来自提供服务的 host |
| 插件 CSS | 本地包与所附着的远程 host | 相同 | 相同 | Files App 中的包与所附着的 host | 提供服务的 host 的清单 `styles`；没有 `tern.css` |
| `tern plugin` CLI | 是 | 是 | 是 | 否 | 否 |
| 插件文件夹监视 | FSEvents | inotify | `ReadDirectoryChangesW` | 每 2 s 轮询 | 不适用 |
| `tern.runtime.os` | `"macos"` | `"linux"` | `"windows"` | `"ios"` | 不适用 |

## 说明 {#notes}

**桌面。** 在三个桌面平台上，会话守护进程运行 host 半区，每个插件一个工作线程，每个窗口在其 UI 线程上运行 window 半区（[架构](architecture.md)）。没有守护进程、自行运行面板的窗口则在自己的进程中运行 host 半区。守护进程在 macOS 与 Linux 上通过 Unix socket 访问，在 Windows 上通过命名管道访问；插件感知不到差别。原地升级守护进程、让 shell 继续运行，仅适用于 Unix；在每个平台上，插件 block 都会在守护进程重启后从其已保存状态恢复
（[生命周期与重新加载](lifecycle.md#daemon-restart-and-upgrade)）。

**JIT。** 桌面发行版构建包含 Luau 的原生代码生成器，并在 CPU 受支持时使用它；否则以解释方式运行。macOS 应用使用 `com.apple.security.cs.allow-jit` 签名，因此强化运行时允许它所需的可执行内存。`tern.runtime.jit` 与
`tern plugin list --json` 的 `jit` 字段会报告这一点。插件代码在两种情况下行为相同。参见[运行时、预算与 JIT](runtime.md#jit)。

**iOS。** iOS 上的 Tern 是一个客户端：其 shell 与 host 半区在所附着的 host 上运行。Window 半区从 App 的 `Documents/Plugins` 文件夹加载（Files App：我的 iPhone 或 iPad › Tern › Plugins），并在解释器中运行。没有命令行，也没有 `git`：把包文件夹复制到该文件夹，并使用偏好设置 › 插件 或命令面板的“重新加载插件”。由于该文件夹无法被原生监视，Tern 每 2 s 轮询一次。`tern.fs` 在 iOS 允许 App 触及的范围内工作，`tern.process.run` 会抛出错误，而 `tern.fetch` 可用。iOS 上的 window 半区仍作用于窗口中的每个面板，而这些面板全部属于远程 host。

**Web 标签页。** Web 标签页（`tern web serve`）只有一个 host，即提供该页面的机器，自身不加载任何插件。它接收该 host 的
catalog，因此会像其他任何副本一样打开相同的 lens block，并显示插件 block、lens 视图与 effect（提示、剪贴板、打开）。它还会从该 catalog 安装 host 上 Ready 插件的清单 `styles`，名称为 `plugin:0:<id>:styles`，使插件 block 与 lens 视图的外观与桌面窗口一致，并在 host 的插件重新加载时重新安装它们。window 半区用 `tern.css` 添加的样式表永远不会到达它，因为那里没有 window 半区运行。

**插件 CSS。** 窗口会安装其自身插件文件夹中每个设置允许的包的清单 `styles`，名称为
`plugin:local:<id>:styles`，再加上其 window 半区用 `tern.css` 添加的样式表。每个所附着的远程 host 上 Ready 的插件都会从该 host 的 catalog 贡献
`plugin:<host>:<id>:styles`；没有窗口运行时的 Web 标签页也以同样方式安装其提供服务 host 的样式。参见
[chrome 与样式](../guides/chrome.md)。

**监视。** 原生监视无法覆盖目录树之处（网络卷、Linux 用完 inotify 监视数量），桌面构建会回退到 iOS 所用的同一套 2 s 轮询。参见[生命周期与重新加载](lifecycle.md#watching)。

## 相关页面 {#related-pages}

- [架构](architecture.md)：每个半区在哪里运行以及为什么。
- [信任与安全](security.md)：每个半区在每台机器上能触及什么。
- [限制](../reference/limits.md)：预算与尺寸，在各平台上都相同。