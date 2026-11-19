# 项目工作区 {#project-workspaces}

`workspaces` 会打开项目在 `.tern/workspace.json` 中描述的标签页：具名标签页、分屏面板，
以及各自的工作目录与命令。它是仅运行于 window 半区的插件，同时也是 `cx.layout:tab`、
内置命令覆盖，以及“保持纯函数、又能反映插件所改状态”的状态栏格式化器的示例。

## 演示内容 {#what-it-demonstrates}

| Surface | 用途 |
| --- | --- |
| `tern.command`, `tern.bind` | “Open workspace”与 “Edit workspace file” |
| `cx.session:focused()`, `cx.session:panes()` | 聚焦面板的工作目录 |
| `tern.fs.exists`, `tern.fs.read`, `tern.json.decode` | 查找并读取工作区文件 |
| `cx.layout:tab(spec)` | 从分屏树构建每个标签页，并报告无法启动的面板 |
| `tern.on("window_start")`, `tern.getenv`, `cx.session:tabs()` | 启动时打开 `TERN_WORKSPACE`，接管已恢复的标签页 |
| `tern.on("tab_closed")` | 在工作区最后一个标签页关闭时将其遗忘 |
| `tern.override("new_tab", fn)` | 在工作区根目录新建标签页 |
| `cx.layout:new_tab`, `cx:open` | 覆盖中新建的标签页；打开文件 |
| `tern.chrome.status`, `tern.chrome.refresh` | 状态行中的工作区名称，在工作区打开或关闭时重绘 |
| 清单中的 `styles` | 为插件自身的分段设置样式 |

## 安装 {#install}

```sh
tern plugin install github.com/stencil-hq/tern-sdk/plugins/examples/workspaces
```

如果需要改动它，可以改为克隆 SDK 并链接该文件夹，这样每次保存时 Tern 都会重载它：

```sh
git clone https://github.com/stencil-hq/tern-sdk
tern plugin link tern-sdk/plugins/examples/workspaces
```

然后在含有 `.tern/workspace.json` 的项目中打开一个 shell（插件文件夹里有一份示例），
从命令面板运行 **Open workspace**，或使用 `cmd+alt+shift+o`（macOS 之外为
`ctrl+alt+shift+o`）。若要在 Tern 启动时打开工作区，启动 Tern 时把 `TERN_WORKSPACE`
设为项目根目录或其 `workspace.json`：

```sh
TERN_WORKSPACE=~/src/webapp tern
```

## 工作区文件 {#the-workspace-file}

```json
{
  "name": "webapp",
  "tabs": [
    {
      "name": "code",
      "split": "right",
      "panes": [
        { "command": "nvim ." },
        {
          "split": "down",
          "panes": [
            { "cwd": "web", "command": "npm run dev" },
            { "cwd": "api", "command": "cargo watch -x run" }
          ]
        }
      ]
    },
    {
      "name": "shell",
      "panes": [{}, { "block": "longrun.slow" }]
    },
    {
      "name": "infra",
      "cwd": "infra"
    }
  ]
}
```

| 字段 | 位置 | 含义 |
| --- | --- | --- |
| `name` | 顶层 | 显示在 toast 与状态行中；默认是根文件夹的名称 |
| `tabs` | 顶层 | 非空的标签页数组，按顺序打开 |
| `name` | 标签页 | 标签页名称 |
| `cwd` | 标签页、组、面板 | 工作目录，相对于外层（最外层为根）；绝对路径与 `~/` 路径同样可用 |
| `split` | 标签页、组 | `right`（默认）、`down`、`left` 或 `up`：`panes` 的划分方向 |
| `panes` | 标签页、组 | 面板与组的数组；不含 `panes` 的标签页只有一个 shell |
| `command` | 面板 | 由登录 shell 运行的命令行（`$SHELL -l -c`） |
| `block` | 面板 | 插件 block 的 kind，例如 `longrun.slow` |
| `args` | 面板 | block 的启动参数（字符串）；仅在指定 `block` 时有效 |

