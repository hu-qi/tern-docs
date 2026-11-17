# 偏好设置 {#preferences}

`prefs` 驱动设置面板：打开某个页面、搜索其中的设置、预览窗口主题，或提供固定的
host 密钥。用它来截取设置界面，并通过 harness 的点击与键盘命令访问控件。

## 打开与关闭 {#opening-and-closing}

| 命令 | 作用 |
| --- | --- |
| `prefs [<page>]` | 打开指定页面并聚焦搜索框。不带页面参数时，使用上次选中的页面；若从未选中过任何页面，则使用 General。 |
| `prefs close` | 关闭面板，保存待处理的编辑，并将焦点返回终端。若已关闭则不做任何事。 |

页面名称均为小写，且区分大小写：

| 页面 | 设置 |
| --- | --- |
| `general` | Shell、agent 命令、标签页与选区。 |
| `appearance` | 主题、外观与界面样式。 |
| `terminal` | 程序 Surface 与内置 profile。 |
| `lenses` | 每个内置命令 lens 的开关。 |
| `databases` | SQLite block。 |
| `notebooks` | Notebook 内核、编辑、运行、输出与保存。仅限桌面端。 |
| `carly` | 模型、记忆、语音与心跳。仅限桌面端。 |
| `keyboard` | 快捷键。 |
| `git` | Git block 与聚焦的仓库。仅限桌面端。 |
| `plugins` | 插件的加载、重载与安装。 |
| `sessions` | 会话守护进程与启动。 |
| `hosts` | 远程 host 与固定密钥。 |
| `advanced` | 文件与一次性优惠。 |

未知的页面或子命令会失败，并列出可用的页面名称。在 iOS 与 web 构建中，`notebooks`、
`carly` 与 `git` 不是有效的页面名称。有效页面或 `close` 之后的尾部参数会被忽略。

`tern ctl state` 在 `prefs.page` 中报告所选页面。面板关闭期间，`prefs` 为 `null`。
关闭面板同时会结束临时的主题预览与提示符预览。

## 搜索与预览 {#searching-and-previewing}

| 命令 | 作用 |
| --- | --- |
| `prefs search [<query>]` | 设置搜索查询词，必要时打开面板。省略查询词或传入 `""` 会清空搜索。 |
| `prefs preview <theme>` | 在整个窗口上预览目录中的某个主题，效果如同悬停其图库磁贴。 |

搜索会在所有页面中查找设置，而不限于当前选中的页面。搜索与预览都会用空格连接其余
所有词；对多词文本加引号以明确其边界。预览要求主题名非空，且当该主题不在目录中时
会以 `no theme called …` 失败。它不会打开面板，也不会保存主题；若想显示其图库磁贴，
请先执行 `prefs appearance`。关闭面板会恢复已保存的主题。

`tern ctl state` 暴露 `prefs.query` 与 `prefs.preview`（所预览的主题名，或 `null`）。
`prefs.prompt_preview` 描述通过 Terminal 页面的控件控制的提示符预览；它没有单独的
`prefs` 子命令。

以下示例遵循 Appearance 的 golden：

```text
ready
prefs appearance
prefs preview "dark-nord"
shot prefs-appearance
prefs close
```

Keyboard 的 golden 会搜索快捷键行以及提及分屏的设置：

```text
ready
prefs keyboard
shot prefs-keyboard-table
prefs search "split"
shot prefs-keyboard
prefs search
prefs close
```

## 固定 host 密钥 {#pinned-host-keys}

| 命令 | 作用 |
| --- | --- |
| `prefs known-hosts <file>` | 让 Hosts 页面从此文件读取固定密钥，而不用 Tern 常规的 `known_hosts` 文件，并刷新面板。 |

文件参数为必需项；其余所有词会以空格连接作为其路径。绝对路径按原样使用。若相对路径
在当前目录中存在，则使用该处的文件；否则会相对 fixture 根目录解析（参见
[Fixture](index.md#fixtures)）。解析该根目录可能失败。此命令不要求解析后的文件存在，
也不会打开 Hosts 页面。

Hosts 的 golden 使用 `prefs known-hosts "goldens/fixtures/known_hosts"`，随后执行
`prefs hosts`。除此之外，无头运行没有默认的固定密钥文件；普通窗口使用 Tern 的常规
文件。所提供的路径不会包含在 `tern ctl state` 中，仅改变它也不会选中页面或改变
`prefs.page`。

## 时序 {#timing}

每个成功的 `prefs` 命令都会稳定 450 ms 的动画时间。它们都不等待 shell、连接或其他
实时操作，也没有针对单个命令的实时超时。这些命令在无头运行与普通窗口中均可工作；
上文所述的页面可用性限制仍然适用。

## 另请参阅 {#see-also}

- [脚本](index.md)：语法、运行脚本与 fixture。
- [Harness 命令](harness.md)：点击设置与截取屏幕截图。
- [终端与面板](terminal.md)：直接设置字体与主题。
- [远程 host](remote.md)：为 Hosts 页面准备 host。
- [调试](../guides/debugging.md)：偏好设置中的插件状态。
