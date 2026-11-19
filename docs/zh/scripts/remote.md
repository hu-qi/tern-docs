# 远程主机 {#remote-hosts}

`remote` 驱动主机连接、Add remote host 对话框、主机浮层以及远程 shell 的链路条件。
借助它，即使没有远程机器也能演练远程 UI：loopback 主机在本地运行真实的会话守护进程，
而连接状态、SSH 设置进度与在线状态都可以预先布置。

## 主机与连接 {#hosts-and-connections}

| 命令 | 作用 |
| --- | --- |
| `remote loopback <address>` | 把一个进程内守护进程作为主机接入，显示其会话，并把它的第一个 shell 移到此前聚焦的面板所在目录。 |
| `remote state <name> connected\|connecting\|stalled` | 直接设置某主机的连接状态。 |
| `remote state <name> reconnecting [<message>...]` | 设置处于第 2 次尝试的重连状态。 |
| `remote state <name> failed [<message>...]` | 设置连接失败状态。 |
| `remote state <name> verify <fingerprint>` | 设置主机密钥验证状态。 |
| `remote identity <name> <principal> local\|ssh-key\|tailscale <from> <user>` | 用单跳替换主机的身份链：主体、认证方式、来源机器以及操作用户。 |
| `remote service <name> <version>\|old [system]` | 布置主机的 Tern 服务版本与更新能力。 |
| `remote switch <name>` | 切换到指定主机。 |
| `remote disconnect <name>` | 断开指定主机。 |
| `remote pair-refused <address>` | 像从移动端扫描 Connect 代码那样添加主机，再像电脑拒绝该代码那样使其失败：会显示表示拒绝的 toast。 |

主机名匹配不区分 ASCII 大小写；未知名称会失败。在设置主机状态之前，先用
`remote loopback` 或 `remote stage` 创建主机。无效地址会失败。诸如 `can@devbox` 的
loopback 地址会创建名为 `devbox` 的主机。

loopback 最多等待三秒让守护进程应答，随后等待 shell 就绪，并受脚本 20 秒真实时间超时的
约束。本组其他命令等待 450 ms 即视为完成；单独设置 `connected` 并不会建立可用连接。

默认的重连消息是 `the network went away`，默认的失败消息是 `the connection timed out`。
只有这两种状态接受消息。消息为剩余的词语，以空格连接。远程参数在脚本解析之后会再次按
空白切分，因此引号无法让主机名或身份参数包含空格。

`service` 接受版本字符串而不校验其格式。普通版本会布置一个用户级服务，可经由链路接受
更新；`system` 则布置一个不具备该能力的系统级服务。`old` 代表版本上报出现之前的服务，
会忽略 `system`。较旧的服务可以在 Preferences › Hosts 中显示 Update 提议。

在 `tern ctl state` 中检查 `hosts.current` 与 `hosts.hosts[]`。每个主机条目包含
`name`、`address`、`state`、`sessions`、`identity`、`tern`（上报的版本）与
`update`（提供的更新或其进度）。

## 对话框与主机选择 {#dialogs-and-host-selection}

| 命令 | 作用 |
| --- | --- |
| `remote add [<address>]` | 打开 Add remote host 对话框，可选择性地填入其地址。 |
| `remote stage <address> [<fingerprint>]` | 布置一个正在连接的主机，或一个等待密钥验证的主机，并在对话框中跟随它。 |
| `remote peers [<name>...]` | 替换对话框中的 tailnet 对等节点列表。 |
| `remote ssh-hosts [<alias>...]` | 替换对话框中的 SSH 配置主机列表。 |
| `remote popover [<name>]` | 打开主机浮层；默认为当前主机。 |
| `remote hosts` | 打开命令面板的 Hosts 范围，用于切换主机。 |

不带地址的 `add` 会以空字段开始。必要时 `stage` 会打开对话框；其地址必须可以解析。
指纹只用于显示以供验证，不会与真实的远程密钥比对。把被跟随的主机设为 `connected`
会关闭对话框。

对等节点与 SSH 主机列表可以为空，从而清空布置的列表。tailnet 对等节点会获得合成的
在线 Linux 详情以及端口 8376 上的地址；`ssh-hosts` 提供的是别名，而不是读取
`~/.ssh/config`。这些命令布置的是发现结果，而非网络发现。本组所有命令等待 450 ms
即视为完成。