既没有 `command` 也没有 `block` 的面板就是一个 shell。命令面板的行为与任何程序结束的
面板相同：命令成功执行并退出后，面板会关闭。

## 设计 {#design}

### 从面板列表到分屏树 {#from-a-list-of-panes-to-a-split-tree}

`cx.layout:tab` 接受 `TabSpec`，即一棵二叉树：叶子节点有一个 `launch`，内部节点有
`split` 与两个子节点 `[1]` 和 `[2]`，`cwd` 向下继承。人们习惯把标签页想成“这三个面板
并排”，因此文件用列表描述，由 `workspace.luau` 转换。`group` 递归地把列表一分为二，
较小的那一半在前：

```text
panes: [a, b, c], split: right

        right
       /     \
      a      right
            /     \
           b       c
```

`a` 占标签页的一半，`b` 与 `c` 共享另一半，这适合“编辑器旁边放两个工具”的常见布局。
`panes` 内部的组（带自己 `panes` 的条目）按自己的方式划分其份额，正如示例中的 `code`
用 `split: "down"` 所做的那样。

转换时每个目录都会解析为绝对路径，因此该 spec 从不依赖构建时聚焦面板所在的位置。Tern
先把第一个叶子创建为新标签页，然后每遇到一个内部节点就分屏一次，并在 spec 带 `name`
时为标签页命名。

### 指向具体行的错误 {#errors-that-point-at-the-line}

编辑过程中出现格式错误的文件很常见，因此 `workspace.load` 在转换的同时做校验，抛出的
消息会指明字段：`tabs[1].panes[2].cwd: must be a string`。它以级别 `0` 抛出，从而不带上
Lua 的文件与行号前缀，window 半区用 `pcall` 捕获该错误并显示为 toast。整个文件转换完成
之前不会构建任何内容，因此第三个标签页中的错误不会留下两个半成品标签页。

### 查找根目录 {#finding-the-root}

“Open workspace” 从聚焦面板的目录开始，用 `tern.fs.exists` 逐级向上，直到找到
`.tern/workspace.json`，与 `git` 查找 `.git` 的方式相同。window 半区运行在本机上，因此
这次向上查找不需要与守护进程往返，只花费几次 `stat` 调用。

### 记住已打开的内容 {#remembering-what-is-open}

window 半区维护 `opened` 表，从根目录映射到工作区名称以及它构建的标签页 id。每个窗口都
有自己的 VM，因此各窗口各有自己的表，插件重载时该表从空开始。`tab_closed` 会移除标签页
id，并在最后一个标签页消失时移除该工作区。打开一个已经打开的工作区时只会弹出 toast，
而不会再把它的标签页打开一遍。

### 启动时打开 {#opening-at-launch}

`window_start` 在每个窗口、每个插件中运行一次，时机在窗口的会话恢复之后。它从窗口进程
的环境中读取 `TERN_WORKSPACE`，既接受根目录，也接受其 `workspace.json` 的路径，并拒绝
相对路径，因为窗口进程的工作目录无法说明用户的意图。

已恢复的会话可能已经带有上次的工作区标签页。构建之前，处理函数会查找名称与文件中某一项
相同、且目录位于根目录之内的标签页，把它们收编进 `opened`，而不是再打开一套。

### 在根目录新建标签页 {#new-tabs-at-the-root}

`tern.override("new_tab", fn)` 会在内置的新建标签页之前运行，无论它来自命令面板、菜单
还是快捷键。当聚焦面板位于某个已打开的工作区内时（工作区嵌套时以最深的根为准），覆盖
会用 `cx.layout:new_tab` 在根目录打开一个 shell 并返回 `true`，因此内置实现不会执行。
其他位置则返回 `false`，由 Tern 打开通常的标签页。参见
[命令、按键与覆盖](../guides/commands.md)。

### 纯函数式的状态分段 {#a-pure-status-segment}

