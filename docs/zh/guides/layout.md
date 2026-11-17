# 布局与工作区 {#layout-and-workspaces}

插件的 window 半区可以跟随窗口中发生的事情（焦点移动、面板与标签页的出现与消失、命令
运行），也可以安排窗口本身：打开标签页、拆分面板，移动、调整大小与关闭它们，并构建完整
的工作区。两者都通过窗口的 `cx` 进行。

```lua
tern.on("window_start", function(cx)
	local pane = cx.layout:new_tab({ cwd = "/tmp" })
	if pane then
		cx.layout:split(pane, "down", { command = "htop" })
	end
end)
```

## 窗口事件 {#window-events}

window 半区中的 `tern.on(name, fn)` 订阅窗口事件。未知的名称会抛出
`tern.on: unknown window event`。

| 事件 | 处理函数 | 时机 |
| --- | --- | --- |
| `window_start` | `fn(cx)` | 每个窗口与每个插件一次，在窗口的会话稳定之后（恢复或全新启动）。 |
| `focus` | `fn({pane, tab}, cx)` | 聚焦的面板发生变化。 |
| `pane_created` | `fn({pane}, cx)` | 添加了任意类型的面板（也包括浏览器 block）。 |
| `pane_closed` | `fn({pane}, cx)` | 某个面板消失。 |
| `tab_created` | `fn({tab}, cx)` | 打开了标签页。 |
| `tab_closed` | `fn({tab}, cx)` | 某个标签页消失。 |
| `command_started` | `fn({pane, line}, cx)` | shell 开始运行一行命令。 |
| `command_finished` | `fn({pane, line, status, took_ms}, cx)` | 命令行以退出码 `status` 结束，耗时 `took_ms` 毫秒。 |
| `cwd` | `fn({pane, path}, cx)` | 面板的工作目录发生变化。 |
| `title` | `fn({pane, title}, cx)` | 面板中的程序设置了标题。 |

事件描述该窗口的会话所看到的内容，远程 host 的面板也包括在内；每个窗口投递自己的事件。
它们随会话变化而入队，在窗口绘制之后投递，绝不在会话变化的过程中投递，并按插件 id 顺序
投递给每个插件的处理函数。`command_started` 与 `command_finished` 需要能报告命令行的
shell，正如 Tern 的 shell 集成那样。

window 半区的 `command_started` 没有 `cwd`，这与同名的 [host 钩子](hooks.md) 不同；
请从 `cx.session:panes()` 或 `cwd` 事件读取目录。host 半区在面板运行的位置看到同样的
shell 事件，且只看到一次；window 半区则在每个显示该会话的窗口中都能看到。

`window_start` 对每个插件在每个窗口中运行一次。重载时，已在该窗口运行过它的插件不会再次
运行，但新增的插件（刚安装或刚启用）会运行。打开第二个窗口时也会在那里运行。响应事件
而改动会话的处理函数会引起更多事件：聚焦另一个面板的 `focus` 处理函数会在下一次投递时
再次收到 `focus`，因此要防止循环。

## 窗口的 `cx` {#the-window-cx}

每个 window 处理函数都会收到 `cx` 作为最后一个参数：事件处理函数、命令、快捷键、覆盖、
路由与 `available` 检查。它只在收到它的那次调用期间有效。保存在上值中稍后使用的 `cx`
会抛出错误。

计时器、进程与 fetch 回调不会继承启动它们的调用的 `cx`；它们会收到一个新的 `cx`：

```lua
tern.on("window_start", function(_cx)
	tern.timer(2000, function(cx)
		if cx then
			cx:toast("info", "Two seconds in")
		end
	end)
end)
```

