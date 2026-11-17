# 账户、更新与 Kickoff {#account-updates-and-kickoff}

这些命令把账户门禁、更新界面与云端 kickoff 进度置入已知状态，而无需登录、下载构建或开通机器。可以用它们在脚本中或通过 `tern ctl` 截取账户界面、更新偏好设置与进度提示条。

## 账户 {#account}

| 命令 | 作用 |
| --- | --- |
| `account signed-out` | 显示登录门禁，并清除账户句柄与头像。 |
| `account waiting` | 显示正在等待浏览器的登录状态。 |
| `account waitlisted [<username>]` | 显示候补名单门禁，可选地指定账户名称。 |
| `account failed <message>` | 显示登录失败门禁，并带上所给消息。 |
| `account signed-in [<username>] [picture <file>]` | 隐藏门禁，显示账户头像，并提供退出登录。 |

每种形式都会让门禁生效，即使是在通常没有门禁的无头窗口中也是如此。它会取消任何待处理的登录等待，但不会真正认证账户，也不会等待浏览器或网络回复。每条命令都会稳定等待 450 毫秒。

用户名与失败消息可以是带引号的字符串，也可以是多个词；这些词会以空格连接。句柄会补上一个前导 `@`。不带名称的登录使用 `@ada`；不带名称的候补账户没有句柄。`failed` 需要非空消息。`picture` 后必须恰好跟一个文件参数，且必须位于可选名称之后。它使用本地图片：绝对路径或已存在的相对路径会直接使用；否则该路径会在 Tern 的 fixture 根目录下解析。fixture 根目录解析可能失败。`account signed-out` 与 `account waiting` 会忽略其后的多余词。

`tern ctl state` 会把这些命令反映在 `gate` 中：`applies`、`phase`、`signed_in`、`handle` 与 `error`。登录会把 `phase` 设为 `off`；失败会把 `error` 设为对应的消息。等待与失败不会清除先前的句柄或头像。头像本身不会包含在状态中。

```text
ready
account signed-out
shot account-signed-out
account waiting
shot account-waiting
account waitlisted "ada"
shot account-waitlisted
account failed "The sign-in server answered 500 (server_error)"
shot account-failed
account signed-in "ada" picture "goldens/fixtures/account-picture.png"
wait 300
shot account-picture
```

## 更新 {#updates}

| 命令 | 作用 |
| --- | --- |
| `update idle` | 显示刚检查过、已是最新版本的状态。 |
| `update checking` | 显示正在检查。 |
| `update downloading <percent>[%]` | 显示从 0 到 100 百分比的下载进度。 |
| `update preparing <percent>[%]` | 显示正在准备已下载的构建，进度从 0 到 100 百分比。 |
| `update waiting` | 显示有较新的构建正在等待来自构建服务的补丁。 |
| `update ready` | 显示已下载的构建可以安装。 |
| `update installed` | 显示该构建已由另一个窗口安装。 |
| `update failed <message>` | 显示更新失败。 |
| `update unsupported <message>` | 显示更新不可用的原因。 |

这些命令在 iOS 上不可用。它们只替换显示的状态，不检查网络，也不下载或安装任何内容。每条命令都会稳定等待 450 毫秒，而非等待真实更新。`checking`、`downloading` 与 `preparing` 会保持该状态，直到提供另一个状态。

示例发布版本为 `0.2.0 (abcdef0)`，下载大小为 48,000,000 字节。下载与准备进度接受 0 到 100 的整数，可选地后跟 `%`；缺失、非数字或超出范围的进度会失败。`failed` 与 `unsupported` 需要非空消息，并把其余的词以空格连接。`idle`、`checking`、`waiting`、`ready` 与 `installed` 会忽略其后的多余词。

新出现的待处理发布版本会发出“更新已就绪”的提示条消息，并显示“重启以更新”提示条与命令面板操作。账户门禁显示时，该提示条会被隐藏。在 `ready` 或 `installed` 之后执行 `checking`、`downloading` 或 `preparing`，会让该发布版本保持为待处理状态，包括提示条，直到另一个状态落定。重复同一个示例发布版本不会再次发出通知，除非是在回应用户请求的检查。在没有真实更新器的无头窗口中，点击“重启”只会报告更新已关闭；它不会重启或安装示例构建。

`tern ctl state` 会暴露 `update.status`、`release`、`received`、`total` 与 `message`。`asked` 记录尚未完成的、由用户请求的检查；`announced` 记录已通知的发布版本 ID。下载与准备会填充字节计数（`received` 保存目前已下载或写入的字节数）；失败与不支持状态会填充 `message`。在任何状态或更新器出现之前，`status` 为 `off`。

```text
ready
update idle
prefs general
prefs search "update"
shot update-prefs-idle
update failed "Could not reach https://build.stencil.so: connection refused"
shot update-prefs-failed
update waiting
shot update-prefs-waiting
update downloading 42
shot update-prefs-downloading
update ready
wait 7000
shot update-prefs-ready
```

## Kickoff 进度 {#kickoff}

| 命令 | 作用 |
| --- | --- |
| `kickoff packing` | 显示“正在打包 stencil…”。 |
| `kickoff starting` | 显示“正在启动云机器…”。 |
| `kickoff installing` | 显示“正在安装 Tern…”。 |
| `kickoff connecting` | 显示“正在连接…”。 |
| `kickoff uploading <sent> <total>` | 显示已上传与总兆字节数。 |
| `kickoff setting-up <line>` | 显示“正在设置 stencil ·”，后接所给的一行文本。 |
| `kickoff off` | 结束模拟任务并隐藏其进度提示条。 |

Kickoff 命令仅限桌面端。它们为一个名为 `stencil` 的模拟检出显示进度，既不要求 `TERN_KICKOFF` 功能开关，也不要求已登录账户、检出或云连接。它们不会启动机器、上传文件或打开远程会话。每条命令都会稳定等待 450 毫秒；没有任何步骤会等待真实工作或自动推进。账户门禁显示时，提示条保持隐藏。

`uploading` 需要恰好两个以十进制 MB 表示的无符号整数大小（1 MB = 1,000,000 字节），而不是百分比或字节计数。它不要求 `sent` 小于或等于 `total`。`setting-up` 需要恰好一个参数：含空格的一行文本请加引号。其他步骤不接受参数；缺失或多余参数以及未知步骤都会失败。

`tern ctl state` 中没有 kickoff 字段。请用 `tree` 查看可见的进度提示条，或用 `shot` 截取它；用 `kickoff off` 清除模拟进度。

## 参见 {#see-also}

- [脚本](index.md)：运行命令、语法与 fixture 路径。
- [偏好设置](prefs.md)：打开“更新”设置分区。
- [Harness 命令](harness.md)：截图与动画时序。
- [控制命令](control.md)：查看状态与可见树。
- [远程 host](remote.md)：驱动真实的远程连接。
- [调试](../guides/debugging.md#driving-a-window-from-a-script)：驱动正在运行的窗口。