状态以 `hosts.popover` 暴露浮层的主机。对话框关闭时 `hosts.dialog` 为 null；否则它包含
`address`、待定的 `host` 与 `state`、`peers` 与 `ssh` 计数、`primary` 按钮标签以及
`setup`。Hosts 面板在 `hosts` 中没有专用字段；请用 `tree` 检查它。

## SSH 设置 {#ssh-setup}

| 命令 | 作用 |
| --- | --- |
| `remote setup <destination>` | 必要时打开对话框，并布置一个 SSH 设置流程，而不启动 SSH 引擎。 |
| `remote setup-step login\|inspect\|install\|service\|route [<note>...]` | 把布置的设置推进到某一步，可选择性地提供该步骤的进度说明。 |
| `remote setup-fail login\|inspect\|install\|service\|route <error>... [terminal]` | 在某一步使设置失败；末尾的 `terminal` 表示该失败需要交互式终端。 |
| `remote setup-offer <name>` | 把布置的主机标记为可进行 SSH 设置，并在对话框中跟随它。 |

这四种形式仅限桌面端，iOS 上不可用。它们布置的是 UI 进度，并不会安装 Tern 或通过 SSH
登录。在发送进度或失败事件之前，先执行 `setup`。要显示设置提议，先布置一台主机，把其
状态设为 `failed`，再使用 `setup-offer`。

未知步骤会导致解析失败。说明与错误会消耗剩余的词语，以空格连接。错误为必需项。末尾的
`terminal` 只有在其前面至少有一个错误词语时才是标志；单独出现时它本身就是错误文本。
命令等待 450 ms 即视为完成，而不是等待真实的 SSH 操作。

检查 `hosts.dialog.setup`：`destination`、`step`、`note`、`failed`、
`needs_terminal` 与 `done`。`step` 使用首字母大写的名称，例如 `Install`。

```text
ready
remote add
remote peers devbox
remote ssh-hosts spark build-01 gpu-box pi-garage
shot remote-setup-hosts
remote setup spark
remote setup-step login
remote setup-step inspect
remote setup-step install Downloading Tern 0.5.1 for linux-arm64 on spark…
shot remote-setup-install
```

## 链路条件与在线状态 {#link-conditions-and-presence}

| 命令 | 作用 |
| --- | --- |
| `remote rtt <name> <ms>\|off` | 覆盖链路的往返时延估计，或恢复其自身估计。 |
| `remote hold <name>` | 让在途输出落地，随后扣住后续的主机输出。 |
| `remote release <name>` | 释放被扣住的输出，并应用此间到达的内容。 |
| `remote peer-join <name> <identity>` | 在当前主机上布置来自机器 `<name>` 的另一个客户端。 |
| `remote peer-leave <name>` | 在当前主机上移除来自该机器的布置客户端。 |

`rtt` 接受非负整数毫秒值。预测回显在超过 30 ms 时开始猜测，并在超过 80 ms 时给猜测
加下划线。这改变的是面板所见的估计值，而非网络的实际延迟。

`hold` 为在途输出留出 300 ms 真实时间，随后扣住其余部分。它会等到扣住生效，再等待
100 ms 即视为完成；常规的 20 秒真实时间等待超时同样适用。`release`、`rtt` 与在线状态
命令等待 450 ms 即视为完成。

对于在线状态命令，`<name>` 是另一客户端的来源机器，而不是要查找的主机。布置的身份使用
tailnet 认证与当前主机的操作用户；若主机没有身份链，则使用 `<identity>` 中 `@` 之前的
部分。当该机器没有任何客户端接入时，`peer-leave` 会失败。

`tern ctl state` 没有专用的 RTT、输出扣住或对等在线字段。用面板输出与 `shot` 检查
预测回显；打开主机浮层检查在线状态。`hosts.current` 标识受在线状态命令影响的主机。

```text
ready
remote loopback can@devbox
agent-command "env -i HOME=$HOME TERM=$TERM PS1='devbox$ ' /bin/sh -i"
block agent
zoom
ready
remote rtt devbox 400
type "e"
remote hold devbox
type "cho hello"
shot remote-echo
remote release devbox
shot remote-echo-landed
```

## 另见 {#see-also}

- [脚本](index.md)：运行命令、语法与计时。
- [终端与面板](terminal.md)：shell 就绪、键入与输出。
- [Preferences](prefs.md)：主机设置与更新提议。
- [控制命令](control.md)：状态与 UI 检查。
- [调试](../guides/debugging.md)：驱动正在运行的窗口。
