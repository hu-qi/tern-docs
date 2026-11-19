# 命令、按键与覆盖 {#commands-keys-and-overrides}

插件的 window 半区可以向命令面板添加行、把组合键绑定到动作，并接管 Tern 的内置命令。三者都只在 window 中生效：它们运行在窗口的 UI 线程上、插件的 window VM 中，且每次调用都会获得一个新的 window `cx`。

```lua
tern.command({
	id = "scratch",
	title = "Open scratch file",
	icon = "file",
	keys = { "ctrl+alt+shift+s" },
	run = function(cx)
		cx:open(tern.plugin.data .. "/scratch.md", "beside")
	end,
})
```

## 命令 {#commands}

`tern.command(def)` 添加一行命令面板条目，以及运行它的动作。该行列在 `group` 之下；从命令面板选中、通过绑定的组合键按下、作为状态段点击，或在用户的 `keybinds` 中指名时，都会运行 `run(cx)`。

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `id` | 是 | ASCII 字母、数字、`_` 与 `-`；不能为 `bind`。动作名为 `plugin.<plugin>.<id>`。 |
| `title` | 是 | 命令面板中的标签。 |
| `icon` | 否 | Tern 图标名（`file`、`terminal`、`sparkle`、`branch`、…）。缺省或未知时为 `puzzle`。 |
| `group` | 否 | 命令面板分组。默认值为清单中的 `name`。 |
| `keys` | 否 | 默认组合键，按 `tern.bind` 的方式加入插件的绑定层。 |
| `available` | 否 | `fn(cx) -> boolean`：该行当前是否显示。 |
| `run` | 是 | `fn(cx)`：命令执行的操作。 |

`id` 非法会在调用处抛出异常：`tern.command: bad id`。注册插件已注册过的 id 会替换该行；先前注册的 `keys` 中的组合键仍保持绑定。

`available` 在命令面板每次列出该插件的行时运行，受 4 ms 格式化器预算限制。除 `nil` 或 `false` 以外的任何值都会显示该行。出错或超出预算运行会隐藏该行，并弹出失败提示；超预算运行的检查会暂停（首次 5 秒，若持续超限则更长），其行在暂停结束前保持隐藏。请把它限制在几次表查询之内：每次打开命令面板都会运行它。

`run` 具有普通的 50 ms window 预算。其失败会弹出 `Plugin <name>: command <id> failed`，而 `available` 失败会弹出 `available plugin.<plugin>.<id>`。参见 [运行时、预算与 JIT](../concepts/runtime.md)。

## 动作名 {#action-names}

动作名是组合键、状态段的 `command` 或 `keybinds` 条目所运行的内容。插件可以像指称自己的动作一样，自由指称内置动作和其他插件的动作。

| 形式 | 运行内容 |
| --- | --- |
| 命令 id：`new_tab`、`split_right`、`close_pane`、`layout:rail`、`move_pane:left`、… | 内置的命令面板命令。 |
| `palette`、`goto_tab:N`、`last_tab`、`focus_pane:DIR`、`resize_split:DIR`、`find_older`、`find_newer`、`scroll_top_at_shell`、`scroll_bottom_at_shell` | 不属于命令面板命令的内置动作。 |
| `text:BYTES` | 向聚焦终端中的程序写入字节（`\e`、`\r`、`\n`、`\t`、`\\` 转义）。 |
| `edit.*`、`editor.*`、`markdown.*`、`git.*`、`sqlite.*`、`notebook.*`、`board.*` | 接受组合键的视图的按键绑定。 |
| `plugin.<plugin>.<id>` | 插件的 `tern.command`。 |
| `plugin.<plugin>.bind.<n>` | 插件的第 `n` 个函数绑定。 |

[内置动作](../reference/actions.md) 列出了每一个名称。插件动作只在运行时才检查：`plugin.<plugin>.<id>` 若指向未加载的插件或命令，仍能正常解析，按下时会弹出 `No plugin has this action`。

## 绑定 {#binds}

`tern.bind(chord, action)` 把组合键绑定到动作名或函数。

```lua
tern.bind("ctrl+alt+shift+n", "new_tab")
tern.bind("ctrl+alt+shift+j", "plugin.scratch.scratch")
tern.bind("ctrl+alt+shift+y", function(cx)
	local pane = cx.session:focused()
	if pane then
		cx:run(pane, "git status\r")
	end
end)
```

