# 清单参考 {#manifest-reference}

`plugin.toml` 声明一个包：它的标识、条目、样式表，以及其 host 半区定义的 block 类型与命令 lens。host 的每个副本都会从目录中获知这些声明，而不运行任何 Lua，因此清单决定了插件认领哪些命令，以及命令面板提供哪些 block 类型。

本页列出每个键及其类型、默认值和校验规则，以及每条规则失败时的确切文本。相关概念参见[包与清单](../concepts/packages.md)。

## 示例 {#example}

```toml
schema = 1
id = "k8s"
name = "Kubernetes"
version = "0.1.0"
description = "Pods as a block, kubectl get as a table."
icon = "box"
host = "host.luau"
window = "window.luau"
styles = ["k8s.css"]

[[blocks]]
id = "pods"
title = "Pods"
files = ["*.yaml"]

[[blocks]]
id = "logs"
title = "Logs"
icon = "file"
palette = false

[[lenses]]
id = "get"
match = ["kubectl get *", "k get *"]
```

## 清单的读取方式 {#how-the-manifest-is-read}

清单分两步检查：

1. **文本规则**，仅需文件本身：大小、TOML 语法、schema、键名与类型、id、名称长度、条目与样式路径，以及 `[[blocks]]`/`[[lenses]]` 规则。`tern plugin install` 与 `tern plugin link` 在接触 plugins 文件夹之前就应用这些规则。
2. **包规则**，需要包目录：指定的条目文件存在，样式表可读取且符合大小上限。加载器每次扫描 plugins 文件夹时都会应用这些规则。

