# Carly 命令 {#carly}

Carly 命令让助手进入对话、工具、语音与定时任务状态，供脚本与截图使用，或运行
她真实的 Tern 工具。用模拟轮次在没有 omp 的情况下演练她的 UI，用工具调用来在
没有 agent 的情况下检查或改变窗口。这一组命令仅限桌面版；无头窗口从不启动 omp。

## 打开与附件 {#opening-and-attachments}

| 命令 | 作用 |
| --- | --- |
| `carly open` | 按她正常的打开行为打开 Carly。 |
| `carly close` | 关闭 Carly。 |
| `carly new` | 开始新的对话，重置其 Lua 环境与 canvas 处理函数。 |
| `carly paste text "<text>"` | 把剪贴板文本粘贴到她的输入框。 |
| `carly paste image <width> <height>` | 粘贴指定像素尺寸的纯灰色位图。 |
| `carly paste file "<path>"` | 从给定的剪贴板路径粘贴文件附件。 |

如果她的输入框尚未接受粘贴，`paste` 会先打开 Carly。图像尺寸为无符号 32 位
整数；文本与文件路径必须非空。文件形式提供的是剪贴板路径，而不是打开文件 block。
对话重置不会移除持久的 canvas。

查看 `state.carly.open`、`peek`、`target`、`field` 与 `attachments`，了解最终的
呈现与输入状态。

## 对话与步骤 {#conversation-and-steps}

| 命令 | 作用 |
| --- | --- |
| `carly ask "<text>"` | 提交一个问题，并把它的轮次标记为已开始。 |
| `carly queue "<text>"` | 提交问题，但不模拟其开始。 |
| `carly stream "<markdown>"` | 为进行中的轮次提供到目前为止的回答。 |
| `carly reply "<markdown>"` | 以最终回答开始并结束一个用户轮次。 |
| `carly fail "<message>"` | 以错误结束用户轮次，包括等待中的问题。 |
| `carly step run\|ok\|bad ["<label>"]` | 记录一个运行中、已完成或失败的工具步骤。 |
| `carly command run\|ok\|bad ["<command line>"]` | 记录相同的步骤状态，显示为 shell 命令。 |
| `carly history "<file>"` | 提供 omp 在此窗口之前保留的内容：omp 消息的 JSON 数组，与其 RPC `get_messages` 的应答一致。 |

这些命令提供对话事件；`command` 不会执行其命令行。重复同一步骤标签会更新该
步骤。`ask`、`queue`、`stream`、`reply` 与 `fail` 的文本必须包含非空白字符；
步骤标签可以为空。在真实窗口中，提交问题也可能送达正在运行的 agent；模拟不会
等待 agent 的回答。

`state.carly.phase` 描述当前活动。`turns` 保存整段对话，最早的在前，包含每个
轮次的 `kind`（`asked`、`spoken`、`task`、`alert` 或 `flush`）、`past`（表示它
来自 `history`）、`started`、`task`、`asked`、`steps`、`unfolded`、`answer`、
`error` 与 `done`。步骤状态值为 `running`、`done` 与 `failed`。
`state.carly.past` 为 `unasked`、`loading`、`loaded` 或 `{ "failed": … }`：
表示 Carly block（命令面板中的 New Carly block）是否已取得此窗口之前的对话。
无头窗口从不向 omp 请求它：已显示的 Carly block 会把它标记为已加载，`history`
则提供一个。

```text
ready
carly open
carly ask "what sessions did I close today?"
carly step ok "Find session actions"
carly command run "ls -la ~/Library/Application Support/Tern"
shot carly-working
carly command ok "ls -la ~/Library/Application Support/Tern"
carly reply "You closed **3 sessions** today."
shot carly-answer
```

这与 `carly-steps` golden 中的对话与步骤进展一致。`carly-block` golden 显示了
一个 Carly block 中的对话，其中较早的部分来自
`carly history "goldens/fixtures/carly-history.json"`。

## 真实工具与断言 {#real-tools-and-assertions}

| 命令 | 作用 |
| --- | --- |
| `carly tool <name> [<json>]` | 运行真实的 Tern 工具并保存其回答。 |
| `carly lua "<code>"` | 运行 `lua` 工具，并在对话轮次中显示其字面输出。 |
| `carly context` | 保存此刻提问会携带的上下文。 |
| `carly last ["<contains>"]` | 显示最后一次工具回答或排队的 canvas 请求，可选地断言其中包含某个子串。 |
| `carly ok` | 断言最后一次工具回答存在且不是错误。 |

工具参数默认为 `{}`。无效的 JSON 会让命令失败。未知工具名与工具执行错误会产生
错误回答，而不是让脚本失败：使用 `carly ok` 可以把它们变成断言。Lua 代码必须
非空；其环境会一直保留，直到执行 `carly new`。

可用的工具名如下：