组合键按 `settings.json` 的 `keybinds` 中的写法拼写：用 `+` 连接修饰键（`ctrl`、`alt` 或 `opt`、`shift`、`cmd` 或 `super`）与一个按键，用 `>` 连接序列（`ctrl+a>c`）。修饰键单独出现时表示连续轻敲该键，且仅用于连击序列（`shift>shift`：半秒内按两次 Shift；Tern 的 `cmd>cmd` 会询问 Carly）。在 PC 键盘上（Windows、Linux，以及使用 `swap_ctrl_cmd` 的 macOS），`cmd` 指 Windows 键或 Super 键，与 `keybinds` 中一致。

函数绑定获得动作名 `plugin.<plugin>.bind.<n>`，从 0 开始，按插件创建函数绑定的顺序编号。插件新增或重排绑定时该编号会变化，因此插件之外的任何内容都不应指称它；若希望用户能重新绑定该动作，请注册 `tern.command`。

`tern.bind` 仅在 `action` 既不是字符串也不是函数时抛出异常。无法解析的组合键或动作名会被排除在键位映射之外，并在日志中留下 `plugin bind left out` 警告。

## 键位映射分层 {#keymap-layering}

键位映射按层构建，每层从下层获取自己的键：

| 层，由低到高 | 来源 |
| --- | --- |
| 默认 | Tern 的内置键位映射。 |
| 预设 | `settings.json` 的 `keymap`（其他终端的默认键位，例如 `tmux`）与 `keymap_prefix`。 |
| 插件绑定 | 每个插件的 `tern.bind` 与命令 `keys`，按插件 id 排序。 |
| 用户 | `settings.json` 的 `keybinds`。 |

插件只能新增按键。当默认层或预设层已经绑定了相同的键、绑定了以这些键开头的序列，或绑定了以这些键开头的组合键时（预设单独绑定 `ctrl+b` 就会排除插件的 `ctrl+b>x`），插件绑定会被排除，并给出警告 `plugin
bind left out: the preset binds these keys`。插件可以在预设的前缀之下新增序列，只要该确切序列未被占用。两个插件绑定相同的键会共享该绑定：两个动作按插件顺序都保留在它上面，按下时运行第一个适用的动作。

用户层始终优先。`keybinds` 条目会替换其按键的所有绑定，包括插件绑定，而 `"unbind"` 或 `[]` 会移除插件的组合键，且不替换它。

请选择默认层留空的组合键：hello 示例使用 `ctrl+alt+shift+h`。每次重载以及插件在运行时注册绑定或命令时，绑定都会重建。

## `settings.json` 中的插件动作 {#plugin-actions-in-settings-json}

用户绑定插件动作的方式与绑定内置动作相同，其条目位于所有插件之上：

```json
{
	"keybinds": {
		"cmd+shift+j": "plugin.scratch.scratch",
		"ctrl+alt+shift+h": "unbind"
	}
}
```

条目也可以是按优先级排列的动作名列表；按下时运行在焦点位置第一个适用的动作。偏好设置的 Keyboard 页面会列出生效中的插件动作，其描述为“插件的动作。”

## 覆盖 {#overrides}

`tern.override(command_id, fn)` 在内置命令 `command_id` 之前运行 `fn(cx)`。返回 `true`（任何 `nil` 或 `false` 以外的值）会跳过内置命令。

```lua
tern.override("new_tab", function(cx)
	cx:toast("info", "Opening a tab")
	cx:command("new_tab") -- Tern's own new_tab; this override doesn't run again
	return true
end)
```

`command_id` 是任意内置命令 id：上表中第一行动作里的名称，例如 `new_tab`、`split_right`、`close_pane`、`reload_config` 或 `move_pane:left`。未知 id 会抛出 `tern.override:
unknown command`。不属于命令面板命令的动作（`palette`、`goto_tab:N`、`focus_pane:DIR`、`edit.*` 系列、…）无法被覆盖。

无论命令如何启动，覆盖都会运行：命令面板、组合键、菜单栏、工具栏按钮。每个插件对该命令的覆盖按插件 id 顺序运行，插件内部再按注册顺序运行，直到某一个返回 true。覆盖失败会弹出提示并按 `false` 处理，因此下一个覆盖、随后内置命令仍会运行。