计时器的 `cx` 参数被标注为可选，因为 host 计时器收不到它；在 window 半区中它总是存在。
参见 [文件、进程与存储](io.md#timers-and-time)。

## 读取会话 {#reading-the-session}

`cx.session` 读取窗口的面板与标签页：

| 方法 | 返回值 |
| --- | --- |
| `cx.session:panes()` | 某个标签页中的每个面板：各为 `{pane, cwd, program, title, busy}`（未知时 `cwd` 为 `""`；`busy` 表示有正在运行的 shell 集成命令）。 |
| `cx.session:tabs()` | 每个标签页：`{id, name?, cwd, program, title, panes, busy}`，描述该标签页聚焦的面板。 |
| `cx.session:focused()` | 聚焦面板的 id，或 `nil`。 |
| `cx.session:resolve(spec)` | `spec` 指定的面板，或 `nil`。 |

`resolve` 命名面板的方式与 `tern` 脚本命名 block 相同：`"@focused"`、写作字符串的面板
id、精确标题、任意大小写的标题，然后是程序名。多个匹配中，位于活动标签页的那个优先。

### id {#ids}

面板与标签页的 id 是 Lua 数字。远程 host 的面板在其 id 的高位携带 host 信息；Tern 会
为 Lua 把这个标记下移，使 id 在 double 中保持精确。请把 id 完全按收到时的样子传回
`cx`，并且不要跨窗口比较 id，也不要把它与 host 半区或 `tern` 脚本中的 id 比较：远程
面板的 id 在那里写法不同。

## 安排面板 {#arranging-panes}

`cx.layout` 改变窗口布局：

| 方法 | 作用 |
| --- | --- |
| `cx.layout:new_tab(launch?)` | 在当前会话中打开一个运行 `launch` 的标签页，使其成为活动页，返回其面板。 |
| `cx.layout:split(target, dir, launch?)` | 用新面板拆分 `target` 面板的 `dir` 一侧，新面板运行 `launch`；新面板获得所在标签页的焦点。返回新面板。 |
| `cx.layout:focus(pane)` | 聚焦此窗口中的某个面板。 |
| `cx.layout:close(pane)` | 关闭某个面板。 |
| `cx.layout:move(pane, target, dir)` | 把 `pane` 移到 `target` 的 `dir` 一侧。任一面板缺失或它们位于不同 host 时返回 `false`。 |
| `cx.layout:resize(pane, dir, cells)` | 把面板最近的分隔线朝 `dir` 移动约 `cells` 个面板单元格；负数则向相反方向移动。没有朝该方向的分屏时返回 `false`。 |
| `cx.layout:tab(spec)` | 构建一个工作区标签页（见下文）；返回其标签页 id。 |

`dir` 为 `"right"`、`"down"`、`"left"` 或 `"up"`；其他任何值都会抛出
`unknown direction`。

`new_tab` 与 `split` 在 launch 指定了 host 缺少的 block 类型时返回 `nil`；`split`
在 `target` 不在任何标签页中时也如此。新标签页在当前会话的 host 上启动，并使用新标签页
本会使用的目录（`new_tabs` 设置），除非 launch 指定了目录。分屏在 `target` 的 host 上
启动，目录为 `target` 的目录，除非 launch 指定了目录。

布局变化属于会话变化：它们会复制到每个显示该会话的窗口。焦点是例外。`cx.layout:focus`
只移动此窗口的焦点，其他窗口保留各自的焦点。

### launch 表 {#launch-tables}

`launch` 表指明新面板运行什么：

| 字段 | 含义 |
| --- | --- |
| `cwd` | 启动所在的目录。 |
| `command` | 面板通过登录 shell 运行的命令行，替代交互式 shell。 |
| `block` | 要打开而不是 shell 的插件 block 类型，写作 `"<plugin>.<block>"`。 |
| `args` | block 的启动参数（字符串），传给它的 `init`。 |

没有 launch 或 launch 为空时，面板运行交互式 shell。`block` 必须是面板所在 host 上某个
Ready 插件的 block 类型。参见 [Block](blocks.md)。

## 工作区 {#workspaces}

`cx.layout:tab(spec)` 在一次调用中从一棵分屏树构建标签页：

| 字段 | 含义 |
| --- | --- |
| `cwd` | 此节点的目录，由其下所有内容继承。 |
| `name` | 标签页的名称（仅限顶层）。 |
| `split` | `[1]` 与 `[2]` 之间的拆分方向：`"right"`（默认）、`"down"`、`"left"` 或 `"up"`。 |
| `[1]`、`[2]` | 分屏的两侧，各为一个 spec。 |
| `launch` | 叶子（没有 `[1]` 与 `[2]` 的 spec）运行什么；默认为 shell。 |

标签页先以最左侧叶子的面板打开，随后每次拆分添加它的第二侧。树中更深的 `cwd` 会覆盖
其上层的值，叶子的 `launch.cwd` 则覆盖两者。`tab` 返回标签页的 id，并给它所构建的标签页
命名，即使完成时另一个标签页已成为活动页。

第二个返回值报告无法启动的面板。第一个面板无法打开时，不会打开标签页，`tab` 返回 `nil`
与该错误。后续拆分的某一侧无法启动时，例如 `launch.block` 指定的类型没有 host 上任何
Ready 插件定义，Tern 会略过该侧及其子树，构建并命名其余部分，并返回标签页 id 与类似
``could not start block `<kind>` `` 的错误。Tern 不会弹出任何提示，因此要检查它：

```lua
local tab, err = cx.layout:tab(spec)
if err then
	cx:toast("error", "Workspace opened incomplete", err)
end
```

```lua
tern.command({
	id = "api",
	title = "Open the api workspace",
	run = function(cx)
		cx.layout:tab({
			name = "api",
			cwd = "/srv/api",
			split = "right",
			{ launch = { command = "nvim" } },
			{
				split = "down",
				{ launch = { command = "cargo watch -x test" } },
				{},
			},
		})
	end,
})
```

从命令面板运行后，它会打开名为 `api` 的标签页：左侧为 `nvim`；右侧上方为
`cargo watch`，下方为交互式 shell，全部位于 `/srv/api`。

## 启动时的工作区 {#a-workspace-at-launch}

window 半区在每次窗口启动时打开项目工作区，除非会话中已有它（恢复的会话会带回自己的
标签页）：

```lua
local ROOT = (tern.getenv("HOME") or "") .. "/work/stencil"

tern.on("window_start", function(cx)
	for _, tab in cx.session:tabs() do
		if tab.name == "stencil" then
			return
		end
	end
	if not tern.fs.exists(ROOT) then
		return
	end
	cx.layout:tab({
		name = "stencil",
		cwd = ROOT,
		split = "right",
		{ launch = { command = "nvim" } },
		{ launch = { command = "cargo watch -x check" } },
	})
end)
```

`window_start` 在每个窗口中都运行，因此这项检查很重要：没有它，每个新窗口都会向会话
添加另一个工作区标签页。

### 在构建旁边保留日志面板 {#keeping-a-log-pane-beside-builds}

事件与布局调用可以组合使用。这个插件在命令失败的面板下方打开一个面板，在同一目录中运行
shell，每个面板至多一个：

```lua
local opened: { [number]: boolean } = {}

tern.on("command_finished", function(ev, cx)
	if ev.status == 0 or opened[ev.pane] then
		return
	end
	opened[ev.pane] = true
	cx.layout:split(ev.pane, "down")
	cx.layout:focus(ev.pane)
end)

tern.on("pane_closed", function(ev, _cx)
	opened[ev.pane] = nil
end)
```

`split` 会让新面板获得焦点；`focus` 调用再把焦点交还给运行该命令的面板。

## 另见 {#see-also}

- [命令、按键与覆盖](commands.md)：`cx` 动作，例如 `cx:run` 与 `cx:new_block`。
- [host 钩子与 spawn 过滤器](hooks.md)：host 半区对同一批 shell 的看法。
- [事件](../reference/events.md)：两个半区中的每个事件与载荷。
- [项目工作区](../examples/workspaces.md)：一个完整的工作区插件。