只报告第一条被违反的规则。违反规则的包是一个**问题**，会连同消息一起出现在 `tern plugin list`、偏好设置 › 插件，以及“插件存在问题”的提示中；它不会加载任何内容。下面的消息按加载器报告的原样引用；`tern plugin install` 与 `link` 会在前面加上 `<dir> is not a plugin: `（参见[命令行](cli.md#errors)）。

未知键是错误，在顶层以及每个 `[[blocks]]` 与 `[[lenses]]` 表中都是如此。拼错的键会让包失败，而不是被忽略。

## 顶层键 {#top-level-keys}

| 键 | 类型 | 必需 | 默认值 | 规则 |
| --- | --- | --- | --- | --- |
| `schema` | 整数 | 是 | | 必须为 `1` |
| `id` | 字符串 | 是 | | `^[a-z][a-z0-9-]{0,31}$`；在已安装的包中唯一 |
| `name` | 字符串 | 是 | | 1–64 个字符 |
| `version` | 字符串 | 是 | | 自由格式 |
| `description` | 字符串 | 否 | `""` | 自由格式，单行 |
| `icon` | 字符串 | 否 | `"puzzle"` | 一个 Tern 图标名；未知名称会变成 `puzzle` |
| `host` | 字符串 | `host`、`window` 之一 | 缺省 | 包内的相对路径，以 `.luau` 或 `.lua` 结尾 |
| `window` | 字符串 | `host`、`window` 之一 | 缺省 | 包内的相对路径，以 `.luau` 或 `.lua` 结尾 |
| `styles` | 字符串数组 | 否 | `[]` | 每个都是包内的相对路径；合计 256 KiB |
| `blocks` | 表数组（`[[blocks]]`） | 否 | `[]` | 需要 `host` |
| `lenses` | 表数组（`[[lenses]]`） | 否 | `[]` | 需要 `host` |

### `schema` 格式版本 {#schema}

清单格式版本。当前只有 `1`。这项检查在任何其他键被读取之前运行，因此将来的 schema 会以清晰的消息失败，而不是给出一串未知键。

| 清单 | 消息 |
| --- | --- |
| 没有 `schema` 键 | `missing schema` |
| `schema = 2` | `unsupported schema 2` |
| `schema = "1"` | `schema must be an integer` |

### `id` 包标识 {#id}

插件在机器上的标识。它为插件贡献的一切命名：block 种类 `<id>.<block>`、lens id `plugin.<id>.<lens>`、动作 `plugin.<id>.<command>`、样式表 `plugin:local:<id>:…`，以及数据文件夹 `<state>/plugin-data/<id>`。参见[包与清单](../concepts/packages.md#ids-and-names)。

id 必须为 1–32 字节：一个小写 ASCII 字母，后跟小写字母、数字或 `-`。

| 清单 | 消息 |
| --- | --- |
| `id = "K8s"`、`id = "1x"`、33 个字符的 id | `invalid id "K8s" (lowercase letters, digits and -, 1-32 long)` |
| 名称顺序中更早的另一个包具有相同 id | `duplicate id k8s`（针对较后的目录报告） |

目录名不必与 id 一致；`tern plugin install` 会按 id 命名其副本。

### `name` 显示名称 {#name}

显示名称：插件命令在命令面板中的分组、其提示的首行（“插件 *名称*：*钩子* 失败”）、偏好设置以及 `tern plugin list`。它按 Unicode 字符计数，而非字节。

| 清单 | 消息 |
| --- | --- |
| `name = ""`，或超过 64 个字符 | `name must be 1-64 characters` |

### `version`、`description` {#version-description}

自由格式字符串，显示在 `tern plugin list`（仅版本）和偏好设置中。Tern 从不比较版本。

### `icon` 图标 {#icon}

Tern 图标集合中的一个图标（[图标名称](../elements/data.md#icon-names)：`box`、`sparkle`、`terminal`、`chev-r`、…），或 Tern 为 omp 接受的别名之一（`success`、`git-branch`）。最后一个 `.` 之前的部分会被忽略，因此 `icon.folder` 就是 `folder`。未知或缺失的名称会变成 `puzzle`；这不算错误。目录中携带解析后的名称。

### `host`、`window` {#host-window}

两个入口。至少要有一个。每个都是相对于包目录的路径，仅由普通组件和 `.` 组成（不含 `..`、不含根、不含盘符），以 `.luau` 或 `.lua` 结尾。

| 清单 | 消息 |
| --- | --- |
| 两个键都没有 | `needs a host or window entry` |
| `host = "../h.luau"`、`host = "/abs/h.luau"`、`host = ""` | `host "../h.luau" must be a relative path inside the plugin` |
| `window = "w.js"` | `window "w.js" must be a .luau or .lua file` |
| 文件不存在 | `missing entry host.luau` |

`host` 在 host 上下文中运行：负责 block、lens、host 事件和 `spawn` 过滤器的工作线程。`window` 在每个 Tern 窗口中运行。参见[架构](../concepts/architecture.md#the-two-halves)。

### `styles` 样式表 {#styles}

CSS 文件，每个都是包内的相对路径（规则与入口相同，扩展名任意）。它们按顺序读取，文件之间以换行连接，并在每个允许该插件的窗口中被安装为单个全局样式表 `plugin:local:<id>:styles`；安装发生在该窗口的 window 入口运行之前，无论该插件是否有 window 入口。参见 [chrome 与样式](../guides/chrome.md)。

| 清单 | 消息 |
| --- | --- |
| `styles = ["../x.css"]` | `style "../x.css" must be a relative path inside the plugin` |
| 文件无法读取 | `cannot read style k8s.css: <io error>` |
| 拼接后的文本超过 256 KiB | `styles are larger than 256 KiB` |

CSS 解析错误不是清单错误：样式表仍会安装，窗口会记录 `plugin style sheet has errors`。

## `[[blocks]]` block 声明 {#blocks}

每个表声明一种 block 类型，种类为 `<plugin>.<id>`。host 入口必须用 [`tern.block.define`](api-host.md#ternblockdefine) 定义它；该声明正是每个副本上的命令面板、“打开方式”菜单和路由决策所看到的内容。

| 键 | 类型 | 必需 | 默认值 | 规则与含义 |
| --- | --- | --- | --- | --- |
| `id` | 字符串 | 是 | | `^[a-z][a-z0-9-]{0,31}$`，在此插件的 block 中唯一 |
| `title` | 字符串 | 是 | | 命令面板行“新建 *标题* block”、“打开方式 *标题*”，以及该 block 的 `title` 处理函数返回之前的面板标题 |
| `icon` | 字符串 | 否 | 插件的图标 | 与顶层 `icon` 相同的图标名；未知时变成 `puzzle`（不是插件的图标） |
| `files` | 字符串数组 | 否 | `[]` | 文件名 glob；匹配的文件会提供“打开方式 *标题*” |
| `palette` | 布尔 | 否 | `true` | 命令面板是否提供“新建 *标题* block” |

`files` glob 仅与文件名匹配（不匹配其目录），忽略 ASCII 大小写：`*.yaml` 匹配 `Deploy.YAML`。“打开方式 *标题*”会在焦点面板旁启动该 block，位于文件所在文件夹，以文件路径作为唯一参数。菜单只列出当前会话所在 host 上处于 Ready 状态的插件的 block 类型。

| 清单 | 消息 |
| --- | --- |
| `[[blocks]]` 没有 `host` | `blocks need a host entry` |
| `id = "Pods"` | `invalid block id "Pods"` |
| 两个表具有相同的 `id` | `duplicate block id "pods"` |
| 缺少 `title` | ``missing field `title` `` |
| 未知键 | ``unknown field `shape`, expected one of `id`, `title`, `icon`, `files`, `palette` `` |

插件入口必须与声明一致；以下情况会使插件失败（状态 Failed），而不是包失败：

| 入口 | 错误 |
| --- | --- |
| 对未声明的 id 调用 `tern.block.define("x", …)` | `tern.block.define: block "x" is not declared in plugin.toml`（在入口中抛出） |
| 声明的 id 从未定义 | `block x is declared in plugin.toml but not defined with tern.block.define` |

## `[[lenses]]` lens 声明 {#lenses}

每个表声明一个命令 lens，id 为 `plugin.<plugin>.<id>`，以及它认领命令行所用的 glob。host 入口必须用 [`tern.lens.define`](api-host.md#ternlensdefine) 定义它。

| 键 | 类型 | 必需 | 默认值 | 规则与含义 |
| --- | --- | --- | --- | --- |
| `id` | 字符串 | 是 | | `^[a-z][a-z0-9-]{0,31}$`，在此插件的 lens 中唯一 |
| `match` | 字符串数组 | 是 | | 至少一个匹配 `program args…` 的 glob |

### 匹配模式 {#match-patterns}

shell 报告（OSC 133）的命令会先按简单命令读取：

- 跳过开头的 `VAR=value` 赋值；
- 连同其选项一起被跳过的包装程序：`sudo`、`doas`、`exec`、
  `time`、`nice`、`nohup`、`env`、`command`、`builtin`、`caffeinate`、`npx`、
  `bunx`、`pnpx`、`uvx`、`pipx`；
- 程序会去掉其目录部分（`/usr/bin/git` 即 `git`）；
- 引号与转义会被移除，重定向被丢弃；
- 输出不属于单个程序的行永远不会被认领：管道、列表（`;`、`&&`、`||`）、
  stdout 重定向、子 shell、heredoc，以及程序字中的命令替换。

程序及其参数以单个空格连接，每个模式必须匹配这整段文本。`*` 匹配任意长度的字符序列（可以为零），`?` 恰好匹配一个字符，其他每个字符匹配其本身。匹配区分大小写。

| 模式 | 命令行 | 是否认领 |
| --- | --- | --- |
| `kubectl get *` | `kubectl get pods` | 是 |
| `kubectl get *` | `FOO=1 sudo kubectl get pods -A` | 是 |
| `kubectl get *` | `kubectl get` | 否（空格必须存在） |
| `kubectl get *` | `kubectl get pods \| grep x` | 否（管道） |
| `kubectl get *` | `Kubectl get pods` | 否（大小写） |
| `kubectl *` | `kubectl logs x` | 是 |

以 shell 别名为名的模式无法透过别名去看实际命令：该行按 shell 报告的原样匹配。请把别名的各种形式列为额外模式（`"k get *"`）。

### 认领顺序 {#claim-order}

当多个 lens 匹配时，按 id 排序的第一个处于 Ready 状态的插件胜出；在该插件内，取清单顺序中第一个模式匹配的 lens。禁用与 Failed 的插件不认领任何内容。插件的认领优先于 Tern 的内置 lens。请按从最具体到最不具体的顺序排列 lens。

| 清单 | 消息 |
| --- | --- |
| `[[lenses]]` 没有 `host` | `lenses need a host entry` |
| `id = "Get"` | `invalid lens id "Get"` |
| 两个表具有相同的 `id` | `duplicate lens id "get"` |
| `match = []` | `lens "get" needs at least one match pattern` |
| 缺少 `match` | ``missing field `match` `` |

| 入口 | 错误 |
| --- | --- |
| 对未声明的 id 调用 `tern.lens.define("x", …)` | `tern.lens.define: lens "x" is not declared in plugin.toml`（在入口中抛出） |
| 声明的 id 从未定义 | `lens x is declared in plugin.toml but not defined with tern.lens.define` |

## TOML 与类型错误 {#toml-and-type-errors}

语法与类型错误会携带 TOML 解析器的消息，但不含位置信息：

| 清单 | 消息 |
| --- | --- |
| `name =`（没有值） | `string values must be quoted, expected literal string` |
| 一行 `not toml =` | ``key with no value, expected `=` `` |
| `id = 5` | ``invalid type: integer `5`, expected a string`` |
| `palette = "no"` | `invalid type: string "no", expected a boolean` |
| 缺少 `version` | ``missing field `version` `` |
| `color = "red"` | ``unknown field `color`, expected one of `schema`, `id`, `name`, `version`, `description`, `icon`, `host`, `window`, `styles`, `blocks`, `lenses` `` |

## 文件与文件夹规则 {#file-and-folder-rules}

| 规则 | 消息 |
| --- | --- |
| `plugin.toml` 超过 64 KiB | `plugin.toml is larger than 64 KiB` |
| 没有 `plugin.toml` 的目录 | `no plugin.toml` |
| `plugin.toml` 无法读取（权限、非 UTF-8） | `cannot read plugin.toml: <io error>` |
| 超过 64 个有效包 | 按 id 排序第 64 个之后的每个包都报 `too many plugins` |

plugins 文件夹中的 `<name>.path` 文件用于链接存放在其他位置的包；它们自己的消息（`cannot read link: …`、`link target "x" is not an absolute path`、`link target /x is not a directory`）列在[错误](errors.md#plugins-folder-problems)中。

## 相关页面 {#related-pages}

- [包与清单](../concepts/packages.md)：布局、文件夹与设置。
- [限制](limits.md)：每一项大小与数量。
- [命令行](cli.md)：安装与链接包。