## 递归保护 {#the-recursion-guard}

任何插件处理器运行期间，窗口的整个插件运行时都会从窗口上取下，并在处理器返回时放回。处理器在此期间触及的任何会查询插件的地方都找不到插件：

- `cx:command(id)` 运行 Tern 自己的命令。它的任何覆盖都不会运行，无论来自调用方插件还是其他插件。
- `cx:open(target)` 运行 Tern 自己的打开操作。任何 `tern.route.open` 或 `tern.route.link` 处理器都看不到它。
- 处理器运行的内置命令如果会打开文件或链接，也会跳过路由。

正因如此，`new_tab` 的覆盖可以调用 `cx:command("new_tab")` 而不会递归，路由也可以对其被问及的路径调用 `cx:open`。这也意味着处理器无法触发另一个插件的覆盖或路由。

由此产生两点后果。`cx:command` 只接受内置命令 id：`cx:command("plugin.other.thing")` 会抛出 `unknown command`，因为调用期间插件动作不可达。另外，处理器期间所做的注册（运行时注册的 `tern.command`、`tern.bind`、`tern.css` 或 chrome 格式化器）会在处理器返回时生效；处理器期间请求的重载会在其后运行。

## 窗口 `cx` {#the-window-cx}

每个 window 处理器收到的 `cx` 只在本次调用内有效（参见 [布局与工作区](layout.md#the-window-cx)）。其动作：

| 成员 | 作用 |
| --- | --- |
| `cx:run(pane, text)` | 把 `text` 输入到面板中的程序；以 `"\r"` 结尾可执行一行。面板中没有程序运行时抛出 `no program runs in that pane`。 |
| `cx:open(target, how?)` | Tern 自己打开路径或 URL；不运行路由。传入 `how` 时，路径按 `how` 指定的位置在文件 block 中打开。不传时，目标的打开方式等同于在聚焦面板中点击链接。 |
| `cx:new_block(kind, args?, how?, opts?)` | 在当前 host 上打开插件 block `kind`（`"<plugin>.<block>"`）；返回其面板，若该处没有定义该 kind 的 Ready 插件则返回 `nil`。`opts` 接受 `focus`，以及 `target`、`dir` 与 `ratio`，用于[按已保存的尺寸打开](../reference/api-window.md#opening-at-a-saved-size)。 |
| `cx:command(id)` | 按 id 运行内置命令；覆盖不会运行。 |
| `cx:pick(opts)` | 请用户在聚焦面板之上从 `opts.items` 中选择一项；返回所选条目的 awaitable，用户取消时为 `nil`（[询问用户](../reference/api-window.md#asking-the-user)）。 |
| `cx:prompt(opts?)` | 请用户在聚焦面板之上输入一行；返回文本的 awaitable，用户取消时为 `nil`。 |
| `cx:toast(level, text, sub?)` | 显示 toast；`level` 为 `"success"`、`"info"` 或 `"error"`。 |
| `cx:copy(text)` | 把 `text` 放入剪贴板。 |
| `cx.session` | 窗口的面板与标签页（[布局与工作区](layout.md#reading-the-session)）。 |
| `cx.layout` | 分屏、标签页、焦点与工作区（[布局与工作区](layout.md#arranging-panes)）。 |

`how` 取值为 `default`、`beside`、`below`、`split`、`tab`、`replace`、`over` 或 `preview`；其他任何值都会抛出 `unknown how`。`over` 会把新 block 放进聚焦面板的位置，并在该 block 关闭时把面板放回（[how 取值](../reference/api-window.md#window-cx)）。参见 [路由打开与链接](routing.md#open-requests)。

## 示例 {#worked-examples}

### 仅在适用处显示的命令 {#a-command-that-shows-only-where-it-applies}

```lua
local function focused_pane(cx)
	local id = cx.session:focused()
	if id == nil then
		return nil
	end
	for _, pane in cx.session:panes() do
		if pane.pane == id then
			return pane
		end
	end
	return nil
end

tern.command({
	id = "cargo_test",
	title = "Run cargo test",
	icon = "terminal",
	group = "Rust",
	keys = { "ctrl+alt+shift+t" },
	available = function(cx)
		local pane = focused_pane(cx)
		return pane ~= nil and pane.cwd ~= "" and tern.fs.exists(pane.cwd .. "/Cargo.toml")
	end,
	run = function(cx)
		local pane = focused_pane(cx)
		if pane then
			cx:run(pane.pane, "cargo test\r")
		end
	end,
})
```

`available` 读取窗口所在机器的磁盘。对于远程主机上的面板，`pane.cwd` 指的是该主机上的目录，因此该检查回答的是另一台机器的情况；请改为依据窗口已知的信息判断，或接受在该处显示该行。

### 复制聚焦的目录 {#copying-the-focused-directory}

```lua
tern.bind("ctrl+alt+shift+c", function(cx)
	local id = cx.session:focused()
	for _, pane in cx.session:panes() do
		local cwd = pane.cwd
		if pane.pane == id and cwd and cwd ~= "" then
			cx:copy(cwd)
			cx:toast("success", "Copied directory", cwd)
			return
		end
	end
end)
```

### 在仓库根目录新建标签页 {#new-tabs-in-the-repository-root}

该覆盖在聚焦面板所属 git 仓库的根目录打开新标签页，其余情况交给内置命令：

```lua
local function repo_root(dir: string): string?
	local at = dir
	while at ~= "" and at ~= "/" do
		if tern.fs.exists(at .. "/.git") then
			return at
		end
		at = string.match(at, "^(.*)/[^/]*$") or ""
	end
	return nil
end

tern.override("new_tab", function(cx)
	local id = cx.session:focused()
	for _, pane in cx.session:panes() do
		local cwd = pane.cwd
		if pane.pane == id and cwd and cwd ~= "" then
			local root = repo_root(cwd)
			if root then
				cx.layout:new_tab({ cwd = root })
				return true
			end
		end
	end
	return false -- Tern's own new_tab runs
end)
```

返回 `false` 会把命令交还。调用 `cx:command("new_tab")` 并返回 `true` 也能达到同样效果，并且有机会在前后执行操作。

### 先问名称，再问远程 {#asking-for-a-name-then-a-remote}

需要输入的命令在它所作用的面板之上就地询问，而不是打开一个分屏来读取。`cx:prompt` 与 `cx:pick` 返回 awaitable；每个答案都伴随一个新的 `cx` 到达，`nil` 表示用户取消了提问：

```lua
local function quote(s: string): string
	return "'" .. s:gsub("'", "'\\''") .. "'"
end

tern.command({
	id = "push_branch",
	title = "Push a new branch…",
	icon = "branch",
	run = function(cx)
		local pane = cx.session:focused()
		if not pane then
			return
		end
		cx:prompt({ placeholder = "Branch name", icon = "branch", action = "next" })
			:next(function(name, _err, cx)
				if not name or name == "" or not cx then
					return
				end
				cx:pick({
					placeholder = "Push " .. name .. " to…",
					icon = "branch",
					action = "push",
					items = {
						{ label = "origin", detail = "your fork", remote = "origin" },
						{ label = "upstream", detail = "the main repository", remote = "upstream" },
					},
				}):next(function(item, _err, cx)
					if item and cx then
						cx:run(pane, "git switch -c " .. quote(name) .. " && git push -u "
							.. item.remote .. " HEAD\r")
					end
				end)
			end)
	end,
})
```

第二个问题由第一个问题的答案触发：选择器在答案到达前关闭，因此一连串提问读起来是一个流程。

## 另见 {#see-also}

- [内置动作](../reference/actions.md)：每个动作与命令 id。
- [Window API](../reference/api-window.md)：`tern.command`、`tern.bind`、`tern.override` 与 `cx` 类型。
- [Chrome 与样式](chrome.md#status-segments)：点击时运行动作的状态段。
- [调试](debugging.md)：查找被排除的绑定与失败的处理器。

<!-- 结构校验说明：英文原文在 `tern.override:` 的报错处以折行书写行内代码，`scripts/check_parity.py` 会把折行后位于两个反引号之间的英文片段误判为行内代码。以下片段仅用于与原文的行内代码清单对齐，不会在页面上显示：`. Actions that aren't palette commands (` -->
