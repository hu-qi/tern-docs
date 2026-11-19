# Chrome 与样式 {#chrome-and-styling}

插件的 window 半区可以为标签页和窗口重新命名、向状态行添加片段、选择程序显示的图标，
以及添加全局 CSS。标题与片段来自 chrome 格式化器：它们是以一张小输入表为参数的纯函数，
Tern 在绘制过程中调用，因此其运行时间受严格预算约束，结果也会被缓存。
样式来自清单中的 `styles` 文件与 `tern.css`。

```lua
tern.chrome.tab_title(function(tab)
	if tab.name then
		return nil -- keep names the user gave
	end
	return string.match(tab.cwd or "", "([^/]+)/*$")
end)
```

## 格式化器 {#formatters}

| 格式化器 | 调用对象 | 结果 | 多个插件时 |
| --- | --- | --- | --- |
| `tern.chrome.tab_title(fn)` | 当前会话的每个标签页。 | 一个标题字符串，或 `nil` 表示使用 Tern 自己的标题。 | 按 id 顺序，第一个给出标题的插件胜出。 |
| `tern.chrome.window_title(fn)` | 该窗口。 | 一个标题字符串，或 `nil` 表示使用 Tern 自己的标题。 | 第一个给出标题的插件胜出。 |
| `tern.chrome.status(fn)` | 获得焦点的面板。 | 一个片段列表，或 `nil` 表示没有片段。 | 每个插件的片段都会显示，按插件 id 顺序排列。 |

每个插件在每个槽位只有一个格式化器；再次注册会替换掉原有的格式化器。空字符串视同 `nil`。
格式化器给出的标题会覆盖 Tern 自己的标题，即使用户重命名过该标签页也是如此，
因此在用户指定的名称应当优先时，要先检查 `tab.name`。

格式化器是纯函数：

- **没有 `cx`。** 格式化器只接收它的输入表。它可以读取 `tern.kv`、`tern.fs` 与 upvalue，
  但不能对窗口执行操作。
- **4 ms 预算。** 运行时间超出的格式化器会抛出 `tern: tab_title exceeded 4 ms`
  （或 `window_title`、`status`），弹出提示并暂停：首次为 5 s，若持续触发则更久。
- **按输入缓存。** 每张不同的输入表只格式化一次；在输入改变之前，Tern 复用其结果。
  缓存为每个格式化器保留最多 256 张输入表，并在插件重载或注册任何内容
  （命令、快捷键或格式化器）时，以及调用 `tern.chrome.refresh()` 时被丢弃。

失败情形（报错、返回类型错误、超出预算）会在命中它们的那一帧之后以
`Plugin <name>: <slot> failed` 的形式提示；该帧使用 Tern 自己的标题，或没有片段。

## 刷新 {#refreshing}

当会话发生变化（焦点、标题、目录、命令开始或结束）以及面板输出时，Tern 会重绘 chrome。
如果某个格式化器的答案依赖其输入之外的东西（时钟、文件、进程结果），那么在上述任一事件发生
之前，它只会显示第一次的答案。应把这类数据放在 upvalue 中，并在其改变后调用
`tern.chrome.refresh()`：

- 它会丢弃本窗口中所有格式化器的缓存结果（标签页标题、窗口标题、状态片段）。
- 它会唤醒窗口，并在下一帧重绘其标签页、状态行与标题，因此每个格式化器都会以当前输入
  重新运行。

只有该窗口会刷新；每个窗口都有自己的 window 半区。在格式化器内部调用 `refresh` 会抛出
`tern.chrome.refresh: not from a formatter`（否则它会在每一帧重新运行该格式化器）：
应改从定时器、进程或 fetch 回调、事件处理器或命令中调用。

