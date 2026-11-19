# 信任与安全 {#trust-and-security}

安装插件就意味着信任它。插件以你的身份运行，对你文件、程序与 shell 的访问权限与你相同，
Tern 没有可以收窄这一权限的权限系统。本页说明信任模型、Luau 沙箱的用途与局限、插件能
触及什么、远程 host 如何改变这一局面，以及在这种前提下如何安装与编写插件。

## 信任模型 {#the-trust-model}

Tern 对待插件的方式，与 Neovim 对待其 Lua 插件、WezTerm 对待其 Lua 配置相同：把它们
视为你选择运行的代码。没有审查，没有签名，`plugin.toml` 中没有权限列表，插件做任何事
之前也不会询问。包一旦放进插件文件夹就开始运行：`tern plugin install`、`link`，以及
复制到该文件夹，都会导致一次重载（通过 CLI 或文件夹监视），从而运行其入口。

| 问题 | 回答 |
| --- | --- |
| 谁决定运行什么？ | 能写入 `<config>/plugins/` 的人，或能写入 `.path` 文件或符号链接所指向的包目录的人 |
| 以谁的权限运行？ | 运行该进程的用户：host 半区为会话守护进程，window 半区为窗口 |
| 运行前会询问什么？ | 什么都不问 |
| 什么能关闭它？ | `settings.json` 中的 `plugins_disabled`（或 `plugins: false`）、删除该包，或 `tern plugin unlink`；Disabled 插件的入口从不运行 |

这个模型是有意为之。终端插件之所以有用，正是因为它能运行 `kubectl`、读取你的项目文件并
向你的 shell 输入；允许这些行为的权限系统几乎限制不了什么，而不允许的系统则会让插件无法
完成工作。

## 沙箱的用途 {#what-the-sandbox-is-for}