状态格式化器会为位于已打开根目录内的面板返回工作区名称。它只读取内存中的 `opened` 表，
绝不访问磁盘：格式化器在 Tern 绘制期间运行，受 4 ms 预算限制，而 Tern 会按输入
（`{pane, cwd, program, title, busy}`）缓存每个结果，直到插件重载、注册新内容或调用
`tern.chrome.refresh()`。

`opened` 不属于该输入，因此若某个面板在工作区打开之前就已经存在于根目录内，它会继续
沿用缓存的答案，即没有分段。所以每次改动 `opened`（构建、启动时收编已恢复的标签页、
工作区的最后一个标签页关闭）都会调用 `tern.chrome.refresh()`，该方法丢弃缓存的答案，
并按当前的 `opened` 重绘状态行。

点击该分段会运行 “Edit workspace file”。清单中的 `workspaces.css` 让该分段加粗；Tern
把它安装为样式表 `plugin:local:workspaces:styles`，选择器
`#statusline .sl-plugin[data-plugin="workspaces"]` 只作用于本插件的分段。参见
[Chrome 与样式](../guides/chrome.md)。

## 限制 {#limits}

- **每个窗口都会运行 `window_start`。** 之后用“新建窗口”打开的窗口不带工作区标签页，
  因此在设置了 `TERN_WORKSPACE` 时它也会打开该工作区。
- **本地文件。** 向上查找与读取都在窗口所在的机器上进行。对于远程主机上的面板，该目录
  指的是远程路径，只有当本地也存在相同路径时才能找到工作区。
- **目录不存在。** 若 `cwd` 不存在，面板会从主目录启动。
- **block 缺失。** 若某个分屏的新一侧会以没有任何已加载插件定义的 block kind 启动，
  `cx.layout:tab` 会连同其下所有内容一起略过该分屏，并构建其余部分；若标签页的第一个
  面板就是这种 block，则该标签页不会打开。无论哪种情况，它都会把错误作为第二个返回值
  给出，`build` 会把它们汇集成一条 “Opened *name* incomplete” toast。
- **纯 JSON。** 不支持注释和尾逗号。

## 代码 {#code}

`plugin.toml`：

```toml
schema = 1
id = "workspaces"
name = "Project Workspaces"
version = "0.1.0"
description = "Opens the tabs a project's .tern/workspace.json describes."
icon = "folder"
window = "window.luau"
styles = ["workspaces.css"]
```

`workspace.luau`：