| 工具 | 作用 |
| --- | --- |
| `inspect` | 在不移动焦点的情况下读取结构化的窗口、会话、host、标签页、面板、agent、设置、进程或 block 数据。 |
| `configure` | 通过正常的保存路径应用经过校验的设置补丁。 |
| `actions` | 发现内置动作与插件动作，或按 id 或精确标签运行动作。 |
| `processes` | 列出本机采样的进程，或向正数 PID 发送信号。 |
| `session` | 列出、切换、创建、重命名或关闭会话。 |
| `arrange` | 重命名、重新着色、重排与重新分组标签页和 block。 |
| `read_block` | 读取 block 的可见内容，包括未保存的文件文本与原生 block 数据。 |
| `send_input` | 向终端发送按键、文本，可选发送 Enter，可选等待输出。 |
| `run_command` | 按 id 通过其正常处理函数运行 Tern 命令。 |
| `canvas_read` | 列出 canvas block 的形状（id、页面框、文本、样式）、其视图、选择与步骤数。 |
| `canvas_shot` | 把 canvas 区域（默认：该 block 显示的内容）渲染为模型可见的 PNG。 |
| `canvas_edit` | 按 id 添加、移动、调整大小、旋转、重设样式、改变类型、分组、排列或删除形状，作为一个撤销步骤；任一编辑失败则全部不生效。 |
| `canvas_history` | 列出、撤销或重做 canvas block 的步骤。 |
| `lua` | 针对 Carly 的 Tern API 与已注册的插件导出运行 Lua。 |

这些是真实操作，而不是模拟的工具步骤。关闭会话会结束其程序；在普通窗口中，
设置可能会持久保存。进程工具针对本机，而不是远程 host；Windows 仅支持
terminate 与 kill 信号。

待处理的工具会在脚本继续之前稳定下来，使用真实经过的时间。进程检查最多等待
10 秒以取得第一个采样。`send_input` 的 `wait_ms` 默认为零，上限为 120000；
提交的命令在 shell 完成通知到达后、且至少经过 250 ms 时可能提前结束。到达
截止时间时会返回终端的最后几行，可能报告命令仍在运行，而不是把截止时间当作
错误。目标已关闭会返回错误回答。脚本 harness 通用的 20 秒稳定超时仍适用于
待处理命令。

`state.carly.last_tool` 保存 `{ "text": …, "error": … }`。`context` 使用 Carly
的目标 block，缺省时回退到聚焦 block。`last` 在没有回答、或其文本不含请求的
子串时失败；它可以显示错误回答。`ok` 在回答缺失或为错误时失败。

```text
ready
carly open
carly lua "scratch = 41; print('hello', 'Lua'); return {answer = scratch + 1, ok = true}"
carly ok
carly lua "scratch += 1; return scratch"
carly last "42"
shot carly-lua-persistence
carly new
carly lua "return scratch == nil"
carly ok
```

这使用了 `carly-lua` 所演练的持久 Lua 状态与重置。
她的 Lua API 参见 [扩展 Carly](../guides/carly.md)。

## 语音 {#voice}

| 命令 | 作用 |
| --- | --- |
| `carly voice connecting\|listening\|speaking\|working\|muted\|error\|off [<level>]` | 设置语音呈现与计量电平；`off` 清除语音状态。 |
| `carly heard "<text>"` | 提供最终的语音识别转写文本。 |
| `carly said "<text>"` | 提供最终的口头回答文本。 |

这些命令模拟语音事件，不会连接麦克风或语音服务。电平默认为 `0.0`，即使其参数
不是数字也是如此。视觉计量条把它限制在 `1.0`；`state.carly.voice.level` 保留
所给的值。关闭时 `state.carly.voice` 为 null，否则包含 `phase` 与 `level`；
语音对话事件也会影响 `turns`。`heard` 与 `said` 要求非空白文本。

## 定时任务 {#scheduled-tasks}

| 命令 | 作用 |
| --- | --- |
| `carly task add <json>` | 按调度 API 的 JSON 规格校验并添加任务，归属记为用户。 |
| `carly task fire <id>` | 立即触发任务的检查或模型轮次。 |
| `carly task run <id> ["<text>"]` | 模拟该任务轮次成功完成，必要时先启动它。 |
| `carly task fail <id> ["<message>"]` | 模拟任务轮次失败，必要时先启动它。 |
| `carly task event command_finished <pane> <status> ["<line>"]` | 向定时任务的检查投递模拟的 shell 完成事件。 |

任务 id 为无符号 32 位整数；`0` 是内置心跳。面板 id 为无符号 64 位整数，
退出状态为有符号 32 位整数。完成文本、错误消息与命令行可以为空。
模拟的完成事件持续固定的 1200 ms；它不会运行 shell 命令。

`add` 的规格要求字符串 `title`，以及 `when` 或 `on` 之一，不能两者都给。它接受
`id`、`check`、`prompt`、`pane`、`once`、`paused` 与事件的 `expires`。对一次性
触发与事件触发，`once` 默认为 true，其他情况为 false；`paused` 默认为 false。
事件过期默认为 `12h`，且必须落在未来七天之内。任务 id `0` 不能以此方式添加或
替换。无效的规格与检查会让命令失败；检查会在任务保存之前先编译并试运行。
新的 id 在 `state.carly.last_tool.text` 中返回。

Carly 忙碌时，`fire` 保留重试行为；它不等待模型回答。`run` 与 `fail` 把完成
结果投递给指名的任务，而不是排队的用户问题。`HEARTBEAT_OK` 是静默完成。
成功的一次性任务会结束其调度；失败会记录失败结果。普通窗口会持久保存调度；
临时的无头会话不会。结果参见 `state.carly.tasks`、`peek` 与带任务标记的
`turns`，调度规格参见 [扩展 Carly](../guides/carly.md)。

## 另见 {#see-also}

- [脚本](index.md)：运行、语法与稳定规则。
- [扩展 Carly](../guides/carly.md)：工具、Lua 与定时检查。
- [会话与 block](sessions.md)：Carly 使用的 block。
- [Harness 命令](harness.md)：输入与截图。
