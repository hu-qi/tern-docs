# API 参考 {#api-reference}

`tern` 模块就是插件 API 的全部。插件的每个半区各自持有一份副本：共享成员在两边都存在，每个上下文再补充自己的成员。本页按上下文为模块建立索引，并规定三个成员页面所用的记号约定。

## 获取模块 {#getting-the-module}

模块在入口文件运行之前就已作为全局 `tern` 安装，`require("tern")` 返回同一个表。全局 `print` 即 `tern.log.info`。

```lua
print(tern.context, tern.plugin.id, tern.runtime.jit)
```

以任何其他字符串调用 `require`，都会加载相对于调用文件而言的 Luau 模块（`require("./util")` 会查找 `util.luau`、`util.lua` 或 `util/init.luau`），并且绝不会离开插件目录；`.luaurc` 别名不会被读取。参见 [运行时、预算与 JIT](../concepts/runtime.md)。

## 供 luau-lsp 使用的类型 {#types-for-luau-lsp}

`tern plugin types DIR` 会写出 `DIR/tern.d.luau`，即运行时随附的定义文件。把它注册为 luau-lsp 的定义文件后，两个入口都会依据所声明的全局 `tern` 进行类型检查：

```sh
tern plugin types ~/src/my-plugin
```

```json
{
  "luau-lsp.platform.type": "standard",
  "luau-lsp.sourcemap.enabled": false,
  "luau-lsp.types.definitionFiles": { "@tern": "tern.d.luau" }
}
```

luau-lsp 不会解析 `require("tern")`（它会报告未知的 require）；在做类型检查的代码中请使用全局 `tern`。把定义标注为 `BlockDef<MyState>` 或 `LensDef<MyState>`，以便为其状态指定类型。定义文件会在文档中把某个上下文的成员标记为 `Host only` 或 `Window only`；它为两个入口声明同一个 `tern`，因此检查器不会阻止 window 入口调用 host 成员。

## 上下文 {#contexts}

`tern.context` 在运行 `host.luau` 的 VM 中为 `"host"`，在运行 `window.luau` 的 VM 中为 `"window"`。另一上下文的成员不存在（`nil`）：使用它会引发 Luau 自身的错误（在 window 入口中对 `tern.block.define` 会报 `attempt to index nil with 'define'`，在 host 入口中对 `tern.command` 会报 `attempt to call a nil value`）。当一个模块同时服务两个入口时，请按 `tern.context` 分支处理。