```lua
--!strict
-- Finds and reads `.tern/workspace.json`, turning it into the tab specs
-- `cx.layout:tab` builds.
--
-- {
--   "name": "webapp",                      -- default: the root's folder name
--   "tabs": [{
--     "name": "dev",                       -- tab name
--     "cwd": "web",                        -- relative to the root (default: the root)
--     "split": "right",                    -- how `panes` divide (default "right")
--     "panes": [                           -- default: one shell
--       {"command": "npm run dev"},        -- a login shell runs it with -c
--       {"block": "longrun.slow", "args": []},
--       {"cwd": "api"},                    -- a shell, relative to the tab's cwd
--       {"split": "down", "panes": [...]}  -- a group, divided its own way
--     ]
--   }]
-- }

local workspace = {}

local FILE = ".tern/workspace.json"
local HOME = tern.getenv("HOME")
local SIDES: { [string]: boolean } = { right = true, down = true, left = true, up = true }

export type Workspace = {
	name: string,
	root: string,
	tabs: { TabSpec },
	-- The tab names, to recognize a restored session's tabs.
	names: { string },
}

-- `path` without trailing slashes.
local function trim(path: string): string
	local out = string.gsub(path, "(.)/+$", "%1")
	return out
end

-- `path` made absolute against `base`; `~` is the home directory.
function workspace.resolve(base: string, path: string): string
	if path == "~" or string.sub(path, 1, 2) == "~/" then
		if HOME == nil then
			error("HOME is not set, so " .. path .. " can't be resolved", 0)
		end
		return trim(HOME .. string.sub(path, 2))
	end
	if string.sub(path, 1, 1) == "/" then
		return trim(path)
	end
	path = string.gsub(path, "^%./", "")
	if path == "" or path == "." then
		return base
	end
	return trim(if base == "/" then "/" .. path else base .. "/" .. path)
end

-- The nearest directory at or above `dir` holding `.tern/workspace.json`.
function workspace.find(dir: string): string?
	local at: string? = trim(dir)
	while at do
		local candidate = if at == "/" then "/" .. FILE else at .. "/" .. FILE
		if tern.fs.exists(candidate) then
			return at
		end
		if at == "/" then
			return nil
		end
		local up = string.match(at, "^(.*)/[^/]*$")
		at = if up == nil or up == "" then "/" else up
	end
	return nil
end

-- Raises `where: message` (no Lua position: the toast shows it as is).
local function fail(where: string, message: string): never
	error(string.format("%s: %s", where, message), 0)
end

local function optional_string(value: any, where: string): string?
	if value ~= nil and type(value) ~= "string" then
		fail(where, "must be a string")
	end
	return value
end

local function side(value: any, where: string): Dir
	local name = optional_string(value, where) or "right"
	if not SIDES[name] then
		fail(where, "must be right, down, left or up")
	end
	return name :: Dir
end

local node: (entry: any, cwd: string, where: string) -> TabSpec

-- `list` divided `split`-wise: the first half on one side, the rest on the
-- other, recursively. With an odd count the first side holds fewer panes,
-- so the first pane (often an editor) gets the most room.
local function group(list: { any }, split: Dir, cwd: string, where: string): TabSpec
	if #list == 0 then
		return {}
	end
	local function range(from: number, to: number): TabSpec
		if from == to then
			return node(list[from], cwd, string.format("%s[%d]", where, from))
		end
		local middle = from + (to - from + 1) // 2 - 1
		return { split = split, range(from, middle), range(middle + 1, to) }
	end
	return range(1, #list)
end

-- One `panes` entry: a group (it has `panes`) or a leaf.
node = function(entry: any, cwd: string, where: string): TabSpec
	if type(entry) ~= "table" then
		fail(where, "must be an object")
	end
	local own = optional_string(entry.cwd, where .. ".cwd")
	local here = if own then workspace.resolve(cwd, own) else cwd
	if entry.panes ~= nil then
		if type(entry.panes) ~= "table" then
			fail(where .. ".panes", "must be an array")
		end
		local spec = group(entry.panes, side(entry.split, where .. ".split"), here, where .. ".panes")
		spec.cwd = spec.cwd or here
		return spec
	end
	local command = optional_string(entry.command, where .. ".command")
	local block = optional_string(entry.block, where .. ".block")
	if command and block then
		fail(where, "has both command and block")
	end
	local args: { string }? = nil
	if entry.args ~= nil then
		if block == nil then
			fail(where .. ".args", "only blocks take args")
		end
		if type(entry.args) ~= "table" then
			fail(where .. ".args", "must be an array of strings")
		end
		args = {}
		for i, arg in entry.args do
			table.insert(args :: { string }, optional_string(arg, string.format("%s.args[%d]", where, i)) :: string)
		end
	end
	return { cwd = here, launch = { command = command, block = block, args = args } }
end

-- The workspace at `root`; raises a readable message when the file is
-- missing or malformed.
function workspace.load(root: string): Workspace
	local path = root .. "/" .. FILE
	local ok, text = pcall(tern.fs.read, path)
	if not ok then
		fail(path, "can't be read")
	end
	local decoded, data = pcall(tern.json.decode, text)
	if not decoded then
		fail(path, "isn't valid JSON (" .. tostring(data) .. ")")
	end
	if type(data) ~= "table" then
		fail(path, "must hold an object")
	end
	local folder = string.match(root, "([^/]+)$") or root
	local name = optional_string(data.name, "name") or folder
	if type(data.tabs) ~= "table" or #data.tabs == 0 then
		fail("tabs", "must be a non-empty array")
	end
	local tabs: { TabSpec } = {}
	local names: { string } = {}
	for i, tab in data.tabs do
		local where = string.format("tabs[%d]", i)
		if type(tab) ~= "table" then
			fail(where, "must be an object")
		end
		local cwd = workspace.resolve(root, optional_string(tab.cwd, where .. ".cwd") or ".")
		local panes = tab.panes or {}
		if type(panes) ~= "table" then
			fail(where .. ".panes", "must be an array")
		end
		local spec = group(panes, side(tab.split, where .. ".split"), cwd, where .. ".panes")
		spec.cwd = spec.cwd or cwd
		spec.name = optional_string(tab.name, where .. ".name")
		if spec.name then
			table.insert(names, spec.name :: string)
		end
		table.insert(tabs, spec)
	end
	return { name = name, root = root, tabs = tabs, names = names }
end

return workspace
```

