# 内置动作 {#built-in-actions}

window 插件可以传给 [`tern.override`](api-window.md#ternoverride)、[`cx:command`](api-window.md#window-cx) 与 [`tern.bind`](api-window.md#ternbind) 的每个名称。命令是命令面板中的行；动作则是键位映射所运行的更广的一组名称，其中包含每一条命令。

## 名称一览 {#names-at-a-glance}

| 名称形式 | 示例 | `tern.bind` | `tern.override` / `cx:command` |
| --- | --- | --- | --- |
| 命令 id | `new_tab`, `layout:rail` | 是 | 是 |
| 仅键位映射的动作 | `palette`, `goto_tab:3`, `text:\e` | 是 | 否 |
| 视图组合键 | `editor.toggle_comment`, `sqlite.write`, `browser.back` | 是 | 否 |
| 插件命令 | `plugin.hello.say_hi` | 是 | 否 |
| 插件函数绑定 | `plugin.hello.bind.0` | 由 `tern.bind` 生成 | 否 |

`tern.override` 与 `cx:command` 只接受下面列出的[命令 id](#commands)：两者都会在 Tern 的命令列表中查找该 id。其他所有动作名称，包括其他插件的 `plugin.*` 命令，都会被拒绝。

`cx:action(name)` 会立即运行上述每一种动作名称形式，而不仅限于命令。视图动作作用于聚焦的视图。未知的插件动作会抛出错误，而不是静默地什么都不做。Carly 具备与已加载的 window 插件相同的动作能力：内置命令、仅键位映射的动作、聚焦视图的动作，以及每个已加载插件的命令。

## 命令 {#commands}

Tern 有 174 条内置命令。id 是 `tern.override`、`cx:command`、`tern.bind` 与 `settings.json` 的 `keybinds` 所接受的内容；label 则是命令面板中的行。带 `:` 的 id 表示每个取值对应一条命令（`layout:rail`、`layout:float` 等）；每个取值都是独立的 id，而裸前缀（`layout`）不是命令。

```lua
tern.override("split_right", function(cx)
	cx:toast("info", "Splitting")
	cx:command("split_right") -- runs the built-in; overrides are out of reach
	return true
end)
```

**Apple** 与 **PC** 两列分别是 Tern 在 Apple 键盘与 PC 键盘（Windows 与 Linux；Linux 上的 Win 键读作 Super）上的默认键。`keymap` 预设或用户设置的 `keybinds` 会改变它们（[键位映射分层](../guides/commands.md#keymap-layering)），而设置 › 键盘会显示实际生效的键。当同一个键运行多个动作时，一次按键会运行在其落点处适用的第一个：⌘L 会聚焦浏览器 block 的地址栏，并在代码视图中选中整行。在 PC 上，Ctrl+Shift+PgUp 与 Ctrl+Shift+PgDn 滚动终端；单独的 PgUp 与 PgDn 则交给终端的程序。

每条命令都可以被覆盖。覆盖在该命令运行之初就被查询，因此无论命令从何处启动都会生效：命令面板、按键、菜单、工具栏按钮，或 Tern 的其他部分。在当前上下文中什么都不做的命令（例如没有聚焦任何 file block 时的 `save`）仍会先到达覆盖。

### 标签页、窗口与会话 {#tabs-windows-and-sessions}

| Id | 命令面板标签 | Apple | PC | 备注 |
| --- | --- | --- | --- | --- |
| `new_tab` | 新建标签页 | ⌘T | Ctrl+Shift+T | |
| `new_window` | 新建窗口 | ⌘N | Ctrl+Shift+N | |
| `switch_session` | 切换会话… | ⌃⌘K | Ctrl+Shift+Space | 切换器获得焦点时再次按下会关闭它 |
| `new_session` | 新建会话 | | | |
| `rename_session` | 重命名会话… | | | |
| `lock_session` | 锁定会话 | | | 会话锁定期间显示为当前会话 |
| `close_session` | 关闭会话 | | | 破坏性操作 |
| `move_session_up` | 上移会话 | | | 在其所属 host 的会话之间移动，循环；在垂直标签页列表中会话名称上的 ⌥↑ |
| `move_session_down` | 下移会话 | | | 在其所属 host 的会话之间移动，循环；在垂直标签页列表中会话名称上的 ⌥↓ |
| `collapse_all_sessions` | 折叠所有会话 | | | 折叠垂直标签页列表中的每个会话；折叠状态随窗口一同保存 |
| `expand_all_sessions` | 展开所有会话 | | | 展开垂直标签页列表中的每个会话 |
| `close_tab` | 关闭标签页 | ⌥⌘W | Ctrl+Shift+Q, Ctrl+Alt+Shift+W | 破坏性操作 |
| `next_tab` | 下一个标签页 | ⇧⌘] | Ctrl+Shift+→ | |
| `previous_tab` | 上一个标签页 | ⇧⌘[ | Ctrl+Shift+← | |
| `next_tab_across_sessions` | 跨会话的下一个标签页 | | | 越过会话的最后一个标签页后，进入下一个会话的第一个标签页 |
| `previous_tab_across_sessions` | 跨会话的上一个标签页 | | | |
| `move_tab_right` | 向右移动标签页 | | Ctrl+Shift+. | |
| `move_tab_left` | 向左移动标签页 | | Ctrl+Shift+, | |
| `rename_tab` | 重命名标签页… | ⇧⌘R | Ctrl+Alt+Shift+T | |
| `show_previous_tab` | 显示上一个标签页 | ⌃⇧Tab | Ctrl+Shift+Tab | |
| `tidy_tab_title` | 整理标签页标题 | | | |
| `focus_tabs` | 聚焦标签页列表 | | | |
| `peek` | 预览标签页 | ⌃⌥↓ | Ctrl+Alt+↓ | |
| `mission_control` | Mission Control | ⌃⌥↑ | Ctrl+Alt+↑ | 在 Mission Control 与标签页预览中，方向键或 h/j/k/l 移动选择，Home/End 选中第一张或最后一张卡片，⏎ 或 Space 打开它，Esc 关闭 |
| `park_pane` | 停放面板 | ⌃⇧↓ | Ctrl+Shift+↓ | 把聚焦的面板从标签页移到该会话的停放面板中；其程序继续运行。停放面板已打开时，关闭它们 |
| `parked_panes` | 停放面板 | ⌃⇧↑ | Ctrl+Shift+↑ | 打开该会话的停放面板并选中第一张卡片；已打开时，把选中的那个带回聚焦面板旁边 |
| `inbox` | 显示需要关注的收件箱 | ⇧⌘I | Ctrl+Shift+I | |
| `clear_inbox` | 清空需要关注的收件箱 | | | |

### Block 与面板 {#blocks-and-panes}

| Id | 命令面板标签 | Apple | PC | 备注 |
| --- | --- | --- | --- | --- |
| `new_shell_block` | 新建 shell block | ⇧⌘T | ``Ctrl+Shift+` `` | |
| `new_agent_block` | 新建 agent block | ⇧⌘A | Ctrl+Shift+A | |
| `new_browser_block` | 新建浏览器 block… | ⇧⌘B | Ctrl+Shift+B | |
| `new_task_manager_block` | 新建任务管理器 block | | | |
| `profile_process` | 分析进程性能 | | | |
| `new_screen_block` | 新建屏幕 block | | | |
| `release_screen` | 停止控制屏幕 | ⌃⌥Esc | Ctrl+Alt+Esc | 聚焦的屏幕 block 切换为仅查看（⌃⌥⎋，PC 上为 Ctrl+Alt+Esc）。在半秒内再次按下，该组合键会把控制重新打开并转到屏幕的 host |
| `new_git_block` | 新建 git block | ⌥⌘G | Ctrl+Alt+Shift+G | |
| `new_board_block` | 新建看板 block | ⌥⌘K | Ctrl+Alt+Shift+K | |
| `open_board` | 打开看板… | | | |
| `open_as_board` | 以看板打开 | | | |
| `new_canvas_block` | 新建画布 block | ⌥⌘E | Ctrl+Alt+Shift+E | |
| `open_canvas` | 打开画布文件… | | | |
| `open_url_in_split` | 在分屏中打开 URL | | | |
| `focus_address` | 聚焦地址栏 | ⌘L | Ctrl+Shift+L | |
| `inspect_page` | 检查页面 | ⌥⌘I, F12 | F12 | |
| `split_right` | 向右分屏 | ⌘D | Ctrl+Shift+Enter, Ctrl+Shift+D | |
| `split_down` | 向下分屏 | ⇧⌘D | Ctrl+Shift+O | |
| `close_pane` | 关闭 block | ⌘W | Ctrl+Shift+W | 破坏性操作（命令面板会为其着色） |
| `zoom` | 放大 block | ⇧⌘⏎ | Ctrl+Shift+R | |
| `equalize` | 均分分屏 | ⌃⌘= | Alt+Shift+= | |
| `next_pane` | 下一个 block | ⌘] | Ctrl+Shift+] | 在浏览器 block 中，⌘] 改为在页面中前进（[`browser.forward`](#browser-blocks-browser)） |
| `previous_pane` | 上一个 block | ⌘[ | Ctrl+Shift+[ | 在浏览器 block 中，⌘[ 改为在页面中后退（[`browser.back`](#browser-blocks-browser)） |
| `move_pane:left` | 向左移动面板 | ⌥⇧⌘← | Ctrl+Alt+Shift+Home | |
| `move_pane:right` | 向右移动面板 | ⌥⇧⌘→ | Ctrl+Alt+Shift+End | |
| `move_pane:up` | 向上移动面板 | ⌥⇧⌘↑ | Ctrl+Alt+Shift+PgUp | |
| `move_pane:down` | 向下移动面板 | ⌥⇧⌘↓ | Ctrl+Alt+Shift+PgDn | |
| `move_pane_to_tab` | 把面板移到标签页… | | | |
| `move_pane_to_session` | 把面板移到会话… | | | |

### 画中画 {#picture-in-picture}

| Id | 命令面板标签 | Apple | PC | 备注 |
| --- | --- | --- | --- | --- |
| `pip` | 画中画 | ⌃⌘P | Ctrl+Alt+Shift+P | |
| `pip_dock:left` | 画中画停靠到左侧 | | | |
| `pip_dock:right` | 画中画停靠到右侧 | | | |
| `pip_dock:up` | 画中画停靠到上方 | | | |
| `pip_dock:down` | 画中画停靠到下方 | | | |
| `pip_corner:top_left` | 将画中画移到左上角 | | | |
| `pip_corner:top_right` | 将画中画移到右上角 | | | |
| `pip_corner:bottom_left` | 将画中画移到左下角 | | | |
| `pip_corner:bottom_right` | 将画中画移到右下角 | | | |
| `pip_stash_all` | 隐藏所有画中画 | ⌃⌥⌘P | Ctrl+Shift+; | |
| `pip_over` | 画中画覆盖… | | | |
| `new_browser_pip` | 新建浏览器画中画 | ⌥⇧⌘B | Ctrl+Alt+Shift+B | |
| `open_url_in_pip` | 在画中画中打开 URL | | | |

### 终端 {#terminal}

| Id | 命令面板标签 | Apple | PC | 备注 |
| --- | --- | --- | --- | --- |
| `copy` | 复制 | ⌘C | Ctrl+Shift+C, Ctrl+Insert | 在 Apple 键盘上，⌘C 也被网格与文本字段原生占用 |
| `paste` | 粘贴 | ⌘V | Ctrl+Shift+V, Shift+Insert | 在 Apple 键盘上，⌘V 同样被原生占用 |
| `paste_selection` | 粘贴选中内容 | | Ctrl+Shift+S | |
| `find` | 在回滚缓冲区中查找 | ⌘F | Ctrl+Shift+F | |
| `scroll_line_up` | 上滚一行 | | | |
| `scroll_line_down` | 下滚一行 | | | |
| `scroll_page_up` | 上滚一页 | ⌘PgUp | Ctrl+Shift+PgUp | |
| `scroll_page_down` | 下滚一页 | ⌘PgDn | Ctrl+Shift+PgDn | |
| `scroll_top` | 滚动到顶部 | ⌘Home | Ctrl+Shift+Home | |
| `scroll_bottom` | 滚动到底部 | ⌘End | Ctrl+Shift+End | |
| `previous_prompt` | 跳到上一个提示符 | ⌘↑ | Ctrl+Shift+Z | |
| `next_prompt` | 跳到下一个提示符 | ⌘↓ | Ctrl+Shift+X | |
| `reply_start` | 跳到回复开头 | ⌘↑ | Ctrl+Shift+Z | 在 omp 的对话中：视图上方那条回复的开头；在那里为 ⌘↑ / Ctrl+Shift+Z |
| `open_scrollback` | 在编辑器中打开回滚缓冲区 | | Ctrl+Shift+H | |
| `toggle_output_fold` | 折叠或展开过长的输出 | | | 离视图最近的那段长命令输出；点击其 `▸ N more lines` 标记同样可以做到 |
| `clear` | 清屏并清空回滚缓冲区 | ⇧⌘K | Ctrl+Shift+K | |
| `restart` | 重启 shell | | | |
| `goto_directory` | 转到目录… | ⇧⌘G | Ctrl+Shift+G | |
| `insert_path` | 插入路径… | ⌥⌘P | Ctrl+Shift+/ | |

### Carly 命令 {#carly}

| Id | 命令面板标签 | Apple | PC | 备注 |
| --- | --- | --- | --- | --- |
| `carly` | 询问 Carly… | 连按 ⌘ 两次 | 连按 Ctrl 两次 | |
| `carly_new_conversation` | Carly：新建对话 | | | |
| `carly_tasks` | Carly：定时任务 | | | 打开 设置 › Carly › 定时任务 |
| `new_carly_block` | 新建 Carly block | | | 与 Carly 的对话作为聊天显示在聚焦的 block 旁边 |

### 数据库与笔记本 {#databases-and-notebooks}

| Id | 命令面板标签 | Apple | PC | 备注 |
| --- | --- | --- | --- | --- |
| `new_database` | 新建数据库… | | | |
| `new_memory_database` | 新建内存数据库 | | | |
| `open_database` | 打开数据库… | | | |
| `open_database_read_only` | 以只读方式打开数据库… | ⇧⌘O | Ctrl+Alt+Shift+O | |
| `open_recent_database` | 打开最近的数据库 | | | |
| `new_notebook` | 新建笔记本 | | | |
| `open_notebook` | 打开笔记本… | | | |

### 文件与笔记 {#files-and-notes}

| Id | 命令面板标签 | Apple | PC | 备注 |
| --- | --- | --- | --- | --- |
| `open_file` | 打开文件… | ⌘O, ⌘P | Ctrl+F12 | |
| `new_note` | 新建笔记 | ⌥⌘N | Ctrl+Alt+Shift+N | |
| `session_note` | 会话笔记 | | | |
| `pane_note` | Block 笔记 | | | |
| `reopen_note` | 重新打开已关闭的笔记 | ⌘Z | Ctrl+Shift+Z | |
| `save` | 保存 | ⌘S | Ctrl+S | |
| `save_as` | 另存为… | ⌥⇧⌘S | Ctrl+Alt+Shift+S | |
| `revert` | 恢复到已保存版本 | | | |
| `toggle_source` | 切换 Markdown 源码 | ⌘E | Ctrl+E | |
| `go_to_line` | 转到行… | ⌃G | Ctrl+G | |
| `toggle_wrap` | 自动换行 | ⌥Z | Alt+Z | |
| `next_change` | 下一处改动 | ⌥F5 | Alt+F5 | |
| `previous_change` | 上一处改动 | ⌥⇧F5 | Alt+Shift+F5 | |
| `fold_all` | 全部折叠 | | | 代码视图（编辑器的 ⇧⌥⌘[） |
| `unfold_all` | 全部展开 | | | 代码视图（编辑器的 ⇧⌥⌘]） |
| `reopen_with_encoding` | 以指定编码重新打开… | | | |
| `line_endings` | 转换行尾… | | | |
| `browse_folder` | 浏览文件夹… | | | 聚焦文件旁边的文件，效果如同在工具栏中点击其名称 |
| `reveal_file` | 在访达中显示文件 | | | |
| `open_file_outside` | 用默认应用打开文件 | | | |
| `copy_file_path` | 复制文件路径 | | | |

### Files 面板 {#files-pane}

| Id | 命令面板标签 | Apple | PC | 备注 |
| --- | --- | --- | --- | --- |
| `files` | 显示/隐藏文件 | ⌃⌘E | Ctrl+Shift+E | |
| `focus_files` | 聚焦 Files | ⇧⌘E | Ctrl+0 | |
| `reveal_active_file` | Files：显示当前文件 | | | |
| `reveal_cwd` | Files：显示目录 | | | |
| `files_pin` | Files：固定文件夹 / 跟随 block | | | |
| `open_folder` | Files：打开文件夹… | | | |
| `files_filter` | Files：筛选… | | | |
| `files_collapse_all` | Files：全部折叠 | | | |
| `files_toggle_hidden` | Files：显示/隐藏隐藏文件 | | | |

### 外观与布局 {#appearance-and-layout}

| Id | 命令面板标签 | Apple | PC | 备注 |
| --- | --- | --- | --- | --- |
| `increase_font_size` | 增大字号 | ⌘=, ⇧⌘= | Ctrl+Shift+= | |
| `decrease_font_size` | 减小字号 | ⌘- | Ctrl+Shift+- | |
| `reset_font_size` | 重置字号 | ⌘0 | Ctrl+Shift+Backspace | |
| `theme` | 更换主题… | ⌃⌘T | Ctrl+Shift+M | |
| `opacity` | 更改不透明度… | | | |
| `blur` | 更改模糊… | | | |
| `appearance:system` | 跟随系统的外观 | | | |
| `appearance:light` | 浅色外观 | | | |
| `appearance:dark` | 深色外观 | | | |
| `copy_on_select` | 选中即复制 | | | |
| `contrast` | 自动对比度校正 | | | |
| `native_surfaces` | 程序原生 surface | | | |
| `surface_headings:auto` | Markdown 标题：自动 | | | |
| `surface_headings:annotated` | Markdown 标题：带注释 | | | |
| `surface_headings:sized` | Markdown 标题：按字号 | | | |
| `surface_diffs` | 改动：行内或分栏 | | | |
| `surface_fold` | 折叠工具调用 | | | |
| `expand_thoughts` | 展开思考过程 | | | |
| `composer_text` | 输入框：纯文本或 Markdown | | | |
| `chat:reader` | 聊天样式：Reader | | | |
| `chat:spine` | 聊天样式：Spine | | | |
| `chat:console` | 聊天样式：Console | | | |
| `native_prompt` | 原生提示符 | | | |
| `prompt_style` | 提示符样式… | | | |
| `prompt_part:palette` | 提示符：下一组配色 | | | |
| `prompt_part:fill` | 提示符：下一种填充 | | | |
| `prompt_part:shape` | 提示符：下一个形状 | | | |
| `prompt_part:frame` | 提示符：下一个外框 | | | |
| `prompt_part:line_end` | 提示符：外框线末端开或关 | | | |
| `prompt_part:gap` | 提示符：下一个间距 | | | |
| `prompt_part:char` | 提示符：下一个提示符字符 | | | |
| `prompt_part:separator` | 提示符：下一组分隔符 | | | |
| `prompt_part:git` | 提示符：下一种 git 格式 | | | |
| `prompt_part:dir` | 提示符：下一种目录格式 | | | |
| `prompt_part:icons` | 提示符：图标开或关 | | | |
| `prompt_part:clock` | 提示符：下一个时钟 | | | |
| `prompt_segments` | 提示符分段… | | | |
| `prompt_collapse` | 折叠已过去的提示符 | | | |
| `next_layout` | 下一个布局 | ⌃⌘L | Ctrl+Shift+L | |
| `layout:rail` | 布局：Rail | | | |
| `layout:float` | 布局：Float | | | |
| `layout:tiles` | 布局：Tiles | | | |
| `layout:studio` | 布局：Studio | | | |
| `toggle_tab_orientation` | 切换标签页方向 | ⇧⌘S | Ctrl+Shift+\ | |
| `tabs:horizontal` | 水平标签页 | | | |
| `tabs:vertical` | 垂直标签页 | | | |
| `toggle_sidebar` | 显示/隐藏侧边栏 | ⌘B | Ctrl+Alt+Shift+\ | |
| `pane_headers:never` | 面板标题：从不 | | | |
| `pane_headers:split` | 面板标题：分屏时 | | | |
| `pane_headers:always` | 面板标题：始终 | | | |
| `status_bar` | 显示状态行 | | | |
| `interface_style` | 更改界面风格… | | | |

### 远程 host {#remote-hosts}

| Id | 命令面板标签 | Apple | PC | 备注 |
| --- | --- | --- | --- | --- |
| `switch_host` | 切换 host… | ⌃⌘H | Ctrl+Shift+J | |
| `add_remote_host` | 添加远程 host… | ⌃⌘N | Ctrl+Shift+Y | |
| `new_session_on_host` | 在 host 上新建会话… | | | |
| `disconnect_host` | 断开与 host 的连接… | | | |
| `update_remote_host` | 更新远程 host… | | | 已连接的 host 运行较旧版本的 Tern 时列出 |

### 应用 {#app}

| Id | 命令面板标签 | Apple | PC | 备注 |
| --- | --- | --- | --- | --- |
| `preferences` | 设置… | ⌘, | Ctrl+, | 设置窗口获得焦点时再次按下会关闭它；设置窗口已打开但无焦点时，聚焦它 |
| `secure_keyboard_entry` | 切换安全键盘输入 | | | 仅 macOS |
| `open_config` | 打开 settings.json | | Ctrl+Shift+F2 | |
| `reload_config` | 重新加载设置 | | Ctrl+Shift+F5 | |
| `reload_plugins` | 重新加载插件 | | | |
| `open_logs` | 打开日志与应用状态 | | | |
| `open_app_data` | 打开应用数据文件夹 | | | |
| `quit` | 退出 Tern | ⌘Q | Alt+F4 | 破坏性操作 |
| `restart_tern` | 重启 Tern | | | |
| `fps` | 调试：显示 FPS | | | |
| `devtools` | 切换开发者工具 | ⌥⌘I, F12 | F12 | 在浏览器 block 中，这些键改为检查其页面（`inspect_page`） |
| `screenshot` | 截图 | | | |
| `show_commands` | 显示所有命令 | ⇧⌘P | Ctrl+Shift+F1 | 命令面板列出命令且获得焦点时再次按下会关闭它 |
| `sign_out` | 退出 Stencil 登录 | | | |
| `check_for_updates` | 检查更新 | | | |
| `release_notes` | 新功能介绍：发行说明 | | | |
| `help` | 帮助与文档 | | | 打开 docs.stencil.so/tern |
| `restart_to_update` | 重启以更新 | | | |
| `restart_session_daemon` | 重启会话守护进程 | | | |
| `install_omp` | 安装 omp | | | 桌面端；在 Tern 管理 omp 之前 |
| `check_omp_updates` | 检查 omp 更新 | | | 在 Tern 管理 omp 期间 |
| `stop_managing_omp` | 停止管理 omp | | | 在 Tern 管理 omp 期间 |


### 覆盖如何运行 {#how-overrides-run}

1. 一条命令开始运行。若没有已加载的插件为其 id 注册覆盖，则运行内置实现。
2. 否则，各插件针对该 id 的覆盖按插件顺序运行（插件按 id 排序加载），每次调用都带有新的 window `cx`，钩子名为 `override <id>`。
3. 第一个返回真值的覆盖会中止其余覆盖，并跳过内置实现。抛出错误或超出预算的处理函数按 `false` 计；该失败会以提示告知。
4. 若没有任何覆盖返回真值，则运行内置实现。

任一插件处理函数运行期间，该窗口的插件会被移出窗口，因此处理函数中的 `cx:command(id)` 直接运行内置实现：不会再运行任何覆盖，也不会有递归。

## 键位动作 {#keymap-actions}

`tern.bind(chord, action)` 接受本节中的任意名称、任意[命令 id](#commands)，或某个[插件动作](#plugin-actions)。名称在重建键位映射时解析，所用解析器与 `settings.json` 的 `keybinds` 相同。

| 动作 | 作用 | Apple | PC | 备注 |
| --- | --- | --- | --- | --- |
| `palette` | 打开命令面板 | ⌘K | Ctrl+Shift+P | 命令面板显示“全部”且获得焦点时再次按下会关闭它 |
| `goto_tab:N` | 激活会话的第 `N` 个标签页 | ⌘1 … ⌘9, ⌥1 … ⌥9 | Ctrl+Shift+1 … Ctrl+Shift+9, Ctrl+Shift+0（第 10 个标签页）, Alt+1 … Alt+9 | 从 1 起计；`goto_tab:0` 与非数字不会解析 |
| `last_tab` | 激活会话的最后一个标签页 | | | |
| `focus_pane:DIR` | 聚焦 `DIR` 方向上的面板 | ⌥⌘ 加方向键 | Ctrl+Alt+Shift 加方向键 | `left`、`right`、`up`、`down` |
| `resize_split:DIR` | 移动最近的分隔条 | ⌃⌘ 加方向键 | Alt+Shift 加方向键 | `left`、`right`、`up`、`down` |
| `find_older` | 跳到较早的查找结果 | ⌘G | F3, Ctrl+Shift+G | 查找栏打开时 |
| `find_newer` | 跳到较新的查找结果 | ⇧⌘G | Shift+F3 | 查找栏打开时 |
| `scroll_top_at_shell` | 滚动到顶部 | | | 在终端中，处于全屏程序之外时 |
| `scroll_bottom_at_shell` | 滚动到底部 | | | 在终端中，处于全屏程序之外时 |
| `text:BYTES` | 把 `BYTES` 写入聚焦终端所运行的程序 | | | 转义 `\e`、`\r`、`\n`、`\t`、`\\`、`\xHH`；其他转义不会解析 |

`unbind`（以及 `[]`）是 `settings.json` 的 `keybinds` 专有的；它不是动作名称，因此 `tern.bind(chord, "unbind")` 会被略过。

```lua
tern.bind("ctrl+alt+1", "goto_tab:1")
tern.bind("ctrl+alt+c", "text:\x03") -- send ^C
tern.bind("ctrl+a>%", "split_right")
```

### 文本编辑：`edit.*` {#text-editing-edit}

作用于聚焦的编辑器或文本字段，从不用在终端上（终端的程序会保留该按键）。

| 动作 | 作用 |
| --- | --- |
| edit.select_all | 全选 |
| edit.copy | 复制 |
| edit.cut | 剪切 |
| edit.paste | 粘贴 |
| edit.undo | 撤销 |
| edit.redo | 重做 |

### 代码与十六进制视图：`editor.*` {#code-and-hex-views-editor}

由聚焦的代码视图或十六进制视图运行。它们只作用于单个组合键：在 `settings.json` 中，把 `editor.*` 动作绑定到序列上会被拒绝。

| 动作 | 作用 | Apple | PC |
| --- | --- | --- | --- |
| editor.move_lines_up | 把选中的行上移 | ⌥↑ | Alt+↑ |
| editor.move_lines_down | 把选中的行下移 | ⌥↓ | Alt+↓ |
| editor.duplicate_lines_up | 复制选中的行（选中上方那份） | ⌥⇧↑ | Alt+Shift+↑ |
| editor.duplicate_lines_down | 复制选中的行（选中下方那份） | ⌥⇧↓ | Alt+Shift+↓ |
| editor.add_caret_above | 在上一行添加光标 | ⌃⇧↑ | Win+Shift+↑ |
| editor.add_caret_below | 在下一行添加光标 | ⌃⇧↓ | Win+Shift+↓ |
| editor.add_next_occurrence | 选中该词，然后添加下一处出现 | ⌘D | Ctrl+Shift+D, Ctrl+D |
| editor.skip_occurrence | 跳到下一处出现 | ⌥⌘D | Ctrl+Alt+D |
| editor.select_all_occurrences | 选中所有出现 | ⇧⌘L | Ctrl+F2, Ctrl+Shift+L |
| editor.select_line | 选中各光标所在的整行，含换行符；再次按下再扩一行（PC 上的 Tern：Ctrl+L） | ⌘L | Ctrl+L |
| editor.carets_at_line_ends | 在每处选区的行尾各放一个光标 | ⌥⇧I | Alt+Shift+I |
| editor.toggle_comment | 切换行注释 | ⌘/ | Ctrl+/ |
| editor.indent | 增加缩进 | Tab | Tab |
| editor.outdent | 减少缩进 | ⇧Tab | Shift+Tab |
| editor.undo | 撤销 | ⌘Z | Ctrl+Z |
| editor.redo | 重做 | ⇧⌘Z | Ctrl+Shift+Z |
| editor.escape | 退出一层：查找栏、额外光标、选区、行内 block | Esc | Esc |
| editor.leave_inline_block | 离开行内代码块（Markdown）；在 block 视图中该键在下方新开一行 | ⌘⏎ | Ctrl+Enter |
| editor.newline_below | 在每个光标所在行下方新增一行而不拆分该行，缩进与在该行末尾按 ⏎ 相同（文件代码视图） | ⌘⏎ | Ctrl+Enter |
| editor.newline_above | 在每个光标所在行上方新增一行，沿用其缩进（闭括号之前多一级） | ⌥⌘⏎ | Ctrl+Alt+Enter |
| editor.toggle_wrap | 切换自动换行 | ⌥Z | Alt+Z |
| editor.find | 查找 | ⌘F | Ctrl+F |
| editor.find_replace | 查找并替换 | ⌥⌘F | Ctrl+Alt+F |
| editor.go_to_line | 转到行（十六进制视图：转到偏移） | ⌃G | Win+G |
| editor.find_next | 下一个匹配 | ⌘G | F3, Ctrl+G |
| editor.find_previous | 上一个匹配 | ⇧⌘G | Shift+F3, Ctrl+Shift+G |
| editor.use_selection_for_find | 用选区做查找 | ⌘E | Ctrl+E |
| editor.delete_to_line_end | 删除到行末的内容（已在行末时删除换行符）并放入 kill 缓冲区；除剪贴板外，所有代码视图共享该缓冲区；两次按键之间没有其他编辑或光标移动的连续按下会累加 | ⌃K | Win+K |
| editor.yank | 在每个光标处插入 kill 缓冲区内容（若删入的光标数与片段数相同，则每个光标一片） | ⌃Y | Win+Y |
| editor.join_lines | 合并选区涉及的各行（光标的行与其下一行）：每个换行符及其两侧空白变成一个空格，`)` `]` `}` 之前或空行处不加空格（PC 上的 Tern：Ctrl+J） | ⌃J | Ctrl+J, Win+J |
| editor.next_change | 下一处 git 改动（循环） | ⌥F5 | Alt+F5 |
| editor.previous_change | 上一处 git 改动（循环） | ⇧⌥F5 | Alt+Shift+F5 |
| editor.subword_left | 移到上一个子词开头（camelCase 驼峰、缩写、数字、`snake_case` 与 `kebab-case` 的各段；PC：Ctrl+Alt+←） | ⌃⌥← | Ctrl+Alt+←, Win+Alt+← |
| editor.subword_right | 移到下一个子词末尾（PC：Ctrl+Alt+→） | ⌃⌥→ | Ctrl+Alt+→, Win+Alt+→ |
| editor.select_subword_left | 扩展到上一个子词开头 | ⌃⌥⇧← | Win+Alt+Shift+← |
| editor.select_subword_right | 扩展到下一个子词末尾 | ⌃⌥⇧→ | Win+Alt+Shift+→ |
| editor.delete_subword_backward | 删除到上一个子词开头（PC：Ctrl+Alt+Backspace） | ⌃⌥⌫ | Ctrl+Alt+Backspace, Win+Alt+Backspace |
| editor.delete_subword_forward | 删除到下一个子词末尾 | ⌃⌥⌦ | Win+Alt+Delete |
| editor.expand_selection | 扩大每处选区：子词、词、字符串内容、字符串、括号内容、括号（向外）、整行、文档（PC：Alt+Shift+→） | ⌃⇧→ | Alt+Shift+→, Win+Shift+→ |
| editor.shrink_selection | 回到上次扩大所替换的那处选区（PC：Alt+Shift+←） | ⌃⇧← | Alt+Shift+←, Win+Shift+← |
| editor.fold | 折叠每个光标周围最内层的范围，或折叠从多行选区开始的每个范围 | ⌥⌘[ | Ctrl+Alt+[ |
| editor.unfold | 展开选区所在行的折叠 | ⌥⌘] | Ctrl+Alt+] |
| editor.toggle_fold | 在主光标处折叠或展开 | ⌥⌘\ | Ctrl+Alt+\ |
| editor.fold_all | 折叠所有范围（含嵌套范围） | ⇧⌥⌘[ | Ctrl+Alt+Shift+[ |
| editor.unfold_all | 展开全部 | ⇧⌥⌘] | Ctrl+Alt+Shift+] |

### 渲染后的 Markdown：`markdown.*` {#rendered-markdown-markdown}

由聚焦的渲染后 Markdown 视图运行；与 `editor.*` 一样只接受单个组合键。

| 动作 | 作用 | Apple | PC |
| --- | --- | --- | --- |
| markdown.bold | 加粗：包裹或取消包裹选区 | ⌘B | Ctrl+B |
| markdown.italic | 斜体 | ⌘I | Ctrl+I |
| markdown.strikethrough | 删除线 | ⇧⌘X | Ctrl+Shift+X |
| markdown.link | 链接卡片 | ⇧⌘K | Ctrl+Shift+K |
| markdown.move_block_up | 上移 block | ⌥↑ | Alt+↑ |
| markdown.move_block_down | 下移 block | ⌥↓ | Alt+↓ |
| markdown.duplicate_block | 复制 block（按 block 选择） | ⌘D | Ctrl+Shift+D, Ctrl+D |
| markdown.outdent | 提升列表项 / 退回上一个表格单元格 | ⇧Tab | Shift+Tab |
| markdown.hard_break | 插入硬换行 | ⇧⏎ | Shift+Enter |
| markdown.extend_blocks_up | 向上扩展 block 选区 | ⇧↑ | Shift+↑ |
| markdown.extend_blocks_down | 向下扩展 block 选区 | ⇧↓ | Shift+↓ |

### 浏览器 block：`browser.*` {#browser-blocks-browser}

在焦点位于浏览器 block、其页面或其地址栏时生效（在地址栏中输入时，Alt+← 与 Alt+→ 仍归地址栏）。在 Apple 键盘上，它们与 Safari 中一样，位于 ⌘[ 与 ⌘] 上 `previous_pane` 与 `next_pane` 之前，因此为侧键发送 ⌘[ / ⌘] 的鼠标工具在那里也能后退前进；在其他位置，⌘[ 与 ⌘] 仍然在 block 之间移动。绑定了 ⌘[ 或 ⌘] 的 `keymap` 预设（Ghostty 的、cmux 的）会让它们保持在前。无论键位映射如何设置，鼠标自带的后退与前进按钮都会翻动页面。

| 动作 | 作用 | Apple | PC |
| --- | --- | --- | --- |
| browser.back | 后退到上一页 | ⌘[ | Alt+← |
| browser.forward | 前进到下一页 | ⌘] | Alt+→ |

### Git：`git.*` {#git-git}

在焦点位于 git block 或 Files 面板的“改动”或“引用”标签页时生效；diff 相关键在 diff 中打开文件时生效。iOS 与 Web 版本不可用。

| 动作 | 作用 |
| --- | --- |
| git.find | 在打开的 diff 中查找，否则搜索提交图 |
| git.new_branch | 新建分支表单 |
| git.undo | 撤销最新一次操作（文本字段之外） |
| git.redo | 重做最新一次被撤销的操作（文本字段之外） |
| git.back | 在选区与已打开的 diff 之间后退（文本字段之外） |
| git.forward | 在选区与已打开的 diff 之间前进（文本字段之外） |
| git.next_commit | 选中下一个提交（未打开 diff） |
| git.previous_commit | 选中上一个提交（未打开 diff） |
| git.peek | 预览选中的提交，或关闭预览 |
| git.select_working_tree | 选中工作区（未打开 diff） |
| git.commit_message | 提交编辑器的摘要字段 |
| git.refresh | 重新读取仓库 |
| git.filter_refs | “引用”标签页的筛选 |
| git.next_hunk | 打开的 diff 中的下一个 hunk（整文件视图：下一处改动） |
| git.previous_hunk | 打开的 diff 中的上一个 hunk |
| git.next_file | 下一个改动的文件 |
| git.previous_file | 上一个改动的文件 |
| git.toggle_wrap | 长 diff 行自动换行 |
| git.cycle_whitespace | 空白：精确 → 忽略空白 → 忽略格式 |
| git.toggle_hunk_view | 每次只显示一个 hunk |
| git.expand_context | 在当前 hunk 上下各多显示 20 行未改动内容 |
| git.toggle_all_context | 显示打开的 diff 中所有未改动行，或再次折叠它们 |
| git.edit_file | 在 file block 中编辑打开的工作区文件 |
| git.stage | 暂存 / 取消暂存选中的行，否则（hunk 视图下）该 hunk，否则该文件 |
| git.discard_lines | 丢弃选中的行，否则（hunk 视图下）该 hunk（会先询问） |
| git.discard_file | 丢弃打开文件的未暂存改动（会先询问） |

### SQLite block：`sqlite.*` {#sqlite-blocks-sqlite}

在聚焦的 SQLite block 中运行；有一个获得焦点时会被列入命令面板。区域动作（`sqlite.structure.*`、`sqlite.browse.*`、`sqlite.execute.*`、`sqlite.pragmas.*`）在该区域显示时列出。block 级动作的默认键：⌘S `write`、⌘Z `undo`、⌥⌘1–⌥⌘4 对应四个区域，⌘E / ⌥⌘D / ⌘I 对应单元格、图表与 schema 工作表，⌘L `log`。

| 动作 | 标签 |
| --- | --- |
| sqlite.write | 写入改动 |
| sqlite.revert | 撤销改动… |
| sqlite.undo | 撤销上一次改动 |
| sqlite.area.structure | 显示数据库结构 |
| sqlite.area.browse | 浏览数据 |
| sqlite.area.execute | 执行 SQL |
| sqlite.area.pragmas | 编辑 pragma |
| sqlite.sheet.cell | 编辑单元格工作表 |
| sqlite.sheet.plot | 图表工作表 |
| sqlite.sheet.schema | Schema 工作表 |
| sqlite.log | SQL 日志 |
| sqlite.read_only | 以只读 / 可写方式重新打开 |
| sqlite.close | 关闭数据库 |
| sqlite.structure.refresh | 刷新结构 |
| sqlite.structure.browse | 浏览选中的表 |
| sqlite.structure.modify | 修改选中对象… |
| sqlite.structure.delete | 删除选中对象… |
| sqlite.structure.copy_create | 复制 create 语句 |
| sqlite.structure.copy_name | 复制名称 |
| sqlite.structure.copy_drop | 复制到 SQL 编辑器 |
| sqlite.structure.menu | 选中对象的菜单 |
| sqlite.structure.row_counts | 在结构中显示行数 |
| sqlite.structure.unfold_all | 展开所有对象 |
| sqlite.structure.fold_all | 折叠所有对象 |
| sqlite.browse.refresh | 刷新 |
| sqlite.browse.previous_table | 上一张表 |
| sqlite.browse.next_table | 下一张表 |
| sqlite.browse.new_tab | 新建数据浏览器 |
| sqlite.browse.rename_tab | 重命名数据浏览器… |
| sqlite.browse.close_tab | 关闭数据浏览器 |
| sqlite.browse.new_record | 新建记录 |
| sqlite.browse.insert_values | 插入值… |
| sqlite.browse.delete_records | 删除记录 |
| sqlite.browse.duplicate_record | 复制记录 |
| sqlite.browse.copy_above | 复制上方单元格 |
| sqlite.browse.set_null | 设为 NULL |
| sqlite.browse.clear_cells | 清空单元格 |
| sqlite.browse.delete | 删除记录或清空单元格 |
| sqlite.browse.cut | 剪切 |
| sqlite.browse.copy_headers | 连表头一起复制 |
| sqlite.browse.copy_sql | 复制为 SQL |
| sqlite.browse.select_all | 全选 |
| sqlite.browse.edit_cell | 编辑单元格… |
| sqlite.browse.find | 查找… |
| sqlite.browse.replace | 查找并替换… |
| sqlite.browse.find_next | 查找下一个 |
| sqlite.browse.find_previous | 查找上一个 |
| sqlite.browse.replace_next | 替换 |
| sqlite.browse.replace_all | 全部替换 |
| sqlite.browse.adjust_rows | 按内容调整行高 |
| sqlite.browse.first_page | 第一页 |
| sqlite.browse.previous_page | 上一页 |
| sqlite.browse.next_page | 下一页 |
| sqlite.browse.last_page | 最后一页 |
| sqlite.browse.goto_row | 转到行… |
| sqlite.browse.clear_filters | 清除筛选 |
| sqlite.browse.clear_sorting | 清除排序 |
| sqlite.browse.focus_filter | 筛选此列 |
| sqlite.browse.global_filter | 在任意列中筛选 |
| sqlite.browse.find_column | 查找列… |
| sqlite.browse.show_rowid | 显示 rowid 列 |
| sqlite.browse.freeze_columns | 冻结到此列为止 |
| sqlite.browse.hide_columns | 隐藏列 |
| sqlite.browse.show_all_columns | 显示所有列 |
| sqlite.browse.select_column | 选中列 |
| sqlite.browse.unlock_view | 解锁视图编辑… |
| sqlite.browse.display_format | 编辑显示格式… |
| sqlite.browse.encoding | 设置编码… |
| sqlite.browse.encoding_all | 为所有表设置编码… |
| sqlite.browse.copy_column_name | 复制列名 |
| sqlite.browse.cond_formats | 编辑条件格式… |
| sqlite.browse.format_toolbar | 格式工具栏 |
| sqlite.browse.bold | 加粗 |
| sqlite.browse.italic | 斜体 |
| sqlite.browse.underline | 下划线 |
| sqlite.browse.align_left | 左对齐 |
| sqlite.browse.align_center | 居中 |
| sqlite.browse.align_right | 右对齐 |
| sqlite.browse.align_justify | 两端对齐 |
| sqlite.browse.clear_format | 清除格式 |
| sqlite.browse.save_as_view | 将当前筛选保存为视图… |
| sqlite.browse.export_csv | 将筛选数据导出为 CSV… |
| sqlite.browse.export_json | 将筛选数据导出为 JSON… |
| sqlite.execute.execute | 执行全部 / 选中的 SQL |
| sqlite.execute.execute_line | 执行当前行 |
| sqlite.execute.stop | 停止执行 SQL |
| sqlite.execute.new_tab | 新建 SQL 标签页 |
| sqlite.execute.open_file | 打开 SQL 文件… |
| sqlite.execute.save_file | 保存 SQL 文件 |
| sqlite.execute.save_file_as | 将 SQL 文件另存为… |
| sqlite.execute.close_tab | 关闭 SQL 标签页 |
| sqlite.execute.rename_tab | 重命名 SQL 标签页… |
| sqlite.execute.duplicate_tab | 复制 SQL 标签页 |
| sqlite.execute.next_tab | 下一个 SQL 标签页 |
| sqlite.execute.previous_tab | 上一个 SQL 标签页 |
| sqlite.execute.focus_editor | 聚焦 SQL 编辑器 |
| sqlite.execute.focus_results | 聚焦 SQL 结果 |
| sqlite.execute.complete | 补全 SQL |
| sqlite.execute.zoom_in | 放大 SQL 编辑器 |
| sqlite.execute.zoom_out | 缩小 SQL 编辑器 |
| sqlite.execute.zoom_reset | 重置 SQL 编辑器缩放 |
| sqlite.execute.copy_with_headers | 连表头一起复制结果 |
| sqlite.execute.copy_as_sql | 将结果复制为 SQL |
| sqlite.execute.export_csv | 将结果导出为 CSV… |
| sqlite.execute.export_json | 将结果导出为 JSON… |
| sqlite.execute.save_as_view | 将结果保存为视图… |
| sqlite.execute.toggle_tiling | 结果与编辑器并排 |
| sqlite.pragmas.save | 保存 pragma |
| sqlite.pragmas.reset | 重置 pragma 编辑 |
| sqlite.pragmas.refresh | 重新加载 pragma |
| sqlite.cell.apply | 编辑单元格：应用 |
| sqlite.cell.discard | 编辑单元格：放弃编辑 |
| sqlite.cell.set_null | 编辑单元格：设为 NULL |
| sqlite.cell.import | 编辑单元格：从文件导入… |
| sqlite.cell.import_reference | 编辑单元格：保存文件引用… |
| sqlite.cell.export | 编辑单元格：导出到文件… |
| sqlite.cell.export_dump | 编辑单元格：导出十六进制转储… |
| sqlite.cell.open_external | 编辑单元格：在外部应用中打开 |
| sqlite.cell.open_default | 编辑单元格：用默认应用或浏览器打开 |
| sqlite.cell.copy_hex_ascii | 编辑单元格：复制十六进制与 ASCII |
| sqlite.cell.overwrite | 编辑单元格：覆盖模式 |
| sqlite.cell.word_wrap | 编辑单元格：自动换行 |
| sqlite.cell.auto_format | 编辑单元格：自动格式化 |
| sqlite.cell.sort_keys | 编辑单元格：排序键 |
| sqlite.cell.auto_switch | 编辑单元格：自动切换模式 |
| sqlite.cell.focus | 编辑单元格：聚焦编辑器 |
| sqlite.cell.mode.text | 编辑单元格：文本模式 |
| sqlite.cell.mode.rtl | 编辑单元格：从右至左文本模式 |
| sqlite.cell.mode.binary | 编辑单元格：二进制模式 |
| sqlite.cell.mode.image | 编辑单元格：图像模式 |
| sqlite.cell.mode.json | 编辑单元格：JSON 模式 |
| sqlite.cell.mode.xml | 编辑单元格：XML 模式 |
| sqlite.cell.mode.svg | 编辑单元格：SVG 模式 |
| sqlite.cell.mode.evaluation | 编辑单元格：求值模式 |
| sqlite.plot.copy | 图表：复制图像 |
| sqlite.plot.save | 图表：另存为 PNG、JPG 或 SVG… |
| sqlite.plot.load_all | 图表：加载所有数据 |
| sqlite.plot.reset | 图表：重置视图 |
| sqlite.plot.legend | 图表：显示图例 |
| sqlite.plot.stacked | 图表：堆叠条形 |
| sqlite.plot.fixed | 图表：固定数字格式 |
| sqlite.plot.log_x | 图表：对数刻度（X） |
| sqlite.plot.log_y | 图表：对数刻度（Y） |
| sqlite.dialogs.create_table | 创建表… |
| sqlite.dialogs.modify_table | 修改表… |
| sqlite.dialogs.create_index | 创建索引… |
| sqlite.dialogs.import_csv | 从 CSV 文件导入表… |
| sqlite.dialogs.import_csv_clipboard | 从剪贴板中的 CSV 数据导入表… |
| sqlite.dialogs.import_sql | 从 SQL 文件导入数据库… |
| sqlite.dialogs.export_csv | 将表导出为 CSV 文件… |
| sqlite.dialogs.export_json | 将表导出为 JSON… |
| sqlite.dialogs.export_sql | 将数据库导出为 SQL 文件… |
| sqlite.dialogs.set_null | 将值设为 NULL |
| sqlite.tools.compact | 压缩数据库… |
| sqlite.tools.integrity_check | 完整性检查 |
| sqlite.tools.quick_check | 快速完整性检查 |
| sqlite.tools.foreign_key_check | 外键检查 |
| sqlite.tools.optimize | 优化数据库 |
| sqlite.tools.row_counts | 在 SQL 标签页中显示行数 |
| sqlite.tools.load_extension | 加载扩展… |
| sqlite.tools.attach | 附加数据库… |
| sqlite.tools.detach | 分离数据库… |
| sqlite.tools.open_project | 打开项目… |
| sqlite.tools.save_project | 保存项目 |
| sqlite.tools.save_project_as | 将项目另存为… |
| sqlite.tools.save_all | 全部保存 |
| sqlite.tools.close_project | 关闭项目 |
| sqlite.tools.save_database_as | 将数据库另存为… |
| sqlite.tools.drop_select | Schema 删除语句：SELECT 语句 |
| sqlite.tools.drop_insert | Schema 删除语句：INSERT 语句 |
| sqlite.tools.drop_names | Schema 删除语句：仅名称 |
| sqlite.tools.drop_qualified | Schema 删除语句：限定名称 |
| sqlite.tools.drop_quoted | Schema 删除语句：带引号的名称 |
| sqlite.tools.recent_1 | 打开最近的数据库 1 |
| sqlite.tools.recent_2 | 打开最近的数据库 2 |
| sqlite.tools.recent_3 | 打开最近的数据库 3 |
| sqlite.tools.recent_4 | 打开最近的数据库 4 |
| sqlite.tools.recent_5 | 打开最近的数据库 5 |
| sqlite.tools.recent_6 | 打开最近的数据库 6 |
| sqlite.tools.recent_7 | 打开最近的数据库 7 |
| sqlite.tools.recent_8 | 打开最近的数据库 8 |
| sqlite.tools.recent_9 | 打开最近的数据库 9 |
| sqlite.tools.recent_flipped_1 | 以只读反转方式打开最近的数据库 1 |
| sqlite.tools.recent_flipped_2 | 以只读反转方式打开最近的数据库 2 |
| sqlite.tools.recent_flipped_3 | 以只读反转方式打开最近的数据库 3 |
| sqlite.tools.recent_flipped_4 | 以只读反转方式打开最近的数据库 4 |
| sqlite.tools.recent_flipped_5 | 以只读反转方式打开最近的数据库 5 |
| sqlite.tools.recent_flipped_6 | 以只读反转方式打开最近的数据库 6 |
| sqlite.tools.recent_flipped_7 | 以只读反转方式打开最近的数据库 7 |
| sqlite.tools.recent_flipped_8 | 以只读反转方式打开最近的数据库 8 |
| sqlite.tools.recent_flipped_9 | 以只读反转方式打开最近的数据库 9 |

### 笔记本 block：`notebook.*` {#notebook-blocks-notebook}

在聚焦的笔记本 block 中运行。

| 动作 | 标签 |
| --- | --- |
| notebook.edit | 编辑单元格 |
| notebook.command | 离开单元格编辑器 |
| notebook.run_select_below | 运行单元格并选中下一个 |
| notebook.run | 运行选中的单元格 |
| notebook.run_insert_below | 运行单元格并在下方插入 |
| notebook.run_all | 运行所有单元格 |
| notebook.run_above | 运行上方单元格 |
| notebook.run_below | 运行选中单元格及其下方 |
| notebook.insert_above | 在上方插入单元格 |
| notebook.insert_below | 在下方插入单元格 |
| notebook.cut | 剪切单元格 |
| notebook.copy | 复制单元格 |
| notebook.paste_below | 在下方粘贴单元格 |
| notebook.paste_above | 在上方粘贴单元格 |
| notebook.duplicate | 复制单元格 |
| notebook.delete | 删除单元格 |
| notebook.twice.delete | 删除单元格（按两次） |
| notebook.twice.interrupt | 中断内核（按两次） |
| notebook.twice.restart | 重启内核（按两次） |
| notebook.undo | 撤销单元格操作 |
| notebook.redo | 重做单元格操作 |
| notebook.to_code | 转换为代码 |
| notebook.to_markdown | 转换为 markdown |
| notebook.to_raw | 转换为 raw |
| notebook.heading.1 | 一级标题 |
| notebook.heading.2 | 二级标题 |
| notebook.heading.3 | 三级标题 |
| notebook.heading.4 | 四级标题 |
| notebook.heading.5 | 五级标题 |
| notebook.heading.6 | 六级标题 |
| notebook.select_above | 选中上方单元格 |
| notebook.select_below | 选中下方单元格 |
| notebook.extend_above | 向上扩展选区 |
| notebook.extend_below | 向下扩展选区 |
| notebook.select_all | 选中所有单元格 |
| notebook.move_up | 上移单元格 |
| notebook.move_down | 下移单元格 |
| notebook.merge | 合并选中的单元格 |
| notebook.merge_above | 与上方单元格合并 |
| notebook.merge_below | 与下方单元格合并 |
| notebook.split | 拆分单元格 |
| notebook.collapse_input | 折叠输入 |
| notebook.collapse_output | 折叠输出 |
| notebook.scroll_output | 滚动输出 |
| notebook.line_numbers | 行号 |
| notebook.all_line_numbers | 所有单元格的行号 |
| notebook.clear_output | 清除单元格输出 |
| notebook.clear_all | 清除所有输出 |
| notebook.interrupt | 中断内核 |
| notebook.restart | 重启内核… |
| notebook.restart_clear | 重启内核并清除输出… |
| notebook.restart_run_all | 重启内核并运行全部… |
| notebook.shutdown | 关闭内核 |
| notebook.interpreter | 更换解释器… |
| notebook.save | 保存笔记本 |
| notebook.save_key | 保存笔记本（命令模式） |
| notebook.save_as | 将笔记本另存为… |
| notebook.rename | 重命名笔记本… |
| notebook.revert_checkpoint | 将笔记本恢复到检查点… |
| notebook.reload | 从磁盘重新加载笔记本 |
| notebook.export_python | 将笔记本导出为 Python… |
| notebook.export_markdown | 将笔记本导出为 Markdown… |
| notebook.export_html | 将笔记本导出为 HTML… |
| notebook.scroll_down | 向下滚动笔记本 |
| notebook.scroll_up | 向上滚动笔记本 |
| notebook.zoom_in | 放大笔记本 |
| notebook.zoom_out | 缩小笔记本 |
| notebook.zoom_reset | 重置笔记本缩放 |
| notebook.sheet.contents | 目录 |
| notebook.sheet.properties | 单元格属性 |
| notebook.sheet.variables | 变量 |
| notebook.sheet.help | 上下文帮助 |
| notebook.shortcuts | 笔记本键盘快捷键 |
| notebook.find_replace | 在笔记本中查找并替换 |
| notebook.apply_metadata | 应用元数据 |
| notebook.complete | 补全 |
| notebook.inspect | 显示检查提示 |

### 看板 block：`board.*` {#board-blocks-board}

在聚焦的看板 block 中运行，位于其文本字段之外。

| 动作 | 标签 |
| --- | --- |
| board.up | 选中上方卡片 |
| board.down | 选中下方卡片 |
| board.left | 选中上一条泳道中的卡片 |
| board.right | 选中下一条泳道中的卡片 |
| board.first | 选中第一张卡片 |
| board.last | 选中最后一张卡片 |
| board.move_up | 上移卡片 |
| board.move_down | 下移卡片 |
| board.move_left | 把卡片移到上一条泳道 |
| board.move_right | 把卡片移到下一条泳道 |
| board.toggle | 标记完成或打开 |
| board.edit | 编辑卡片标题 |
| board.new_below | 在下方新建卡片 |
| board.new_above | 在上方新建卡片 |
| board.delete | 删除卡片 |
| board.undo | 撤销看板改动 |
| board.redo | 重做看板改动 |
| board.details | 卡片详情 |
| board.filter | 筛选卡片 |
| board.switch_view | 切换看板 / 列表视图 |
| board.hide_done | 隐藏已完成卡片 |
| board.clear | 清除选择 |
| board.new_lane | 新建泳道 |
| board.rename_lane | 重命名泳道… |
| board.move_lane_left | 左移泳道 |
| board.move_lane_right | 右移泳道 |
| board.delete_lane | 删除泳道 |
| board.done_lane | 完成泳道 |
| board.open_markdown | 以 Markdown 打开 |

### 画布 block：`canvas.*` {#canvas-blocks-canvas}

在画布持有按键时于聚焦的画布 block 中运行，位于其文本编辑器之外。撤销与重做仅在确实有可撤销或可重做的内容时生效，复制与剪切仅在存在选区时生效。

| 动作 | 标签 |
| --- | --- |
| canvas.tool_select | 选择工具 |
| canvas.tool_lasso | 套索工具 |
| canvas.tool_hand | 抓手工具 |
| canvas.tool_draw | 绘制工具 |
| canvas.tool_highlight | 荧光笔 |
| canvas.tool_eraser | 橡皮擦 |
| canvas.tool_laser | 激光笔 |
| canvas.tool_arrow | 箭头 |
| canvas.tool_line | 直线 |
| canvas.tool_rect | 矩形 |
| canvas.tool_ellipse | 椭圆 |
| canvas.tool_diamond | 菱形 |
| canvas.tool_triangle | 三角形 |
| canvas.tool_hexagon | 六边形 |
| canvas.tool_parallelogram | 平行四边形 |
| canvas.tool_star | 星形 |
| canvas.tool_cylinder | 圆柱体 |
| canvas.tool_pill | 胶囊形 |
| canvas.tool_bracket | 方括号 |
| canvas.tool_brace | 花括号 |
| canvas.tool_polygon | 多边形 |
| canvas.tool_curve | 曲线 |
| canvas.tool_text | 文本工具 |
| canvas.toggle_tool_lock | 保持工具选中 |
| canvas.undo | 撤销 |
| canvas.redo | 重做 |
| canvas.cut | 剪切 |
| canvas.copy | 复制 |
| canvas.paste | 粘贴 |
| canvas.delete | 删除 |
| canvas.duplicate | 复制 |
| canvas.select_all | 全选 |
| canvas.deselect | 取消选择 |
| canvas.group | 编组 |
| canvas.ungroup | 取消编组 |
| canvas.toggle_lock | 锁定 |
| canvas.copy_style | 复制样式 |
| canvas.paste_style | 粘贴样式 |
| canvas.bring_to_front | 移到最前 |
| canvas.bring_forward | 前移一层 |
| canvas.send_backward | 后移一层 |
| canvas.send_to_back | 移到最后 |
| canvas.align_left | 左对齐 |
| canvas.align_center | 居中对齐 |
| canvas.align_right | 右对齐 |
| canvas.align_top | 顶部对齐 |
| canvas.align_middle | 垂直居中对齐 |
| canvas.align_bottom | 底部对齐 |
| canvas.distribute_horizontally | 水平分布 |
| canvas.distribute_vertically | 垂直分布 |
| canvas.flip_horizontally | 水平翻转 |
| canvas.flip_vertically | 垂直翻转 |
| canvas.edit_text | 编辑文本 |
| canvas.crop | 裁剪 |
| canvas.reset_crop | 重置裁剪 |
| canvas.insert_image | 插入图像… |
| canvas.zoom_in | 放大 |
| canvas.zoom_out | 缩小 |
| canvas.zoom_to_fit | 缩放到适合 |
| canvas.zoom_to_selection | 缩放到选区 |
| canvas.zoom_reset | 缩放到 100% |
| canvas.look_clean | Clean 外观 |
| canvas.look_mono | Mono 外观 |
| canvas.look_sketch | 手绘外观 |
| canvas.paper_dots | 点阵纸 |
| canvas.paper_grid | 网格纸 |
| canvas.paper_lines | 横线纸 |
| canvas.paper_none | 空白纸 |
| canvas.fill_none | 无填充 |
| canvas.fill_semi | 半透明填充 |
| canvas.fill_solid | 实心填充 |
| canvas.fill_pattern | 图案填充 |

## 插件动作 {#plugin-actions}

插件 `hello` 中 id 为 `say_hi` 的 window 插件命令 [`tern.command`](api-window.md#terncommand) 会成为动作 `plugin.hello.say_hi`。命令面板按其 `title` 显示，并归入其 `group`（默认：插件的名称）。该动作名称可以由任何插件用 `tern.bind` 绑定，也可以写在 `settings.json` 的 `keybinds` 中，还可以由状态分段的 `command` 指名。它不是内置命令，因此 `tern.override` 与 `cx:command` 会拒绝它。

传给 `tern.bind` 的函数会得到动作名称 `plugin.<plugin>.bind.<n>`，其中 `n` 从 0 起计该插件的函数绑定。这也是 `bind` 不能用作命令 id 的原因。

任何 `plugin.<a>.<b>`，只要两部分都非空就能解析，无论该插件是否存在。当某个键运行其中之一时，Tern 查找已加载的插件 `<a>` 及其命令 `<b>`（或函数绑定 `<n>`）；若没有，则不会运行任何东西。

```lua
tern.command({
	id = "say_hi",
	title = "Say hi",
	run = function(cx)
		cx:toast("info", "hi")
	end,
})
tern.bind("ctrl+alt+shift+h", "plugin." .. tern.plugin.id .. ".say_hi")
```

完整示例参见[命令、按键与覆盖](../guides/commands.md)。

## 组合键 {#chords}

`tern.bind` 的组合键写法与 `settings.json` 的 `keybinds` 相同：

- 用 `+` 连接的修饰键 `ctrl`、`alt`（或 `opt`）、`shift`、`cmd`（或 `super`），最后是一个按键。
- 按键是按键盘布局打出的字符（`ctrl+shift+2`、`cmd+plus`）、具名按键、`f1`–`f20`，或物理按键（`cmd+digit_1`、`ctrl+key_a`、`alt+bracket_left`）。
- 序列用 `>` 连接多个组合键：`ctrl+a>c` 表示先 ⌃A、再 C。最后一个之前的组合键构成前缀。
- 单独的修饰键（`cmd`、`shift` 等）表示轻敲该键：只按下并松开，不伴随其他键。轻敲只能组成纯粹的轻敲序列，每次都在上一次之后半秒内：`shift>shift` 表示连按 Shift 两次（Tern 把 `cmd>cmd`，即连按 ⌘ 两次，绑定到 `carly`）。其他任何按键或一次点击都会结束该序列。
- 在 Windows 与 Linux 上（以及设置了 `swap_ctrl_cmd` 的 macOS 上），`ctrl` 是 Ctrl 键，`cmd`/`super` 是 Windows 键或 Super 键。

插件绑定位于 Tern 的默认键与键盘预设之上、用户的 `keybinds` 之下。插件只能新增按键：绑定到默认键或预设已绑定的按键，或与它们的某个序列相衔接（作为其开头或以其为开头）的绑定会被略过。

## 错误 {#errors}

| 调用 | 错误输入 | 结果 |
| --- | --- | --- |
| `tern.override(id, fn)` | `id` 不是命令 id | 抛出 ``tern.override: unknown command `<id>` `` |
| `cx:command(id)` | `id` 不是命令 id | 抛出 ``unknown command `<id>` `` |
| `tern.command(def)` | `id` 不是字母、数字、`_`、`-` 或 `bind` | 抛出 ``tern.command: bad id `<id>` (letters, digits, `_` and `-`; not `bind`)`` |
| `tern.bind(chord, action)` | `action` 既不是字符串也不是函数 | 抛出 `tern.bind: the action is a name or a function` |
| `tern.bind(chord, action)` | 无法解析的组合键或动作名称 | 调用时不报错。重建键位映射时该绑定被略过，日志中出现警告 `plugin bind left out` 及解析错误（对名称而言为 ``unknown action `<name>` ``） |
| `tern.bind(chord, action)` | 默认键或预设已绑定的按键 | 略过；日志警告 `plugin bind left out: the preset binds these keys` |

`tern.bind` 不检查 `plugin.*` 动作是否存在；未知的动作名称仍会解析，按下时不做任何事。
