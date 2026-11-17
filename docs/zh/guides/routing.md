# 路由打开与链接 {#routing-opens-and-links}

路由让插件的 window 半区决定打开文件或跟随链接时会发生什么——改为打开插件的 block、
重定向到另一个 URL 或路径，或完全自行处理。路由在 Tern 的内置处理之前运行，
因此可以认领不存在的路径，以及 Tern 不认识的 URL scheme。

```lua
tern.route.open(function(req, _cx)
	if string.match(req.path, "%.tfplan$") then
		return { block = "terraform.plan", args = { req.path } }
	end
	return nil
end)
```

## 两种路由 {#two-routes}

| 路由 | 询问的内容 | 处理函数 |
| --- | --- | --- |
| `tern.route.open(fn)` | 用户请求打开的文件。 | `fn(req, cx) -> decision?` |
| `tern.route.link(fn)` | 在面板与 block 中跟随的链接，以及系统交给 Tern 的 URL。 | `fn(link, cx) -> decision?` |

两者都只在 window 半区生效。一个插件可以各注册多个处理函数。
处理函数先按插件 id 顺序、再按插件内的注册顺序运行，直到有一个返回决策；
`nil` 表示交给下一个。当所有处理函数都放行时，运行 Tern 的内置处理。

每次处理函数调用都有 50 ms 的 window 预算，并获得一个新的 `cx`。出错的处理函数
（或返回的不是表、也不是 `nil` 的处理函数）会以 `Plugin <name>: route.open failed`
（或 `route.link`）弹出提示，并按 `nil` 计；随后运行下一个处理函数。

## 打开请求 {#open-requests}

`req` 描述一个即将打开的文件：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `path` | `string` | 绝对路径；文件存在时为规范路径（已解析符号链接与 `..`）。 |
| `line` | `number?` | 要显示的行号，从 1 开始。 |
| `col` | `number?` | 该行上的列号，从 1 开始。 |
| `host` | `string` | 文件所在 host 的名称。 |
| `how` | `string` | 它会在哪里打开（见下文）。 |
| `origin` | `string` | 由什么发起（见下文）。 |

`how` 说明内置打开会把文件放在哪里：

| `how` | 放置位置 |
| --- | --- |
| `default` | Tern 惯常的位置：已在显示该文件的 block，否则按本次打开的情境新建 block。 |
| `beside` | 聚焦面板旁的分屏。 |
| `below` | 它下方的分屏。 |
| `split` | 手势选定的分屏（拖放到面板边缘）。在决策中，`split` 表示 `beside`。 |
| `tab` | 新的标签页。 |
| `replace` | 替换它来源的 block（文件 block 中的链接、peek）。 |
| `over` | 聚焦面板所在槽位中的新 block，该面板会被暂存，待 block 关闭后再放回该槽位。Tern 自身的打开从不请求它；`path` 决策的 `how` 可以使用它。 |
| `preview` | 标签页的预览 block。 |

`origin` 指明经由 UI 的路径：