| 成员 | Host | Window | 页面 |
| --- | --- | --- | --- |
| `tern.context`, `tern.plugin`, `tern.runtime` | 是 | 是 | [共享](api-shared.md#identity) |
| `tern.log`, `tern.json`, `tern.now`, `tern.getenv`, `tern.timer` | 是 | 是 | [共享](api-shared.md) |
| `tern.base64` | 是 | 是 | [共享](api-shared.md#base64) |
| `tern.kv`, `tern.fs`, `tern.process` | 是 | 是 | [共享](api-shared.md#storage) |
| `tern.secrets` | 否 | 是 | [Window](api-window.md#ternsecrets) |
| `tern.fetch` | 是 | 是 | [共享](api-shared.md#network) |
| `tern.ui`, `tern.parse` | 是 | 是 | [UI 构造器](ui.md) |
| `tern.block.define` | 是 | 否 | [Host](api-host.md#ternblockdefine) |
| `tern.lens.define` | 是 | 否 | [Host](api-host.md#ternlensdefine) |
| `tern.pane.write`, `tern.pane.list` | 是 | 否 | [Host](api-host.md#ternpane) |
| `tern.on` | host 事件 | window 事件 | [Host](api-host.md#ternon)、[Window](api-window.md#ternon)、[事件](events.md) |
| `tern.command`, `tern.bind`, `tern.override` | 否 | 是 | [Window](api-window.md) |
| `tern.route.open`, `tern.route.link` | 否 | 是 | [Window](api-window.md#ternrouteopen) |
| `tern.chrome.tab_title`, `window_title`, `status` | 否 | 是 | [Window](api-window.md#chrome-formatters) |
| `tern.chrome.refresh` | 否 | 是 | [Window](api-window.md#ternchromerefresh) |
| `tern.chrome.program_icon` | 否 | 是 | [Window](api-window.md#ternchromeprogram_icon) |
| `tern.files.button` | 否 | 是 | [Window](api-window.md#ternfilesbutton) |
| `tern.css` | 否 | 是 | [Window](api-window.md#terncss) |

`tern.on` 在两个上下文中都存在，但事件集合不同；上下文不认识的事件名会在调用处引发错误。

处理程序上下文 `cx` 因调用者不同而不同：

| `cx` | 接收方 | 成员 | 页面 |
| --- | --- | --- | --- |
| Effect cx | lens 的 `open` 与 `event`、host 事件处理程序 | `toast`、`open`、`copy` | [Host](api-host.md#effect-cx) |
| Block cx | 所有 block 处理程序 | Effect cx，外加 `pane`、`cwd`、`cols`、`rows`、`render`、`save`、`exit`、`frame`、`blob` | [Host](api-host.md#block-cx) |
| Window cx | 命令、快捷键绑定、覆盖、路由、Files 面板按钮、窗口事件、窗口计时器、process 与 fetch 回调 | `session`、`layout`、`run`、`open`、`new_block`、`command`、`toast`、`copy` | [Window](api-window.md#window-cx) |

chrome 格式化器不接收 `cx`。host 的计时器、process 与 fetch 回调也不接收。

## 记号约定 {#notation}

- 函数签名使用 `tern.d.luau` 声明时的 Luau 类型语法。`T?` 表示可选值（`T` 或 `nil`）；写作 `name: T?` 的字段可以缺省。
- 写作 `cx:name(...)` 的方法使用 `:` 调用。
- **引发（Raises）** 指该调用抛出带有相应文本的 Lua 错误；调用它的处理程序会失败，除非用 `pcall` 捕获该错误。
- 失败或超出预算的处理程序会以提示条“插件 *name*：*hook* 失败”的形式报告，并写入日志；各页给出的钩子名就是其中出现的名称。参见[错误](errors.md#handler-failures)。
- 字节偏移、行与列均从 1 开始计数。时间单位为毫秒。
- 面板与标签页 id 是 Lua number。请原样传回；远程 id 的打包方式参见 [Window API](api-window.md#pane-and-tab-ids)。

## 声明与运行时的差异 {#where-the-declarations-and-the-runtime-differ}

运行时为准。在 `tern.d.luau` 声明得更窄或不同之处，成员页面会在注释中说明：

- 对于没有面板的链接（系统交给 Tern 的 URL），`LinkRequest.pane` 为 `nil`；声明中写作 `number`。
- `cx.layout:move` 与 `cx.layout:resize` 返回布尔值（是否发生了移动）；声明中不返回任何值。
- `LensDef.finish` 总是接收一个数字；声明允许 `nil`。
- block 的 `cx:exit` 接受一个可选的退出码（默认为 `0`）。
- `tern.ui.badge` 接受缺省的 `tone`。
- host 的 `cx:toast` 接受任意级别字符串；参见 [Effect cx](api-host.md#effect-cx)。
- window 上下文还会投递 `title` 事件，而声明中 `tern.on` 的列表遗漏了它。
- `tern.css` 安装样式表 `plugin:local:<plugin>:<name>`。

## 页面 {#pages}

- [共享 API](api-shared.md)：标识、日志、JSON、时间、计时器、键值存储、文件、进程、HTTP 请求。
- [Host API](api-host.md)：block、lens、host 事件、面板，以及它们各自的 `cx` 类型。
- [Window API](api-window.md)：命令、快捷键绑定、覆盖、路由、chrome、CSS、窗口事件，以及带有 `cx.session` 与 `cx.layout` 的窗口 `cx`。
- [UI 构造器](ui.md)：每个 `tern.ui` 构造器与 `tern.parse` 辅助函数。
- [事件](events.md)：每个 `tern.on` 事件及其负载。