会跳动的片段从 `tern.timer` 中调用它：在有待计数内容时每秒一次，没有时停止该定时器，
因此空闲窗口不运行任何 Lua。
[长时间运行的命令](../examples/longrun.md) 就是以这种方式显示焦点面板的运行时长。
[下面的示例](#a-segment-fed-by-a-process) 在每次轮询后刷新。

## 输入 {#inputs}

`tab_title(tab)` 接收：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `number` | 标签页 id。 |
| `name` | `string?` | 用户为该标签页指定的名称。 |
| `cwd` | `string` | 焦点面板的目录；未知时为 `""`。 |
| `program` | `string` | 焦点面板的程序。 |
| `title` | `string` | 焦点面板的标题。 |
| `panes` | `number` | 该标签页有多少个面板。 |
| `busy` | `boolean` | 其中是否有命令正在运行。 |

`window_title(win)` 接收：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `space` | `string` | 当前会话的名称（即 Tern 自己的窗口标题）。 |
| `tab` | `string?` | 活动标签页的标题。 |
| `pane` | `number?` | 焦点面板的 id。 |
| `cwd` | `string?` | 焦点面板的目录。 |
| `tabs` | `number` | 当前会话有多少个标签页。 |

`status(pane)` 接收焦点面板：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `pane` | `number` | 面板 id。 |
| `cwd` | `string` | 其目录；未知时为 `""`。 |
| `program` | `string` | 其程序。 |
| `title` | `string` | 其标题。 |

`cx.session:tabs()` 与 `cx.session:panes()` 返回的表，与 `tab_title` 和 `status` 所接收的
表结构相同。远程主机上的面板报告的是该主机上的目录；`tern.fs` 读取的是窗口所在的机器。

## 状态片段 {#status-segments}

状态格式化器返回一个由片段表组成的列表：

| 字段 | 必需 | 含义 |
| --- | --- | --- |
| `text` | 是 | 片段的文本。 |
| `icon` | 否 | 显示在文本之前的 Tern 图标名；未知名称不显示图标。 |
| `tone` | 否 | 颜色：`accent`、`muted`、`ok`、`warn`、`error`（或 `bad`）有 Tern 样式；其他值只是供自定义 CSS 使用的属性。 |
| `command` | 否 | 点击时运行的动作名（`"new_tab"`、`"plugin.<plugin>.<id>"`）。 |

缺少 `text` 的片段，或不是表的列表项，会使格式化器失败。`command` 在片段被点击时解析；
无法解析时会提示 `A status segment's command is unknown`。

片段渲染在状态行的末尾，位于面板尺寸之后：

```html
<footer id="statusline">
	…
	<span class="sl-plugins">
		<span class="sl-plugin" data-plugin="ID" data-tone="TONE">ICON TEXT</span>
		<span class="sl-plugin on" data-plugin="ID" role="button" title="COMMAND">…</span>
	</span>
</footer>
```

仅当片段设置了 `tone` 时才会出现 `data-tone`。带有 `command` 的片段会获得 `on` 类、
`role="button"`，并以动作名作为提示文字。状态行仅在状态栏开启时显示
（`status_bar` 命令）。

## Files 面板按钮 {#files-pane-buttons}

`tern.files.button` 在 Files 面板的头部、其自带工具的旁边添加一个按钮，并在被点击时以
面板所显示的文件夹及其选中项运行处理器。与格式化器不同，它不是纯函数：处理器会像命令那样
获得 `cx`。参见
[Window API](../reference/api-window.md#ternfilesbutton)。

```lua
tern.files.button({
	id = "copy-paths",
	title = "Copy selected paths",
	icon = "copy",
	run = function(files, cx)
		if #files.selection > 0 then
			cx:copy(table.concat(files.selection, "\n"))
		end
	end,
})
```

```html
<header class="ft-head">
	…
	<div class="ft-tools">
		…
		<span class="ft-plugins on">
			<button class="icon-btn ft-hb ft-rv ft-plugin" data-plugin="ID" data-id="BUTTON" title="TITLE">ICON</button>
		</span>
		<button class="icon-btn ft-hb ft-rv" title="More">…</button>
		…
	</div>
</header>
```

## 程序图标 {#program-icons}

每个标签页都会为其中的每个面板显示其运行程序的图标：带图标的标签页上显示应用磁贴，
纯文本标签页、命令面板的面板行与停放卡片上显示扁平符号。`tern.chrome.program_icon(program, icon)`
为某个程序选择另一个图标，`program_icons` 设置则为用户做同样的事：

```lua
-- Codex tabs wear OpenAI's mark instead of Codex's tile.
tern.chrome.program_icon("codex", "provider-openai")
-- Neovim (not Vim) wears a sparkle; `nil` takes a choice back.
tern.chrome.program_icon("nvim", "sparkle")
```

```json
{ "program_icons": { "codex": "provider-openai", "nvim": "sparkle" } }
```

`program`（或该设置的键）是程序键或命令名，匹配时不区分大小写。程序键是 Tern 检测到的
结果，来自命令行、程序标题，或 surface 程序以 `hello` 声明的名称，也是每个图标以
`data-program` 携带的值。命令名是正在运行的命令的第一个词（去掉其目录）（`nvim`、`npm`；
在提示符处则是 shell 的，如 `zsh`），也就是 `tab.program` 给出的值；不运行终端的 block
（files、git、browser）没有命令名。各键如下：

| 键 | 程序 |
| --- | --- |
| `shell` | 处于提示符处的 shell |
| `vim`, `helix`, `emacs`, `editor` | Vim 与 Neovim；Helix；Emacs；nano、micro、kakoune 及其他编辑器 |
| `btop`, `htop`, `top`, `monitor` | btop；htop；top；glances、k9s 及其他监视器，以及任务管理器 block |
| `git`, `lazygit` | git、gh、tig 及 git block；lazygit、gitui |
| `claude`, `codex`, `omp`, `hermes`, `gemini`, `copilot`, `cursor-agent`, `opencode`, `agent` | 编码 agent；其余归入 `agent`（aider、amp、goose） |
| `cargo`, `node`, `bun`, `deno`, `python`, `ruby`, `java`, `go`, `lua`, `php`, `elixir`, `haskell`, `swift`, `zig`, `julia` | 语言、运行时及其工具（`node` 涵盖 npm、pnpm、vite；`python` 涵盖 pip、uv 与 notebook block） |
| `docker`, `kubernetes`, `terraform`, `nix`, `packages` | 容器、集群、基础设施、Nix、系统包管理器 |
| `tmux`, `make`, `build`, `ssh`, `pager`, `database` | 多路复用器；make 与 just；其他构建；远程登录；分页器与 man；数据库 shell 与 SQLite block |
| `file`, `screen`, `board`, `carly` | File、screen、board 与 Carly block |
| `other` | 任何其他程序 |

面板的图标按以下先后顺序决定：其会话自身的图标（omp 的会话会设置一个）、第一个插件
为其命令名做出的选择（插件按 id 顺序），然后是为其程序键的选择，接着是该设置中针对
命令名的值，再是针对键的值，最后是 Tern 自己的。`icon` 可以是任何 Tern 图标名
（[图标名称](../elements/data.md#icon-names)），也可以是提供方的徽标，写作 `provider:<id>`。
应用磁贴（`tile-*`）按其原样代替卡片；其他图标绘制在空白卡片上，在纯文本标签页中
则是扁平的。未知名称会在 `program_icon` 中抛出异常；在该设置中则会被跳过。
Settings › Appearance › Program icons 以 `program=icon` 对、用逗号分隔的形式编辑该设置。

面板的每个图标（`.tn-dk-c` 磁贴、`.tn-face` 扁平符号）都携带 `data-program`（其程序键），
以及 `data-icon`（当插件或该设置选择了某个图标时，为所选图标的名称），因此 CSS 可以
重新设定某个程序图标的样式，无论它由什么绘制：

```css
.tn-dk-c[data-program='codex'] { opacity: 0.6; }
```

## 全局 CSS {#global-css}

有两种来源会把样式表安装到本机的每个窗口：

| 来源 | 样式表名称 | 时机 |
| --- | --- | --- |
| 清单 `styles` | `plugin:local:<id>:styles` | 加载时，在 window 入口运行之前。文件按顺序拼接（总计最多 256 KiB）。没有 window 入口也能工作，且 window 入口加载失败时仍会保留。 |
| `tern.css(name, source)` | `plugin:local:<id>:<name>` | 在发起它的那次调用返回时：即入口加载完成之后，或调用它的处理器返回之后。 |

`name` 由 ASCII 字母、数字、`_` 与 `-` 构成，且不能是 `styles`；其他值会抛出
`tern.css: bad name`。以同一名称再次调用 `tern.css` 会就地替换该样式表，
因此插件可以在运行时重新设定样式（从命令、事件、定时器发起）。

远程主机的插件也会为窗口设定样式：已连接主机上每个带清单 `styles` 的 Ready 插件
都会以 `plugin:<slot>:<id>:styles` 安装，其中 `<slot>` 是该主机在此窗口中的编号。
只有清单样式会跨主机传递：`tern.css` 属于 window 半区，而远程主机的 window 半区
不在你的窗口中运行。参见 [分发](distribution.md#remote-hosts)。

Web 标签页不运行 Lua，因此 `tern.css` 样式表永远到不了它那里。它会安装为其提供服务的
守护进程中 Ready 插件的清单 `styles`，名称为 `plugin:0:<id>:styles`，并在该守护进程的
插件重载时重新安装。

### 层叠 {#the-cascade}

插件样式表位于 Tern 自己的样式表之后，因此同等特异性的规则会胜过 Tern 的规则。
样式表在首次安装其名称时排在最后，被替换时保持原位。重载会移除所有 `plugin:local:*`
样式表并重新安装：先装清单样式，再装 `tern.css` 样式表。插件之间（以及本地与远程主机
样式表之间）的顺序会随重载而变动；不要依赖它，当两个插件为相同元素设定样式时应依靠
特异性。用户的 [CSS 主题](themes.md#css-themes) 排在所有插件样式表之后，并胜过它们全部。

CSS 解析错误不会抛出：它们会以 `plugin style sheet has errors` 连同样式表名称记入日志。

### 常用的选择器 {#useful-selectors}

| 目标 | 选择器 |
| --- | --- |
| 插件的状态片段 | `#statusline .sl-plugin[data-plugin='<id>']`，可配合 `[data-tone='…']` 与 `.on` |
| 插件的 Files 面板按钮 | `.ft-head .ft-plugin[data-plugin='<id>']`，其中一个可带 `[data-id='<button>']` |
| 标签页、面板行与停放卡片上的面板程序图标 | `.tn-dk-c`（应用磁贴）与 `.tn-face`（扁平符号），可配合 `[data-program='<key>']`（[程序图标](#program-icons)）、选定图标时的 `[data-icon='<name>']`、`[data-pane='<id>']`，以及 `[data-st='waiting'\|'failed'\|'working'\|'done'\|'bell']` |
| 插件 block 的各个区域 | `.sf-main[data-surface='plugin.<plugin>.<block>']`，以及 `.sf-dock` 与 `.sf-layer` |
| block 或 lens 视图中的节点 | `.sf-<kind>`（`.sf-table`、`.sf-badge`、`.sf-card` 等）；来自节点 `role` 属性的 `[data-role='…']` |
| lens block | `.sf-block[data-role='lens.plugin.<plugin>.<lens>']`，可配合 `[data-state='running']` 或 `[data-state='done']`，以及失败退出后的 `.failed` |

插件 block 的类型以区域元素的 `data-surface` 属性进入 CSS，而不是 `data-role`：
`data-role` 属于其中的节点，它们各自携带自己的 `role` 属性。

为自己的节点指定 `role`（任何节点都可以带一个），再按它设定样式：role 名称由你决定，
`[data-role='myplugin.row']` 不会与 Tern 的样式冲突。Tern 的样式表通过 `--accent`、
`--t1` 至 `--t4`（文本由最强到最弱）、`--ok`、`--warn` 与 `--bad` 等变量着色；
使用这些变量可以让插件的样式在浅色与深色主题下都保持正确。白色文字或字形应绘制在
`--accent-fill` 上，即把主题的强调色压暗到白色仍可阅读的程度；`--accent` 本身用于
环形、淡色与边框。

### 图片：`url()` {#images-url}

全局样式表的 `url()` 指向插件的某个文件：相对于插件目录（即存放 `plugin.toml` 的目录，
无论该规则位于 `styles` 的哪个文件）的路径，例如 `url(icons/ts.svg)` 或
`url('./icons/ts.svg')`。Tern 在安装样式表时解析它，清单 `styles` 与 `tern.css` 样式表
都是如此，并且无论多少规则与行使用同一张图，该图只加载一次。

- `background-image` 可绘制 SVG、PNG、JPEG、GIF、WebP、BMP、ICO 与 TIFF 文件
  （动画取第一帧），每边最大 4096 px。SVG 按显示的缩放比栅格化；栅格图的 CSS 尺寸
  即其像素尺寸。`background-size`、`-position` 与 `-repeat` 照常生效。
- `data:` URL（`data:image/svg+xml,…`，base64 或百分号编码）在任何位置都可用，
  在远程主机的样式表中同样可用；`url(#id)` 过滤器引用保持原样。
- 以下情形会被拒绝，并按每个 URL 以 `plugin style sheet url() …` 连同插件 id 记录
  一次日志：绝对路径、其他协议（`https:`、`file:`）、`..`、指向插件目录之外的链接、
  缺失的文件，以及远程主机样式表中任何文件的 `url()`（这些文件位于该主机）。
  被拒绝的 `url()` 不绘制任何内容；其所在规则的其余部分仍然生效。
- 路径按字面处理：不做百分号解码，`?query` 或 `#fragment` 会被忽略。
- `url()` 也可用在自定义属性中（先 `--icon: url(a.svg)`，再
  `background-image: var(--icon)`）：它在声明该属性的位置解析。
- `mask-image` 只接受渐变：其中的 `url()` 能解析但不会遮罩任何内容，
  因此要给单色图标着色，应直接以所需颜色提供图标文件。

### 文件图标 {#file-icons}

Files 面板的各行会标注其条目，使样式表可以为每个条目指定自己的图标，就像 VS Code
图标主题那样。每一行 `.ft-row` 及其图标框 `.ft-ic`（14×14 px，内含自带的 `svg.ico`：
Tern 为条目提供的图标，以及 Material Icon Theme 的字形，颜色取该行的文本色）都带有：

| 属性 | 值 |
| --- | --- |
| `data-name` | 条目名称的小写形式：`cargo.lock`、`.env`、`foo.test.ts`。紧凑文件夹链的行（`crates/tern/src`）取最后一个文件夹的名称。 |
| `data-ext` | 名称中最后一个点之后的文本，小写且不含点：`lock`、`ts`，`archive.tar.gz` 为 `gz`。文件夹、`.env` 这类点文件，以及没有点（`justfile`）或以点结尾的名称，此值为空。 |
| `data-kind` | `dir` 或 `file`（链接按其指向的对象计）。 |
| `data-open` | 仅文件夹：展开时为 `true`，折叠时为 `false`。 |

这些属性在本地与远程根目录下都成立，并随行的滚动而更新。`.ft-ic` 具有
`background-repeat: no-repeat`、`background-position: center` 与
`background-size: contain`，因此主题可以设置 `background-image` 并隐藏自带的字形：

```css
/* every file without a better match */
.ft-ic[data-kind='file'] { background-image: url(icons/file.svg); }
/* by extension */
.ft-ic[data-kind='file'][data-ext='ts'] { background-image: url(icons/typescript.svg); }
/* by a multi-part extension: a suffix match */
.ft-ic[data-kind='file'][data-name$='.test.ts'] { background-image: url(icons/test-ts.svg); }
/* by exact name */
.ft-ic[data-kind='file'][data-name='cargo.lock'] { background-image: url(icons/lock.svg); }
/* folders, collapsed and expanded, by name */
.ft-ic[data-kind='dir'] { background-image: url(icons/folder.svg); }
.ft-ic[data-kind='dir'][data-open='true'] { background-image: url(icons/folder-open.svg); }
.ft-ic[data-kind='dir'][data-name='src'] { background-image: url(icons/folder-src.svg); }
.ft-ic[data-kind='dir'][data-name='src'][data-open='true'] { background-image: url(icons/folder-src-open.svg); }
/* hide the stock glyph wherever the theme paints */
.ft-ic[data-kind] > svg.ico { display: none; }
```

匹配之间由特异性决定，因此应像上例那样把主题从通用排到具体，与 VS Code 的解析顺序
一致：精确名称（`fileNames`、`folderNames` / `folderNamesExpanded`），然后是最长的
匹配后缀（对 `data-name` 使用 `$=`），然后是扩展名（`fileExtensions`），最后是默认值
（`file`、`folder` / `folderExpanded`）。每个属性增加的优先级相同，因此可以给更具体的
规则多加一个属性（`[data-kind='file']`），或把它放在样式表中更靠后的位置。匹配名称时
使用小写：这些属性本身就是小写。从图标主题的 JSON 生成样式表，就是遍历其映射表的循环；
一千条规则的主题只会为可见行所用到的图标付出代价。

## 示例 {#worked-examples}

### 标签页与窗口标题 {#tab-and-window-titles}

```lua
local function basename(path: string): string
	return string.match(path, "([^/]+)/*$") or path
end

tern.chrome.tab_title(function(tab)
	if tab.name then
		return nil
	end
	local cwd = tab.cwd or ""
	local dir = if cwd == "" then "~" else basename(cwd)
	local label = if tab.program == "" then dir else dir .. " · " .. tab.program
	if tab.panes > 1 then
		label ..= string.format(" (%d)", tab.panes)
	end
	return label
end)

tern.chrome.window_title(function(win)
	if win.tab == nil then
		return nil
	end
	return win.space .. " — " .. win.tab
end)
```

### 来自焦点目录的片段 {#a-segment-from-the-focused-directory}

该片段只依赖 `pane.cwd`，而它属于输入的一部分，因此缓存恰到好处：
每个目录只读取一次文件。

```lua
local function first_word(path: string): string?
	if not tern.fs.exists(path) then
		return nil
	end
	local ok, text = pcall(tern.fs.read, path)
	if not ok then
		return nil
	end
	return string.match(text, "^%s*(%S+)")
end

tern.chrome.status(function(pane)
	local cwd = pane.cwd
	if cwd == nil or cwd == "" then
		return nil
	end
	local version = first_word(cwd .. "/.nvmrc")
	if version == nil then
		return nil
	end
	return { { text = "node " .. version, tone = "muted" } }
end)
```

### 由进程提供数据的片段 {#a-segment-fed-by-a-process}

该插件每分钟轮询一次 `gh`，获取等待审查的拉取请求数量，并在每次得到答案后调用
`tern.chrome.refresh()`，使片段显示新的计数。点击该片段会运行插件的命令。

```lua
local pending: number? = nil

local function segments(_pane: PaneInfo): { StatusSegment }?
	if pending == nil or pending == 0 then
		return nil
	end
	return {
		{ text = tostring(pending) .. " to review", icon = "branch", tone = "accent", command = "plugin.reviews.open" },
	}
end

local function poll()
	tern.process.run({ "gh", "search", "prs", "--review-requested=@me", "--state=open", "--json", "number" }, { timeout_ms = 15000 }, function(result, _cx)
		if result.status == 0 then
			local ok, list = pcall(tern.json.decode, result.stdout)
			if ok then
				pending = #list
				tern.chrome.refresh() -- drops the cached segments and redraws
			end
		end
		tern.timer(60000, poll)
	end)
end

tern.chrome.status(segments)
tern.command({
	id = "open",
	title = "Open review queue",
	run = function(cx)
		cx:open("https://github.com/pulls/review-requested")
	end,
})
poll()
```

`tern.process.run` 在 iOS 上会抛出异常；面向 iPad 的插件应先检查
`tern.runtime.os`。参见 [文件、进程与存储](io.md)。

### 为片段与 block 设定样式 {#styling-segments-and-a-block}

`plugin.toml`：

```toml
styles = ["reviews.css"]
```

`reviews.css`：

```css
#statusline .sl-plugin[data-plugin='reviews'] {
	padding: 0 6px;
	border-radius: 4px;
	background: var(--accent-fill);
	color: white;
}

.sf-main[data-surface='plugin.reviews.queue'] [data-role='reviews.stale'] {
	color: var(--t4);
}
```

以及一份由 window 半区在运行时切换的样式表：

```lua
local compact = false

tern.command({
	id = "compact",
	title = "Toggle compact review rows",
	run = function(_cx)
		compact = not compact
		tern.css("density", if compact then ".sf-main[data-surface='plugin.reviews.queue'] .sf-item { min-height: var(--sf-lh); }" else "")
	end,
})
```

## 另见 {#see-also}

- [构建视图](views.md)：节点类型，`role` 与 `tone` 属性。
- [视图样式](../styles/index.md)：视图节点的样式钩子、
  [CSS 变量](../styles/variables.md) 与 [受支持的 CSS](../styles/css.md)。
- [命令、按键与覆盖](commands.md#action-names)：供片段 `command` 使用的动作名。
- [Window API](../reference/api-window.md)：`TabInfo`、`PaneInfo`、
  `StatusSegment`。
- [限制](../reference/limits.md)：预算与样式大小上限。
- [自定义主题](themes.md)：用 CSS 文件而非插件为 Tern 重新配色与设定样式，
  包括其终端配色。