| `origin` | 产生自 |
| --- | --- |
| `palette` | 从命令面板打开文件（Open file…）。 |
| `files` | 从 Files 面板打开文件。 |
| `drop` | 把文件拖放到窗口。 |
| `link` | 在终端中点击的文件路径；面板中没有被任何 `tern.route.link` 处理函数认领的文件链接；文件 block 中的链接；打开 peek 的文件。 |
| `system` | 系统：Finder 的 Open With、拖放到 Dock 图标、`--open-file`、第二次启动。 |
| `cli` | 在面板中执行 `tern open`（见[下文](#tern-open-from-a-pane)）。 |
| `carly` | 由 Carly 的窗口上下文打开的文件；URL 打开会先询问 `tern.route.link`。 |

终端中打印的路径会直接进入 `tern.route.open`（origin 为 `link`）；它是路径而不是
URL，因此 `tern.route.link` 永远看不到它。`file://` URL 或指向文件的超链接属于链接：
`tern.route.link` 先看到它，当没有处理函数认领时，再由 `tern.route.open` 看到该文件。

Tern 自行发起的打开不经过路由：Files 面板的预览、git 与 board block 打开文件、
Open logs 与 app state、“Open with” 菜单项、`tern db`，以及插件处理函数发起的
每个 `cx:open`。

## 链接请求 {#link-requests}

`link` 描述一个正在被跟随的链接：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `url` | `string` | 书写形式的 URL：`https://…`、`file://…`、自定义 scheme，或链接所指的路径。 |
| `pane` | `number?` | 链接所在的面板；不来自任何面板时为 `nil`。 |
| `mods` | 表 | 按住的修饰键：`cmd`（⌘；PC 上为 Super）、`alt`、`shift`、`ctrl`，各为布尔值。 |

以下情形会询问 `tern.route.link`：

- 终端面板中的链接点击（URL 与 OSC 8 超链接）；
- 面板链接菜单的 “Open file”、“Open link” 与 “Open link in browser” 项
  （“Open link in Tern” 直接打开浏览器 block）；
- 文件 block 与其他 surface 中的 URL 链接；
- host 半区通过其 effect `cx:open(target)` 请求的打开；
- 系统交给 Tern 的 URL（注册给 Tern 的某个 scheme 的链接）；
- `tern.route.open` 决策中的 `url`。

## 决策 {#decisions}

决策是一个表，其中设置 `block`、`url`、`path` 或 `handled` 之一。
设置多项时，以该顺序中的第一个为准。四项都未设置的表属于错误：
`a route decision sets block, url, path or handled = true`。

| 决策 | 来自 `tern.route.open` | 来自 `tern.route.link` |
| --- | --- | --- |
| `nil` | 下一个处理函数，然后是内置打开。 | 下一个处理函数，然后是内置链接处理。 |
| `{block = "<plugin>.<block>", args = {…}}` | 在文件所在 host（`req.host`）上以 `args`（默认 `{}`）打开该插件 block，位于聚焦面板旁（当 `req.how` 为 `tab` 或 `below` 时，位于新标签页中或其下方），起始目录为文件所在文件夹。 | 在链接所在面板的 host 上以 `args` 打开该插件 block，位于该面板旁，起始目录为其所在目录。 |
| `{url = "…"}` | 改为跟随该 URL：`tern.route.link` 的处理函数看到一次，然后进入内置链接处理，后者不会把文件 URL 再送经 `tern.route.open` 路由。 | 用内置处理跟随该 URL；不再有任何路由看到它。 |
| `{path = "…", how? = …}` | 用内置打开打开该路径，给出 `how` 时按其放置，否则按 `req.how`。 | 在面板所在 host 上以文件 block 打开该路径，给出 `how` 时按其放置，否则放在默认位置（按住 ⌥ 时在面板旁）。 |
| `{handled = true}` | 不再运行其他内容。 | 不再运行其他内容。 |

决策中的 `how` 若不是这七个名称之一，属于错误。`block` 类型必须是该 block 打开
所在 host 上某个 Ready 插件的 block 类型：对 `tern.route.open` 是文件所在的 host，
对 `tern.route.link` 是链接所在面板的 host。远程 host 上的文件会在那台机器上打开
block，因此该机器必须安装插件的 host 半区。该 host 上没有 Ready 插件定义该类型时，
不会打开任何内容（内置处理也不会运行），并弹出错误提示 “Could not open the block”，
其下为 `No plugin on <host>
defines block type <kind>`。

`handled` 表示插件已完成这次打开所需的一切，通常通过 `cx`。它必须恰好为 `true`；
`{handled = false}` 属于错误，而不是放行。

## “Open with” 菜单 {#open-with-menus}

在清单中声明 `files` glob 的 block 类型，会在文件 block 的 ⋯ 菜单中、以及 Files
面板针对匹配文件的上下文菜单中，获得一个 “Open with `<title>`” 项，而不会接管
所有打开：

```toml
[[blocks]]
id = "plan"
title = "Terraform Plan"
files = ["*.tfplan", "*.plan.json"]
```

glob 只匹配文件名，支持 `*` 与 `?`，按 ASCII 大小写不敏感。这些项列出当前会话
host 上 Ready 插件的 block 类型，且只对该 host 上的文件出现。选择其中一项会在
聚焦面板旁、文件所在文件夹中以 `args = {<absolute path>}` 打开该 block。
这些打开不经过 `tern.route.open`。

<!-- 原文在该行内代码处换行，校验解析出的跨行片段按原文保留：`. These opens don't pass through ` -->

当 block 只是查看文件的多种方式之一时，优先使用 `files`；当插件的视图应当成为
默认时，使用路由。

## 在面板中执行 `tern open` {#tern-open-from-a-pane}

在面板中执行 `tern open PATH` 会在显示该面板的 Tern 窗口中打开文件，包含路由：

- 在会话守护进程的面板中（通常情况），命令与该守护进程通信，守护进程把请求转交
  给一个接受打开的窗口：显示该会话时为聚焦窗口，否则为最近连接的窗口。该窗口以
  origin `cli` 打开每个文件，先运行路由，并应答该命令。
- 在未运行守护进程的窗口的面板中，命令与窗口自身的 socket 通信，结果相同。
- 当没有窗口接受守护进程的打开请求时，守护进程自行按会话布局的一次编辑打开文件，
  所有已附加窗口都会采纳（若没有窗口显示该守护进程，会为其启动一个窗口）。
  没有 window 半区运行这次打开，因此没有路由看到它。

该命令报告已打开的 block，`--wait` 等待它们关闭。返回 `{block = …}` 的路由会把
该 block 交给命令等待。返回 `{url = …}` 或 `{handled = true}` 的路由不留下 block，
命令会以 `PATH cannot open in a file block` 失败。由于 `EDITOR='tern open --wait'`
是 Tern 编辑提交信息的方式，除非插件为这些打开提供 block，否则不要干预
`origin == "cli"` 的打开。

## 递归 {#recursion}

路由处理函数运行期间，所有插件的路由与覆盖都在窗口之外
（[递归防护](commands.md#the-recursion-guard)）。处理函数可以调用
`cx:open(req.path)` 对它被询问的路径执行内置打开，或调用
`cx:open(other, "beside")` 打开另一个文件，而自身的路由看不到结果。
处理函数通过 `cx:command` 引发的打开同样如此。

## 示例 {#worked-examples}

### 把某种文件类型当作 block，但用户要求文本时除外 {#a-file-type-as-a-block-except-where-the-user-asked-for-text}

```lua
local claimed = { files = true, palette = true, link = true, system = true }

tern.route.open(function(req, _cx)
	if not string.match(req.path, "%.ipynb$") then
		return nil
	end
	if not claimed[req.origin] or req.how == "replace" then
		return nil -- `tern open`, drops and in-place opens stay text
	end
	return { block = "nb.viewer", args = { req.path } }
end)
```

### 重定向与认领链接 {#redirecting-and-claiming-links}

```lua
tern.route.link(function(link, cx)
	-- Shift-click copies a web link instead of following it.
	if link.mods.shift and string.match(link.url, "^https?://") then
		cx:copy(link.url)
		cx:toast("success", "Link copied", link.url)
		return { handled = true }
	end
	-- A private scheme: ticket://PROJ-123 opens the tracker.
	local key = string.match(link.url, "^ticket://(%u+%-%d+)$")
	if key then
		return { url = "https://tracker.example.com/browse/" .. key }
	end
	return nil
end)
```

程序可以把任意 URL（包括自定义 scheme）标记为 OSC 8 超链接；点击它时会像
其他链接一样询问 `tern.route.link`。

### 打开源码而不是构建产物 {#opening-the-source-instead-of-the-build-output}

```lua
tern.route.open(function(req, _cx)
	local root, rest = string.match(req.path, "^(.*)/dist/(.-)%.js$")
	if root == nil or rest == nil then
		return nil
	end
	local source = root .. "/src/" .. rest .. ".ts"
	if tern.fs.exists(source) then
		return { path = source, how = "beside" }
	end
	return nil
end)
```

`tern.fs` 读取窗口所在机器的磁盘。`host` 指向远程 host 的请求针对的是远程主机上的
文件，因此对远程文件而言，该检查回答的是错误的机器。

## 另见 {#see-also}

- [Block](blocks.md)：定义路由所打开的 block 类型。
- [命令、按键与覆盖](commands.md)：window `cx` 与递归防护。
- [Window API](../reference/api-window.md)：`OpenRequest`、`LinkRequest` 与
  `RouteDecision`。
- [清单参考](../reference/manifest.md)：`[[blocks]] files`。
