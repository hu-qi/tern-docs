# 术语表 {#glossary}

本组页面使用的术语，按英文名称的字母顺序排列。每条给出该术语在插件 SDK 中的含义，并链接到深入讲解它的位置。

| 术语 | 含义 | 参见 |
| --- | --- | --- |
| 动作 | 键位映射可以运行的一个名字：内置命令 id（`new_tab`）、仅存在于键位映射的动作（`palette`、`goto_tab:3`）、视图组合键（`editor.toggle_comment`），或插件动作（`plugin.<plugin>.<id>`）。`tern.bind` 把组合键绑定到动作；状态段在点击时运行其中一个 | [内置动作](actions.md) |
| `available` | 窗口命令的可选判定函数，命令面板每次列出各行时都会调用；返回假值即隐藏该行。预算 4 ms | [Window API](api-window.md#terncommand) |
| block | 程序为 Lua 的面板：由插件的 host 半区定义的 block 类型，由命令面板、“Open with”、路由决策、`cx:new_block` 或工作区启动。它像 shell 一样存在于守护进程的面板表中，并通过 Surface 协议绘制 | [block](../guides/blocks.md)、[Host API](api-host.md#ternblockdefine) |
| Block cx | 每个 block 处理函数都会收到的 `cx`：效果，外加 `pane`、`cwd`、`cols`、`rows`、`render`、`save`、`exit`、`frame`、`blob` | [Host API](api-host.md#block-cx) |
| block 类型 | 一条 `[[blocks]]` 声明及其 `tern.block.define` 实现 | [清单参考](manifest.md#blocks) |
| 预算 | 单次调用进入 Lua 的时间上限：host 上为 2 s，window 中为 50 ms，chrome 格式化器与 `available` 为 4 ms。超出上限的调用失败，其钩子暂停 | [运行时、预算与 JIT](../concepts/runtime.md#budgets) |
| catalog | host 的插件所提供的内容，以数据形式给出：每个插件的 id、名称、版本、状态、block 类型、lens 规则与拼接后的样式，以及该文件夹的问题。host 把它发送给每个窗口、iOS 与 Web 标签页，使它们无需运行 Lua 就能列出 block 类型并做出 lens 认领 | [架构](../concepts/architecture.md#the-catalog) |
| 组合键 | `tern.bind` 与 `keys` 所书写的按键组合（`cmd+shift+h`），或这样的组合构成的序列（`ctrl+a>c`） | [内置动作](actions.md#chords) |
| Chrome | 面板周围的窗口外壳：标签标题、窗口标题、状态行。插件用格式化器与 CSS 塑造它 | [Chrome 与样式](../guides/chrome.md) |
| 认领 | lens 接管一条命令行的决定，仅由清单的 `match` glob 做出：按 id 顺序第一个 Ready 的插件，再取该插件清单顺序中第一个 glob 匹配 `program args…` 的 lens。认领是声明式的，因此每个副本都得出相同的决定 | [清单参考](manifest.md#match-patterns) |
| 命令 | 命令面板中的一行。内置命令有 id（`split_right`）；插件用 `tern.command` 注册自己的命令，命名为 `plugin.<plugin>.<id>` | [Window API](api-window.md#terncommand)、[内置动作](actions.md#commands) |
| 上下文 | VM 运行在哪个半区：`tern.context` 为 `"host"` 或 `"window"`。每个上下文有自己的成员 | [API 参考](api.md#contexts) |
| cx | 传给处理函数的处理上下文对象：依调用方不同，是效果 cx、block cx 或 window cx。window 的 `cx` 仅在收到它的那次调用期间有效 | [API 参考](api.md#contexts) |
| 守护进程 | 会话守护进程：拥有面板、并为本机运行各 host 半区的每用户进程。窗口附着到它 | [架构](../concepts/architecture.md#where-each-half-runs) |
| 数据文件夹 | `<state>/plugin-data/<id>/`，由插件的两个半区共享：`tern.plugin.data`、`TERN_PLUGIN_DATA`、`kv.json` 的所在目录 | [包与清单](../concepts/packages.md#the-data-folder) |
| 决策 | `tern.route.open` 或 `tern.route.link` 处理函数为接管一次打开或一个链接而返回的内容：`{block = kind, args?}`、`{url = …}`、`{path = …, how?}` 或 `{handled = true}`；`nil` 表示拒绝 | [Window API](api-window.md#route-decisions) |
| Disabled | 一种插件状态：被 `plugins` 或 `plugins_disabled` 设置关闭。它不加载任何内容，也不认领任何内容 | [包与清单](../concepts/packages.md#problems-and-statuses) |
| dock、layer、main | block 视图的三个区域：`main` 是 block 的区域，`dock` 是其下方的条带，`layer` 是其上方的那层 | [Host API](api-host.md#view-model) |
| 效果 | host Lua 向显示某个面板的窗口发出的请求：toast、打开或复制到剪贴板。效果以数据形式从 host 传到窗口 | [Host API](api-host.md#effect-cx) |
| Effect cx | lens 的 `open` 与 `event` 以及 host 事件处理函数的 `cx`；它只有 `toast`、`open` 与 `copy` | [Host API](api-host.md#effect-cx) |
| 入口 | 上下文在加载时运行的 Luau 文件：清单中的 `host` 或 `window` | [清单参考](manifest.md#host-window) |
| 事件 | `tern.on` 订阅的通知。host 事件（`command_finished`、`pane_exited`、…）与 window 事件（`focus`、`tab_created`、…）是两套独立的集合 | [事件](events.md) |
| Failed | 一种插件状态：其入口在加载时抛出错误或超出预算，或留下了未定义的已声明 block 或 lens | [错误](errors.md#load-failures) |
| 格式化器 | 计算 chrome 文本的纯 window 函数：`tern.chrome.tab_title`、`window_title` 或 `status`。它收到一个小输入表，没有 `cx`，预算为 4 ms，结果按输入缓存，直到 `tern.chrome.refresh()` 或一次重载 | [Window API](api-window.md#chrome-formatters) |
| 帧 | block 发送的一批 Surface 协议操作：两个视图之间的差异，或来自 `cx:frame` 的原始操作。超过 64 KiB 的帧会被分块 | [Host API](api-host.md#view-model) |
| glob | 包含 `*`（任意长度）与 `?`（单个字符）的模式。lens 的 `match` glob 对命令区分大小写；block 的 `files` glob 对文件名忽略 ASCII 大小写 | [清单参考](manifest.md#match-patterns) |
| 半区 | 插件两个部分之一：host 半区（`host.luau`）与 window 半区（`window.luau`）。它们通常运行在不同进程中，往往位于不同机器上；在同一台机器上时，它们只共享数据文件夹 | [架构](../concepts/architecture.md#the-two-halves) |
| 钩子 | 一次进入 Lua 的调用所使用的名字（`pods.view`、`command <id>`、`focus`、`timer`）。它出现在失败 toast 中，也是预算超限后被禁用的单元 | [运行时、预算与 JIT](../concepts/runtime.md#a-tripped-budget) |
| host | 运行 Tern 面板的机器：本机，或窗口所附着的远程 host。每个 host 为自己的面板运行其已安装插件的 host 半区 | [架构](../concepts/architecture.md#where-each-half-runs) |
| host 半区 | 插件中位于 `host.luau` 的部分：block 类型、lens、host 事件、spawn 过滤器、`tern.pane`。它运行在运行面板的 host 上的工作线程中 | [Host API](api-host.md) |
| How | 文件或 block 的打开位置：`default`、`beside`（或 `split`）、`below`、`tab`、`replace`、`over` 或 `preview` | [Window API](api-window.md#route-decisions) |
| kind | block 类型的全名，`<plugin>.<block>`（`k8s.pods`）。路由决策、`cx:new_block` 与 `launch.block` 接受它 | [包与清单](../concepts/packages.md#ids-and-names) |
| 启动 | 描述新面板运行内容的表：`cwd`、`command`，或带 `args` 的 `block` | [Window API](api-window.md#launch) |
| lens | 插件对某条命令输出的原生视图。清单的 glob 认领该命令；host 半区的 `open`、`line`、`finish` 与 `view` 把捕获到的行变成视图，显示在 lens block 中 | [命令 lens](../guides/lenses.md)、[Host API](api-host.md#ternlensdefine) |
| lens block | shell 面板中承载已认领命令的原始输出、并显示其 lens 视图的 block；Raw 显示输出本身 | [架构](../concepts/architecture.md#lenses-declarative-claims-views-out-of-band) |
| lens id | `plugin.<plugin>.<lens>`；lens block 的角色是 `lens.` 加上它 | [包与清单](../concepts/packages.md#ids-and-names) |
| lens 状态 | lens 的 `open` 返回的值，由工作线程为每个插件保留最近 256 次捕获，并通过状态重建重新构建 | [Host API](api-host.md#lens-state-and-rehydration) |
| 链接 | 插件文件夹中的 `<name>.path` 文件，指向位于别处的某个包目录；`tern plugin link` 写入它。也指在面板中点击的超链接，`tern.route.link` 可以接管它 | [命令行](cli.md#tern-plugin-link) |
| 清单 | `plugin.toml`，schema 1 | [清单参考](manifest.md) |
| 节点 | 视图中的一个元素：`{k = kind, p = props, c = children}`，用 `tern.ui` 构建 | [UI 构建器](ui.md#nodes-and-spans) |
| 覆盖 | 在内置命令之前运行的 window 处理函数（`tern.override`）；返回真值即跳过内置命令 | [Window API](api-window.md#ternoverride) |
| 包 | 包含 `plugin.toml`、其入口、样式与模块的目录 | [包与清单](../concepts/packages.md) |
| 暂停的钩子 | 调用超出预算的钩子：该 VM 中此后对它的调用会被跳过 5 s，重复超限则更久（最多 5 min），或直到一次重载 | [运行时、预算与 JIT](../concepts/runtime.md#a-tripped-budget) |
| 插件顺序 | 按插件 id 的顺序，同一插件内按注册顺序。插件轮流参与的一切（覆盖、路由、格式化器、spawn 过滤器、认领、window 事件）都按此顺序进行 | [生命周期与重载](../concepts/lifecycle.md#loading) |
| 插件文件夹 | `<config>/plugins/`（`tern plugin dir`），或 iOS 上 Files 应用中的 Tern › Plugins | [包与清单](../concepts/packages.md#the-plugins-folder) |
| 问题 | 插件文件夹中不能成为可用插件的条目，并附原因 | [错误](errors.md#plugins-folder-problems) |
| Ready | 一种插件状态：已加载并运行中 | [包与清单](../concepts/packages.md#problems-and-statuses) |
| 区域 | 参见 dock、layer、main | |
| 状态重建 | 在工作线程丢失状态后（重载、守护进程重启、被逐出）重建 lens block 的状态：host 在处理该 block 的事件之前，把该 block 保存的命令与原始输出重新通过 `open`、`line` 与 `finish` 播放一遍 | [生命周期与重载](../concepts/lifecycle.md#lens-rehydration) |
| 重载 | 丢弃某个上下文的 VM 并重新加载所有插件，发生在插件文件夹发生变化、执行 `tern plugin reload` 或改动偏好设置之后。运行中的 block 从它们最后一次 `save` 的状态重启 | [生命周期与重载](../concepts/lifecycle.md#reloading) |
| 副本 | 面板屏幕的一个副本：守护进程的、每个已附着窗口的、iOS 的、Web 标签页的。只有 host 运行 Lua；副本从 catalog 获知认领，从 host 获知视图 | [架构](../concepts/architecture.md#lenses-declarative-claims-views-out-of-band) |
| 角色 | 节点或 block 为 CSS 暴露的字符串：节点的 `role` 属性变成 `data-role`；lens block 的角色是 `lens.plugin.<plugin>.<lens>`；插件 block 的 surface 带有 `data-surface="plugin.<plugin>.<block>"` | [Chrome 与样式](../guides/chrome.md) |
| 路由 | 在 Tern 打开文件（`tern.route.open`）或打开被点击的链接（`tern.route.link`）之前被咨询的 window 处理函数；第一个决策胜出 | [路由打开与链接](../guides/routing.md) |
| 段 | `tern.chrome.status` 格式化器添加到状态行的一项：文本、可选图标、色调与点击动作 | [Window API](api-window.md#ternchromestatus) |
| 会话 | 窗口中一组具名的标签页，由 `cx.session` 读取；一个窗口可以容纳多个 | [布局与工作区](../guides/layout.md) |
| 样式表 | 窗口级联中的全局样式表：插件的清单样式（`plugin:local:<id>:styles`）、`tern.css` 样式表（`plugin:local:<id>:<name>`），或远程 host 的插件样式（`plugin:<host>:<id>:styles`） | [Chrome 与样式](../guides/chrome.md) |
| span | 节点中一段带样式的文本：`{t = text, s = style?}` | [UI 构建器](ui.md#spans) |
| spawn 过滤器 | host 的 `spawn` 事件：一个同步处理函数，可以在每个进程面板启动之前改写其程序、参数、目录与环境；每个插件的等待上限为 50 ms | [事件](events.md#the-spawn-filter) |
| 状态 | block 由 `init` 返回、传给每个处理函数、并通过 `save` 持久化的值；或 lens 捕获中由 `open` 返回的值 | [Host API](api-host.md#blockdef) |
| 状态值 | Ready、Disabled 或 Failed；每个半区各自维护 | [生命周期与重载](../concepts/lifecycle.md#the-catalog-and-statuses) |
| Surface | 面板屏幕中结构化视图的那一层，block 与 lens block 绘制于其中，基于 Surface 协议 | [构建视图](../guides/views.md) |
| 色调 | span、徽标、行与段的语义颜色名：`accent`、`success`、`warning`、`error`、`info`、`muted`、… | [UI 构建器](ui.md#nodes-and-spans) |
| 视图 | block 的 `view` 或 lens 的 `view` 返回的内容：block 是若干区域的节点，lens 是一个节点 | [构建视图](../guides/views.md) |
| VM | 一个 Luau 虚拟机：每个 host 上每个插件一个（在其工作线程中），每个窗口中每个插件一个。沙箱化，256 MiB，受预算限制。除数据文件夹外，VM 之间不共享任何内容 | [运行时、预算与 JIT](../concepts/runtime.md#the-vm) |
| Window cx | 命令、绑定、覆盖、路由、window 事件、window 定时器、进程与 fetch 回调的 `cx`：`session`、`layout`、`run`、`open`、`new_block`、`command`、`toast`、`copy` | [Window API](api-window.md#window-cx) |
| window 半区 | 插件中位于 `window.luau` 的部分，在每个 Tern 窗口的 UI 线程上运行：命令、绑定、覆盖、路由、格式化器、CSS、window 事件、布局 | [Window API](api-window.md) |
| 窗口键 | 命名窗口中各会话、在守护进程中所用的键：第一个窗口为 `""`，其他窗口为 `"2"`、`"3"`、…。面板与 window 半区的进程以 `$TERN_WINDOW_KEY` 看到它，window 处理函数用 `cx:window_key()` 读取它，`tern inspect` 为每个客户端在其 `conn` 旁列出它，`tern` 命令用 `--window` 选择其中一个（第一个窗口用 `--window ""`）。host 效果会发给带有该面板窗口键的每个窗口 | [命令行](cli.md#common-behavior) |
| 工作线程 | host 上运行某个插件 host 半区的线程，拥有独立的 VM。工作线程并行运行；每个线程一次处理其插件的请求、事件与回调 | [架构](../concepts/architecture.md#host-workers) |
| 工作区 | window 半区用 `cx.layout` 构建的标签页布局，通常由 `window_start` 触发 | [布局与工作区](../guides/layout.md#workspaces) |
