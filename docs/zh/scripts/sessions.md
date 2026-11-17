# 会话与 block {#sessions-and-blocks}

这些命令把标签页归入具名会话、在会话之间切换、保护工作免遭关闭，并选择新终端 block 运行什么。用它来搭建工作区，或在脚本中为 agent block 指定一条可预期的命令。

## 会话 {#sessions}

| 命令 | 作用 |
| --- | --- |
| `session new [<name>]` | 创建会话，切换到该会话并打开它的第一个标签页。 |
| `session switch <name>` | 切换到名称匹配的第一个会话，忽略 ASCII 字母大小写。 |
| `session rename <name>` | 重命名当前会话。 |
| `session close` | 请求关闭当前会话及其各标签页中的程序。 |
| `session lock` | 切换当前会话的锁定状态。 |
| `session end-on-success` | 使聚焦的 block 在其程序以状态 0 退出后结束其会话，与 `tern new … --end-on-success` 启动一个会话的方式相同。 |
| `sessions [<query>]` | 打开命令面板的 Sessions 范围，并填入查询内容。 |

名称与查询中含空格时需加引号。省略新建会话的名称或将其留空，会生成一个唯一的随机两词名称。新会话初始为未锁定；其第一个标签页使用新标签页目录与 `new-blocks` 设置。显式名称不必唯一。切换到未知名称会以 `no session named …` 失败；切换与重命名要求名称非空。未知的 `session` 子命令会失败。`session close`、`session lock` 与 `session end-on-success` 不接受参数，不过解析器对它们会忽略尾随的词。当前会话没有标签页时，`session end-on-success` 以 `no focused block` 失败。被如此标记的 block 若以其他状态退出，则像其他 block 一样保留并显示其状态；在锁定的会话中，成功只关闭该 block。

关闭当前会话会回到窗口此前显示的会话；若这些都不存在，则选择下一个会话，没有下一个会话时选择上一个。关闭唯一的会话后，它仍然存在，只是没有标签页。锁定会拒绝关闭该会话及其标签页与 block，并显示 toast，而不是让脚本失败。再次切换锁定即可解锁。确认对话框与未保存数据的询问可能使会话保持打开；命令回复成功并不代表它已关闭。

`session close` 与 `sessions` 会等待 450 ms 结算，而不等待问题或命令面板选择的回答。其他命令按真实时间等待可见程序面板回到提示符或已结束，然后结算 450 ms。正常的 20 秒超时适用；繁忙的会话可能使切换到它的操作超时。

在 `tern ctl state` 中，`sessions` 列出每个会话的 `name`、标签页数量与 `current` 标志。`tabs`、`panes` 与 `focused` 显示结果工作区。锁定状态不在 state 中暴露。`palette` 保存切换器的查询，`palette_scope` 标识其范围。

## 关闭策略 {#closing-policy}

| 命令 | 作用 |
| --- | --- |
| `confirm-close never\|running\|always` | 设置关闭 block、标签页、会话或窗口时何时请求确认。 |

默认值为 `running`：当除空闲 shell 之外的程序将要结束时询问，包括正在运行的命令、编辑器或处于回合中途的 agent。空闲 shell 与回合之间的 agent 关闭时不会询问。`always` 每次都询问；`never` 跳过此确认。值无效或缺失会失败。

这不会绕过锁定，也不会绕过关于未保存的数据库或笔记本数据的询问。在无头运行中使用 harness 的对话框命令来回答问题。该策略同样适用于退出。它不在 `tern ctl state` 中暴露；请在答复后观察受影响的 `sessions` 与 `tabs`。设置它使用与上文相同的提示等待与 450 ms 结算。

## Shell 与 agent block {#shell-and-agent-blocks}

| 命令 | 作用 |
| --- | --- |
| `block shell\|agent` | 打开显式选定类型的 block 并聚焦它。 |
| `agent-command <command>` | 设置后续 agent block 通过登录 shell 运行的命令。 |
| `new-blocks shell\|agent` | 选择新标签页与分屏所打开的类型。 |

shell block 在聚焦面板旁打开，沿用其目录；没有打开的标签页时，它会获得自己的标签页。Agent block 遵循 agent 放置偏好：默认向右分屏，也可选择新建标签页或替换该标签页唯一的空闲 shell。显式的 `block` 命令忽略 `new-blocks`。

新标签页与分屏默认使用 `shell`。默认 agent 命令为 `omp`；为截图场景设置一条确定性的命令，而不要依赖已安装的 agent。更改 `agent-command` 不会重启已有的 block。它要求非空文本。`block` 与 `new-blocks` 只接受 `shell` 或 `agent`；缺失、多余或无效的词会失败。

这些命令按真实时间等待可见程序面板回到提示符或已结束，然后结算 450 ms，并适用正常的 20 秒超时。因此，让程序保持繁忙的命令可能超时。这一组命令都不限于仅桌面或仅无头使用。

state 会在 `tabs[].panes`、`panes` 与 `focused` 中显示新的 block（包括其 `label`、`running`、`prompt` 与 `error`）。配置的 agent 命令与新 block 类型都不直接在 `tern ctl state` 中暴露。

## 示例 {#examples}

创建会话并过滤切换器，与 sessions golden（基准用例）一致：

```text
ready
session rename "tern"
tab new
session new "website"
tab new
tab new
session new
run "printf 'deploying…\\n'"
session switch "website"
shot sessions-tabs
sessions "web"
shot sessions-filter
```

打开 shell 与 agent block，使用 blocks golden（基准用例）所用的确定性命令：

```text
ready
agent-command "printf '\\033[1m✻ Agent\\033[0m ready in %s\\n\\n> ' \"$PWD\"; sleep 600"
block shell
block agent
ready
shot blocks
```

## 另见 {#see-also}

- [终端与面板](terminal.md)：标签页、分屏与提示符等待。
- [标签页与导航](navigation.md)：显示与浏览会话标签页。
- [Harness 命令](harness.md)：回答对话框与截图。
- [脚本](index.md)：语法、时序与控制端点。
- [调试](../guides/debugging.md)：用脚本驱动窗口。
