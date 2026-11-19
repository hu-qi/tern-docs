# 脚本 {#scripts}

Tern 可以用脚本驱动：脚本是纯文本文件，内含一系列命令，用于打开面板、向 shell 输入、点击、按键、把功能置入给定状态并截图。同一批命令也会通过窗口的控制端点，逐条发送给正在运行的窗口。Tern 自身的截图与回归场景（`crates/tern/goldens/*.txt`）就是脚本。

```text
# A split with git status beside a listing.
size 1280 800
ready
split right
run "git status"
expect "On branch"
focus left
run "ls"
shot split-status
```

## 运行脚本 {#running-scripts}

| 命令 | 作用 |
| --- | --- |
| `tern shot [SCENARIO...] [--out DIR] [--size WxH[@S]] [--scale S] [--theme light\|dark\|both] [--flat]` | 在离屏环境中运行场景，并为每条 `shot` 命令写出 PNG 及其布局 JSON，放入 `DIR/<scenario>/`（默认为 `target/shots/tern`）。`SCENARIO` 是 `.txt` 文件、存放它们的目录，或某个 Tern golden 的名称。 |
| `tern serve [--control EP] [--out DIR]` | 在控制端点上运行一个无头窗口，直到 `quit`。 |
| `tern --control EP [ARGS]` | 一个普通窗口，同时监听控制端点。 |
| `tern ctl [--control EP] COMMAND...` | 向 `serve` 或某个窗口发送一条命令，并打印其 JSON 回复。在 Tern 面板中且不带 `--control` 时：发送给显示该面板的窗口。 |
| `tern ctl [--control EP] --file SCENARIO` | 逐条发送脚本中的命令，每条都在上一条的回复之后发送。 |

`EP` 是 Unix 域套接字路径，或 127.0.0.1 上的 TCP 端口（`0`：任意空闲端口）；`serve` 默认使用 `/tmp/tern.sock`（Windows 上为临时目录中的 `tern.sock`），在 Tern 面板之外运行时 `ctl` 也是如此。`tern help dev` 会打印同样的概要，并列出所有命令族。每条回复是一行 JSON：`{"ok":true,…}` 或 `{"ok":false,"error":"…"}`。

无头运行（`shot`、`serve`）是确定性的：使用从不保存的默认设置、固定时钟、不恢复会话、不加载插件（除非用 `plugins fixtures` 加载 Tern 的测试插件），并以合成测试图案代替真实屏幕。

## 语法 {#syntax}

- 每行一条命令。`#` 开始注释；空行会被跳过。
- 参数以空格分隔。双引号字符串可以包含空格，以及转义序列 `\"`、`\\`、`\n` 与 `\t`。
- 脚本选择器（`click`、`a11y`、`webview` 等）算作一个参数：含空格的请加引号。
- `ctl` 会把自己的词合并成一行命令，因此需要脚本解析器引起来的文本，必须放在 shell 引号内：`tern ctl expect '"On branch"'`。

## 时序 {#timing}

每条命令都会在下一条运行之前落定：动画结束，或命令等待它所启动的工作完成（shell 提示符、git 读取、数据库查询）。依赖真实工作的等待会在 20 秒后放弃，并使脚本失败。`wait MS` 手动推进时间；`freeze-anims` 与 `motion-at MS` 会停止推进，以截取运动过程中的画面。

Tern 在当前平台无法运行的命令会被跳过，并给出警告。某些命令在前置条件不成立时，会停止脚本后续内容，但不判定脚本失败。

## Fixture {#fixtures}

打开 fixture 的命令（`file fixture`, `sqlite fixture`, `board
fixture`, `{fixtures}` in `run`,
等）会从 Tern 的源码树读取它们：在开发者构建中即 `crates/tern/goldens/fixtures`。已发布的 Tern 需要
把 `STENCIL_FIXTURE_ROOT` 设为某个检出的 `crates/tern` 才能使用；接受自定义路径的命令无需该设置。

## 状态 {#state}

`tern ctl state` 以 JSON 打印 Tern 的状态：面板、标签页、会话、设置，以及每种 block 各一个条目（`file_blocks`、`git_blocks`、`sqlite_blocks`、`carly` 等）。脚本用它检查某条命令做了什么；下文各页会说明自己填充的部分。

## 命令族 {#command-families}

脚本混合使用三类命令：harness 的输入与截取命令，每个 Stencil 应用都有；控制命令，只有控制端点会响应；以及 Tern 自身的命令，按其驱动的 Tern 部分分组。

| 命令族 | 命令 | 页面 |
| --- | --- | --- |
| Harness | `size`、`wait`、`move`、`down`、`up`、`click`、`dblclick`、`hover`、`key`、`type`、`wheel`、`swipe`、`touch`、`drop`、`shot`、`record`、`freeze-anims`、`motion-at`、`appearance`、`menu`、`a11y`、`dialog`、`webview`、`spelling` 等 | [Harness 命令](harness.md) |
| 控制 | `dump`、`tree`、`pick`、`state`、`stats`、`layers`、`a11y`、`menus`、`system`、`css`、`perf`、`trace`、`resize`、`quit`、`webcall`、`webreports` | [控制命令](control.md) |
| 终端与面板 | `ready`、`git-read`、`link-read`、`run`、`expect`、`completing`、`split`、`close`、`zoom`、`equalize`、`focus`、`resize`、`tab`、`rename`、`palette`、`find`、`context`、`font`、`ui-font-size`、`font-family`、`font-weight`、`adjust-cell-height`、`adjust-cell-width`、`font-thicken`、`padding`、`ui-font`、`code-font`、`program-icon`、`decorations`、`layout`、`theme`、`themes`、`scroll`、`copy`、`alert`、`inbox`、`peek`、`melt`、`feed`、`surface-play`、`plugins` | [终端与面板](terminal.md) |
| 标签页与导航 | `tabs`、`filter`、`status-bar`、`pane-headers`、`style`、`interface-style`、`picker`、`goto`、`insert-path`、`running`、`drag-pane`、`move-pane`、`tidy`、`previous-tab`、`cross-session-click` | [标签页与导航](navigation.md) |
| 会话与 block | `session`、`sessions`、`block`、`agent-command`、`new-blocks`、`confirm-close` | [会话与 block](sessions.md) |
| 远程 host | `remote` | [远程 host](remote.md) |
| 偏好设置 | `prefs` | [偏好设置](prefs.md) |
| 浏览器 block | `browser` | [浏览器 block](browser.md) |
| 画中画 | `pip` | [画中画](pip.md) |
| Files 面板 | `files` | [Files 面板](files.md) |
| File block | `file` | [File block](file.md) |
| 任务管理器 | `procs` | [任务管理器](procs.md) |
| Screen block | `screen` | [Screen block](screen.md) |
| Git block | `git` | [Git block](git.md) |
| SQLite block | `sqlite` | [SQLite block](sqlite.md) |
| Notebook block | `notebook` | [Notebook block](notebook.md) |
| Board block | `board` | [Board block](board.md) |
| Canvas block | `canvas` | [Canvas block](canvas.md) |
| Profile block | `profile` | [Profile block](profile.md) |
| 账户、更新与云端 | `account`、`update`、`kickoff` | [账户、更新与 Kickoff](status.md) |
| Carly | `carly` | [Carly](carly.md) |

Git、notebook、Carly 与 kickoff 命令仅在桌面版中运行。

## 参见 {#see-also}

- [调试](../guides/debugging.md#driving-a-window-from-a-script)：用脚本测试插件。
- [命令行](../reference/cli.md)：`tern plugin` 命令。