`window.luau`：

```lua
--!strict
-- workspaces, window half: opens the tabs a project's
-- `.tern/workspace.json` describes, from the palette or at launch
-- (`TERN_WORKSPACE`), starts new tabs at the root of the workspace the
-- focused pane is in, and names that workspace in the status line.

local workspace = require("./workspace")

local OPEN = "plugin.workspaces.open"
local EDIT = "plugin.workspaces.edit"
local HOME = tern.getenv("HOME")

-- A workspace this window opened (or found restored), and its tab ids.
type Opened = {
	name: string,
	root: string,
	tabs: { [number]: boolean },
}

-- Opened workspaces by root. Only this window's VM sees it, and a plugin
-- reload starts it empty.
local opened: { [string]: Opened } = {}

local function tilde(path: string): string
	if HOME and string.sub(path, 1, #HOME + 1) == HOME .. "/" then
		return "~" .. string.sub(path, #HOME + 1)
	end
	return path
end

local function inside(path: string, root: string): boolean
	return path == root or string.sub(path, 1, #root + 1) == root .. "/" or root == "/"
end

-- The opened workspace holding `path`; the deepest root wins when
-- workspaces nest.
local function owner(path: string?): Opened?
	if path == nil then
		return nil
	end
	local best: Opened? = nil
	for root, entry in opened do
		if inside(path, root) and (best == nil or #root > #best.root) then
			best = entry
		end
	end
	return best
end

local function focused_cwd(cx: WindowCx): string?
	local id = cx.session:focused()
	for _, pane in cx.session:panes() do
		if pane.pane == id then
			return pane.cwd
		end
	end
	return nil
end

-- Builds `w`'s tabs and remembers them.
local function build(cx: WindowCx, w: workspace.Workspace)
	local entry: Opened = { name = w.name, root = w.root, tabs = {} }
	local count = 0
	-- What couldn't start: a tab whose first pane failed is missing, a
	-- split whose new side failed is left out of its tab.
	local problems: { string } = {}
	for _, spec in w.tabs do
		local tab, err = cx.layout:tab(spec)
		if tab then
			entry.tabs[tab] = true
			count += 1
		end
		if err then
			table.insert(problems, err)
		end
	end
	if count == 0 then
		local why = if #problems > 0 then table.concat(problems, "; ") else tilde(w.root)
		cx:toast("error", "Workspace " .. w.name .. " opened no tabs", why)
		return
	end
	opened[w.root] = entry
	-- Panes already inside the root get the segment too.
	tern.chrome.refresh()
	if #problems > 0 then
		cx:toast("error", "Opened " .. w.name .. " incomplete", table.concat(problems, "; "))
	else
		cx:toast("success", "Opened " .. w.name, string.format("%d tabs · %s", count, tilde(w.root)))
	end
end

-- Reads the workspace at `root`, toasting the problem when it doesn't load.
local function read(cx: WindowCx, root: string): workspace.Workspace?
	local ok, result = pcall(workspace.load, root)
	if not ok then
		cx:toast("error", "Workspace not opened", tostring(result))
		return nil
	end
	return result
end

local function open_at(cx: WindowCx, root: string)
	local current = opened[root]
	if current then
		cx:toast("info", current.name .. " is already open", tilde(root))
		return
	end
	local w = read(cx, root)
	if w then
		build(cx, w)
	end
end

tern.command({
	id = "open",
	title = "Open workspace",
	icon = "folder",
	run = function(cx: WindowCx)
		local cwd = focused_cwd(cx)
		local root = if cwd then workspace.find(cwd) else nil
		if root == nil then
			cx:toast("error", "No workspace here", "No .tern/workspace.json above " .. tilde(cwd or "this pane"))
			return
		end
		open_at(cx, root)
	end,
})

tern.command({
	id = "edit",
	title = "Edit workspace file",
	icon = "folder",
	run = function(cx: WindowCx)
		local cwd = focused_cwd(cx)
		local root = if cwd then workspace.find(cwd) else nil
		if root == nil then
			cx:toast("error", "No workspace here", "No .tern/workspace.json above " .. tilde(cwd or "this pane"))
			return
		end
		cx:open(root .. "/.tern/workspace.json", "beside")
	end,
})

tern.bind(if tern.runtime.os == "macos" then "cmd+alt+shift+o" else "ctrl+alt+shift+o", OPEN)

-- At launch: the workspace TERN_WORKSPACE names (its root, or its
-- workspace.json). A restored session already has its tabs, so tabs named
-- like the workspace's and inside its root are adopted instead of opened
-- twice.
tern.on("window_start", function(cx: WindowCx)
	local target = tern.getenv("TERN_WORKSPACE")
	if target == nil or target == "" then
		return
	end
	local first = string.sub(target, 1, 1)
	if first ~= "/" and first ~= "~" then
		cx:toast("error", "TERN_WORKSPACE must be an absolute path", target)
		return
	end
	local root = workspace.resolve("/", target)
	root = string.gsub(root, "/%.tern/workspace%.json$", "")
	local w = read(cx, root)
	if w == nil then
		return
	end
	local names: { [string]: boolean } = {}
	for _, name in w.names do
		names[name] = true
	end
	local restored: Opened = { name = w.name, root = root, tabs = {} }
	for _, tab in cx.session:tabs() do
		if tab.name and names[tab.name] and tab.cwd and inside(tab.cwd, root) then
			restored.tabs[tab.id] = true
		end
	end
	if next(restored.tabs) then
		opened[root] = restored
		tern.chrome.refresh()
	else
		build(cx, w)
	end
end)

tern.on("tab_closed", function(ev: TabEvent, _cx: WindowCx)
	for root, entry in opened do
		if entry.tabs[ev.tab] then
			entry.tabs[ev.tab] = nil
			if next(entry.tabs) == nil then
				opened[root] = nil -- the last of its tabs closed
				tern.chrome.refresh()
			end
		end
	end
end)

-- A new tab from a pane inside an opened workspace starts at its root;
-- anywhere else the built-in runs (returning false).
tern.override("new_tab", function(cx: WindowCx): boolean
	local entry = owner(focused_cwd(cx))
	if entry == nil then
		return false
	end
	return cx.layout:new_tab({ cwd = entry.root }) ~= nil
end)

-- Pure: reads only `opened`, never the disk. Tern caches the answer per
-- pane input, so every change to `opened` calls `tern.chrome.refresh()`.
tern.chrome.status(function(pane: PaneInfo): { StatusSegment }?
	local entry = owner(pane.cwd)
	if entry == nil then
		return nil
	end
	return { { text = entry.name, icon = "folder", command = EDIT } }
end)
```

`workspaces.css`：

```css
/* The workspace's status segment reads as a label, not a hint. */
#statusline .sl-plugin[data-plugin="workspaces"] {
	font-weight: 600;
}
```