每个插件半区都运行在沙箱化的 Luau VM 中
（[运行时、预算与 JIT](runtime.md#the-vm)）。沙箱防止有缺陷的插件伤害 Tern；它不能阻止
恶意插件伤害你。

| 沙箱特性 | 防范 | 无法阻止 |
| --- | --- | --- |
| 没有 `io`，没有 `os.execute`、`os.getenv` 或 `os.remove` | 代码在 `tern` 的错误处理之外意外接触系统 | `tern.fs`、`tern.process` 与 `tern.getenv`，它们做同样的事 |
| `require` 限于包目录 | 模块路径悄然加载他人的代码 | 用 `tern.fs.read` 读取任意文件 |
| 只读的内置库 | 某个模块为其他模块破坏 `string` 或 `table` | VM 之外的任何东西 |
| 时间预算（4 ms、50 ms、2 s） | 无限循环冻住窗口或工作线程 | 移入进程或分散到多个计时器中的长时间工作 |
| 256 MiB 内存上限 | 失控的表耗尽进程 | 插件启动的进程 |
| 每个插件的每个半区一个 VM | 某个插件的全局变量或错误影响另一个 | 某个插件通过 `tern.fs` 写入另一个插件的包或数据文件夹 |

离开 VM 的每条途径都经过 `tern`，因此 `tern` API 就是插件能直接做的一切的完整清单。
它并不是一份狭窄的清单。

## 插件能触及什么 {#what-a-plugin-can-reach}

| 触及范围 | host 半区 | window 半区 |
| --- | --- | --- |
| 文件 | `tern.fs` 在 host 上读取、写入与删除守护进程用户能访问的任意路径 | 相同，作用于窗口所在的那台机器 |
| 程序 | `tern.process.run` 以任意参数启动任意程序，继承守护进程的环境加上 `TERN_PLUGIN_DATA` | 相同，从窗口的进程启动，加上 `TERN_WINDOW_KEY`；在 iOS 上会抛出错误 |
| 网络 | `tern.fetch` 从守护进程所在机器发出任意 HTTP(S) 请求，方法、标头与正文任意 | 相同，从窗口所在的机器发出，包括 iOS |
| 环境 | `tern.getenv` 读取守护进程的环境 | `tern.getenv` 读取窗口的环境 |
| 钥匙串 | 无 | `tern.secrets` 在系统钥匙串中读写此插件自己的密钥；它无法指名另一个插件的密钥 |
| shell 输入 | `tern.pane.write` 向 host 上任意面板输入 | `cx:run` 向窗口中任意面板输入，包括远程 host 的面板 |
| 新 shell | `spawn` 过滤器可以改变 host 启动的每个 shell 的程序、参数、目录与环境 | `cx.layout` 打开运行命令的标签页与分屏 |
| 你运行的内容 | `command_started` 与 `command_finished` 携带每一行命令；`tern.pane.list` 给出每个面板的目录、程序与标题 | 同样的事件与 `cx.session`，覆盖窗口中的每个面板 |
| 命令输出 | lens 会收到其 `match` glob 认领的命令输出的每一行 | 没有直接途径 |
| 你的窗口 | 在显示该面板的窗口中的效果：toast、剪贴板（`cx:copy`），以及打开路径或 URL（`cx:open`），后者遵循与点击链接相同的规则 | 内置命令的覆盖、快捷键、先于其他处理看到每次打开与链接点击的路由、chrome 文本，以及覆盖 Tern 全部 UI 的样式表 |

`tern.process.run` 接收参数向量并直接启动程序，不经过 shell。`tern.fetch` 能到达机器
可访问的任意 HTTP(S) 服务器，包括 `localhost` 与本地网络，因此它是数据离开机器的又一条
途径。任何其他程序，例如 `curl` 或 `ssh`，同样只需一次 `tern.process.run`。

插件数据也不是私密的。`<state>/plugin-data/<id>/` 与 `kv.json` 是普通文件，每个以你的
身份运行的插件与程序都能读写。`tern.secrets` 把每个插件的密钥保存在系统的安全存储中
（不可用时改为仅属主可读的文件），账户名以插件命名（`plugin.<id>.<name>`），因此一个插件的
`tern.secrets` 永远不会返回另一个插件的密钥。参见
[文件、进程与存储](../guides/io.md)。

## 远程 host {#remote-hosts}

当你的窗口连接到另一台机器时，会有两组插件参与，它们运行在不同位置，拥有不同权限：

| 插件 | 运行于 | 以谁的身份 | 触及 |
| --- | --- | --- | --- |
| 远程 host 的 host 半区 | 远程机器上的守护进程中 | 该守护进程运行的用户 | 那台机器的文件、程序与面板 |
| 你的 window 半区 | 你的机器上的窗口中 | 你 | 你的机器，以及你窗口中的每个面板（包括远程面板） |

远程 host 的插件从不在你的机器上运行代码。从它们到达你窗口的是数据：它们的目录（block
标题与图标、lens glob）、block 帧、lens 视图、效果（toast、剪贴板文本、打开操作），以及
它们的清单样式，你的窗口会将这些样式作为全局样式表安装（`plugin:<host>:<id>:styles`）。远程
host 运行哪些插件由该 host 的所有者决定，在该 host 的插件文件夹中进行。

另一方面，你的 window 半区跨 host 工作：`cx:run` 接受窗口中的任意面板，因此 window 插件
输入远程 shell 的文本会以该 shell 的权限在那台 host 上运行。安装 window 插件时，应当把
它视为能向你打开的每个 shell 输入，因为它确实可以。

## 没有权限系统 {#no-permission-system}

Tern 不声明、不检查也不询问能力，也不对包签名或校验。插件能做的一切，从其入口运行的那一
刻起就能做。现有的控制手段都很粗粒度：

- `settings.json` 中的 `plugins: false` 不在该机器上加载任何插件。
- `plugins_disabled` 阻止列出的插件加载；Preferences › Plugins 中每个插件都有一个开关。
- 每台机器读取自己的设置与插件文件夹：在你的 Mac 上禁用某个插件不会在远程 host 上禁用
  它，反之亦然。

参见 [包与清单](packages.md#settings)。

## 建议 {#recommendations}

**安装。**

- 安装前先阅读插件：`plugin.toml`、两个入口、它们 `require` 的每个模块，以及每一处
  `tern.process.run`、`tern.fetch`、`tern.fs.write`、`tern.fs.remove`、
  `tern.pane.write` 与 `cx:run` 调用。
- 安装你读过的代码。用 git URL 执行 `tern plugin install` 会对默认分支做一次当时的
  浅克隆，因此安装的内容可能不是你先前审查的内容。要固定某个提交，请自行克隆仓库，
  检出你审查过的提交，然后从该目录安装：

  ```sh
  git clone https://github.com/example/tern-k8s
  git -C tern-k8s checkout 3f2a9c1
  tern plugin install ./tern-k8s
  ```

  安装的副本不包含 `.git`，也不会自我更新；之后的 `tern plugin install --force` 会
  替换它。
- 让插件文件夹及链接到其中的每个目录只对你可写：写进去的任何内容都会在下一次重载时
  运行。
- `tern plugin list` 与 Preferences › Plugins 显示已加载的内容。对不放心的插件，应
  禁用它而不是让它继续运行。

**开发。**

- 用 `tern plugin link DIR` 开发插件：Tern 从你的检出中加载它，并在每次保存后重载，
  `tern plugin unlink ID` 会再次移除它。参见 [分发](../guides/distribution.md)。
- 把面板输出、命令行、文件名与 lens 输入视为不可信文本。绝不要在未加引号的情况下用
  它们拼接 `cx:run` 或 `tern.pane.write` 字符串，因为那些文本会在用户的 shell 中
  运行；优先使用带参数向量的 `tern.process.run`。
- 让密钥远离 `tern.kv` 与数据文件夹，它们是普通文件：改用 `tern.secrets`（window
  半区）保存，它把每个插件的密钥保存在系统钥匙串中以其自身命名的账户下。参见
  [`tern.secrets`](../reference/api-window.md#ternsecrets)。
- 在 README 中说明插件运行哪些程序、联系哪些服务器、写入哪些文件，以便用户快速审查。

## 相关页面 {#related-pages}

- [架构](architecture.md)：每个半区在哪里运行。
- [运行时、预算与 JIT](runtime.md)：沙箱的细节。
- [分发](../guides/distribution.md)：安装、链接与发布。
