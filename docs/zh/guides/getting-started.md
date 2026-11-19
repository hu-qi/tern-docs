# 快速开始 {#getting-started}

本页从空文件夹出发，做出一个两半区都齐全的可用插件：一个 host 侧 lens，把 `seq`
输出变成摘要与 sparkline；以及一个 window 侧的命令面板命令，用于显示 toast。过程中还会
配置类型检查、重载，以及错误出现的位置。

需要 shell 集成已在面板中启用的 Tern（默认如此），以及用于类型检查的
[luau-lsp](https://github.com/JohnnyMorganz/luau-lsp)。

## 创建包 {#create-the-package}

插件就是一个文件夹，内含 `plugin.toml` 以及该清单所指的 Luau 文件。可以在任意位置创建它；
它不必位于 Tern 的插件文件夹中：

```sh
mkdir -p ~/src/first
cd ~/src/first
```

`plugin.toml` 声明插件，以及 Tern 在任何 Lua 运行之前必须知道的一切：它的 id、两个入口
文件，以及带有其所认领命令行的 lens。

```toml
schema = 1
id = "first"
name = "First"
version = "0.1.0"
description = "A seq lens and a hello command."
host = "host.luau"
window = "window.luau"

[[lenses]]
id = "seq"
match = ["seq *"]
```

`id` 由小写字母、数字与 `-` 组成，以字母开头，最多 32 个字符。`match` 是一组 glob，匹配
命令的程序名与参数；`seq *` 匹配 `seq 12` 与 `seq 1 2 10`，但不匹配单独的 `seq`。
[包与清单](../concepts/packages.md) 列出了每一个键。

`host.luau` 是 host 半区。它运行在面板所在之处（通常是 Tern 的会话守护进程），并实现该
lens：

```lua
--!strict
-- The host half: a lens that reads `seq` output as numbers.

type State = { values: { number } }

local ui = tern.ui

local seq: LensDef<State> = {
	open = function(_run, _cx)
		return { values = {} }
	end,
	line = function(state, l)
		local n = tonumber(l.text)
		if n then
			table.insert(state.values, n)
		end
	end,
	finish = function(_state, _status) end,
	view = function(state)
		if #state.values == 0 then
			return nil -- not numbers: keep the raw output
		end
		local sum = 0
		local series: { { any } } = {}
		for i, n in state.values do
			sum += n
			series[i] = { tostring(i), n }
		end
		return ui.col({
			ui.text({
				ui.span(tostring(#state.values), "strong num"),
				ui.span(" numbers, sum "),
				ui.span(tostring(sum), "num"),
			}),
			ui.spark(series),
		})
	end,
}

tern.lens.define("seq", seq)
```

`window.luau` 是 window 半区。它在该机器上的每个 Tern 窗口中运行，并添加一个命令面板
命令：

```lua
--!strict
-- The window half: a palette command.

tern.command({
	id = "hello",
	title = "Say hello",
	icon = "sparkle",
	run = function(cx)
		local how = if tern.runtime.jit then "native code" else "the interpreter"
		cx:toast("info", "Hello from " .. tern.plugin.name, "running on " .. how)
	end,
})
```

API 就是全局的 `tern`。`require("tern")` 在运行时返回同一张表，但 luau-lsp 会把它报告为
未知的 require，因此这些示例使用全局方式。哪些成员存在于哪个半区，见
[API 参考](../reference/api.md#contexts)；两个半区本身的划分在
[架构](../concepts/architecture.md) 中有说明。

## 链接它 {#link-it}

`tern plugin link` 就地注册文件夹，因此可以原地编辑：

```sh
tern plugin link ~/src/first
```

```text
linked first 0.1.0 → /Users/you/src/first
```

链接会把 `first.path` 写入插件文件夹（`tern plugin dir` 会打印它）。在 Tern 的守护进程
运行时，守护进程会重载其插件，随后命令会打印所有加载失败的插件以及文件夹问题。没有守护
进程时，它打印 `no daemon running; changes apply at next start`。

`tern plugin list` 显示已加载的内容：

```text
first 0.1.0 First — 0 blocks, 1 lenses, window  ready
```

没有守护进程运行时，`list` 只读取文件夹而不运行任何 Lua，因此那里的 `ready` 仅表示清单
解析成功。

## 配置类型检查 {#set-up-type-checking}

`tern plugin types` 会把 API 的类型定义写入文件夹：

```sh
tern plugin types ~/src/first
```

```text
wrote /Users/you/src/first/tern.d.luau
```

把 luau-lsp 指向该文件作为定义文件。在 VS Code 中，把以下内容放入工作区的
`.vscode/settings.json`：

```json
{
	"luau-lsp.platform.type": "standard",
	"luau-lsp.sourcemap.enabled": false,
	"luau-lsp.types.definitionFiles": { "@tern": "tern.d.luau" }
}
```

`definitionFiles` 把名称映射到路径。`platform.type = "standard"` 关闭 Roblox 的全局变量，
sourcemap 设置则阻止 luau-lsp 查找 Rojo 项目。无需 `.luaurc`。在 shell 中，同样的检查是：

```sh
luau-lsp analyze --platform=standard --definitions=@tern=tern.d.luau host.luau window.luau
```

用 `LensDef<State>` 与 `BlockDef<State>` 标注定义，可以标注各处理器共享的状态；
以 `--!strict` 开头可获得完整的检查。升级 Tern 之后要重新生成 `tern.d.luau`。

## 重载 {#reload}

Tern 监视插件文件夹以及每个已链接的文件夹。保存文件会在大约 300 ms 内重载插件的两个
半区，所以多数时候只需保存。要手动重载：

- `tern plugin reload` 重载守护进程的插件，打印与 `list` 相同的行，并在插件失败或文件夹
  有问题时以 1 退出。守护进程把新目录发送给各窗口后，该机器上的窗口会重载自己的半区。
- 命令面板中的 **Reload plugins**，或 Preferences › Plugins 中的 **Reload**，会让窗口
  所附着的每台主机（你的守护进程以及任何远程主机）重载，随后重载该窗口自身的半区。

重载会保留什么、重启什么，见[生命周期与重载](../concepts/lifecycle.md)。

## 看看实际效果 {#see-it-work}

在任意 Tern 面板中运行：

```sh
seq 12
```

输出会变成一个 block，在 sparkline 之上显示 "12 numbers, sum 78"。该 block 的 **Raw**
开关显示原始输出，Tern 始终保留它。运行 `seq 3 x`：`seq` 打印错误而不是数字，`view`
返回 `nil`，于是该 block 显示原始输出。

lens 只能看到 shell 集成上报的命令行，而且只限简单的命令行：`seq 12 | tail -3` 或
`clear; seq 12` 仍然是普通终端输出。[命令 lens](lenses.md) 说明了这些规则。

打开命令面板并键入 "Say hello"。该行位于以插件命名的分组中；选择它会出现 toast
"Hello from First"，其下为 "running on native code"（或 "the interpreter"）。

## 出问题时 {#when-something-goes-wrong}

| 失败内容 | 出现位置 |
| --- | --- |
| `plugin.toml` 无法解析或违反规则 | `tern plugin list`：`problem DIR: <error>`（例如 ``unknown field `bogus`, expected one of …``）；该插件不会加载 |
| 某个入口在加载时抛出错误 | `tern plugin list`：`failed: <first line>`，例如 `failed: runtime error: …/host.luau:2: attempt to index nil with 'y'`；完整回溯在日志中 |
| 上述任一情况在重载之后出现 | 窗口中的 toast："1 plugin has problems" |
| window 半区加载失败 | toast "Plugin First failed to load"，其下为错误 |
| 某处理器抛出错误或超出预算 | toast "Plugin First: seq.view failed"（钩子名称各不相同），附带错误的首行，以及日志行 `plugin handler failed` |

失败的处理器只丢失那一次调用；插件继续运行。超出预算的处理器会被暂停：其钩子在 5 秒内
被跳过，若持续触发则更久。

`print` 与 `tern.log` 写入 Tern 日志，目标为 `tern::plugin`，默认日志过滤器会将其丢弃。
用 `STENCIL_LOG=warn,stencil=info,tern::plugin=debug` 启动 Tern（或守护进程）即可看到它们。
[调试](debugging.md) 涵盖日志、预算与常见错误。

## 下一步 {#next-steps}

- [命令 lens](lenses.md)：认领、行形态、实时视图与状态重建。
- [Block](blocks.md)：程序就是你编写的 Lua 的面板。
- [构建视图](views.md)：节点模型、构建器、动作与样式。
- [Host 钩子与 spawn 过滤器](hooks.md)：响应命令并塑造新的 shell。
- window 半区参见[命令、按键与覆盖](commands.md) 与
  [路由打开与链接](routing.md)。
- 插件准备好交付他人时，参见[分发](distribution.md)。
