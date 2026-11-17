# 包与清单 {#packages-and-manifests}

插件是一个目录，内含 `plugin.toml` 清单、最多两个 Luau 入口文件，以及它们所用的模块与样式表。本页介绍包的目录结构、清单、包及其数据所在的位置、插件事物的命名方式，以及无法作为插件使用的文件夹如何被报告。逐键的完整规则见
[清单参考](../reference/manifest.md)。

## 包的目录结构 {#package-layout}

```text
k8s/
  plugin.toml      -- the manifest (schema 1)
  host.luau        -- host half: blocks, lenses, pane hooks
  window.luau      -- window half: commands, keys, routes, chrome, layout
  k8s.css          -- global styles, listed in `styles`
  lib/
    pods.luau      -- require("./lib/pods")
```

只有 `plugin.toml` 及其指定的入口是必需的。入口与样式路径相对于包目录，且不能离开该目录。文件夹中的其他内容只有在某个入口 `require` 它，或某个处理器用 `tern.fs` 读取它时才会被读取。

## 清单 {#the-manifest}

`plugin.toml` 使用 schema 1。未知键是错误，无论位于顶层还是任何表内部，因此拼写错误会让包失败，而不是被忽略。

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

[[lenses]]
id = "get"
match = ["kubectl get *", "k get *"]
```

| 键 | 用途 |
| --- | --- |
| `schema` | 必须是整数 `1`。 |
| `id` | 插件在该机器上的身份；作为其命名的一切的前缀。 |
| `name` | 显示名称：命令面板分组、提示、偏好设置。 |
| `version` | 自由格式；由 `tern plugin list` 与偏好设置显示。 |
| `description`、`icon` | 可选；未知或缺失的图标变为 `puzzle`。 |
| `host`、`window` | 两个入口；至少需要一个。每个都是相对的 `.luau` 或 `.lua` 路径。 |
| `styles` | 拼接为一张全局样式表的 CSS 文件，总计最多 256 KiB。 |
| `[[blocks]]` | Block 类型；每个都需要 host 入口中的 `tern.block.define`。 |
| `[[lenses]]` | 命令 lens 以及认领命令的 glob；每个都需要 host 入口中的 `tern.lens.define`。 |

Block 与 lens 在清单中声明、在 Lua 中定义，两者必须一致。清单那一半是每个副本无需运行 Lua 就能从 catalog 中得知的内容（block 标题与图标、lens 认领）；Lua 那一半是 host 运行的内容。定义未声明的 id 会在入口中抛出错误
（`tern.block.define: block "x" is not declared in plugin.toml`）；声明了入口从未定义的 id 会在入口结束时使插件失败
（`block x is declared in plugin.toml but not defined with tern.block.define`）。
因此，`[[blocks]]` 与 `[[lenses]]` 都需要 `host` 入口。

## 目录 {#directories}

这些页面中的路径使用两个占位符。`<config>` 是 Tern 的配置目录，`<state>` 是其状态目录：

| 平台 | `<config>` | `<state>` |
| --- | --- | --- |
| macOS | `~/Library/Application Support/Tern` | `~/Library/Application Support/Tern` |
| Linux | `$XDG_CONFIG_HOME/tern`（`~/.config/tern`） | `$XDG_STATE_HOME/tern`（`~/.local/state/tern`） |
| Windows | `%APPDATA%\Tern` | `%LOCALAPPDATA%\Tern` |
| 任意平台，设置了 `TERN_CONFIG_DIR` | `$TERN_CONFIG_DIR` | `$TERN_CONFIG_DIR` |

### 插件文件夹 {#the-plugins-folder}

包位于 `<config>/plugins/`；`tern plugin dir` 会打印它。在 iOS 上，该文件夹是 App 的 `Documents/Plugins`，Files App 将其显示为“我的 iPhone”（或 iPad）› Tern › Plugins。iOS 没有命令行，也没有 `git`：把包文件夹复制到那里即可。

Tern 按名称顺序读取插件文件夹中的条目：

| 条目 | 视为 |
| --- | --- |
| 目录（或指向目录的符号链接） | 包；其 `plugin.toml` 必须直接位于其中。 |
| 文件 `<name>.path` | 链接的包：文件去掉首尾空白后的内容必须是指向包目录的绝对路径。`tern plugin link DIR` 会写出 `<id>.path`。 |
| 以 `.` 开头的名称 | 跳过。`tern plugin` 在点开头的同级项中暂存变更。 |
| 其他任何文件 | 忽略。 |

已安装的包是 `<config>/plugins/<id>` 处的一份副本
（`tern plugin install`）；链接的包留在原处并从那里加载，这正是开发它时想要的方式。参见
[分发](../guides/distribution.md)与
[命令行](../reference/cli.md)。

### 数据文件夹 {#the-data-folder}

每个插件获得 `<state>/plugin-data/<id>/`，在其某个 VM 启动时创建。Lua 通过 `tern.plugin.data` 看到它的绝对路径；用 `tern.process.run` 运行的程序通过 `TERN_PLUGIN_DATA` 环境变量获得它。`tern.kv` 将其值保存在那里的 `kv.json` 中，每次 `tern.kv.set` 都通过临时文件加重命名的方式重写。

插件的两个半区，以及每个窗口中的 window 半区，共享这个文件夹与一个 `tern.kv` 存储：当文件的修改时间或长度变化时，每个 VM 会重新读取 `kv.json`，因此 `get` 能看到其他 VM 的写入，`set` 也绝不会写回过期的副本。同一瞬间的两次 `set` 仍会竞争，最后一次重命名获胜。参见
[文件、进程与存储](../guides/io.md)。

## 设置 {#settings}

`<config>/settings.json` 中的两个键决定哪些插件加载。每台机器读取自己的设置；host 之间不同步任何内容。

| 键 | 默认值 | 作用 |
| --- | --- | --- |
| `plugins` | `true` | `false` 时完全不加载插件。 |
| `plugins_disabled` | `[]` | 保持不加载的插件 id（状态 Disabled）。 |

偏好设置 › 插件 可编辑两者，并在任一变化时重新加载会话与窗口的插件。两个半区在每次加载与重新加载时都会重新读取 `settings.json`（守护进程、窗口，以及没有守护进程运行时窗口自己的 host 运行时），因此手动编辑会在下次重新加载时于各处生效。无头运行（`tern shot`、`tern serve`）只在 `plugins fixtures` 场景命令下加载插件，该命令同样从
`settings.json` 读取这两个键。

## Id 与名称 {#ids-and-names}

插件、block 与 lens 的 id 都匹配 `^[a-z][a-z0-9-]{0,31}$`：一个小写字母，然后是至多 31 个小写字母、数字或 `-`。block 与 lens 的 id 在其插件内唯一。插件贡献的一切都以其 id 命名：

| 事物 | 名称 | 使用于 |
| --- | --- | --- |
| Block 类型（kind） | `<plugin>.<block>` | `cx:new_block`、`launch.block`、路由决策 `{block = …}` |
| Block surface 角色 | `plugin.<plugin>.<block>` | CSS `[data-surface='plugin.k8s.pods']`，设置在 block 的区域元素上 |
| Lens id | `plugin.<plugin>.<lens>` | Lens block：block 的角色为 `lens.` 后接其 lens id |
| Lens block 角色 | `lens.plugin.<plugin>.<lens>` | CSS `.sf-block[data-role='lens.plugin.k8s.get']` |
| 命令动作 | `plugin.<plugin>.<id>` | `tern.bind`、`settings.json` 中的 `keybinds`、状态行段 `command` |
| 函数绑定动作 | `plugin.<plugin>.bind.<n>` | 传给 `tern.bind` 的第 `n` 个函数，从 0 计数 |
| 清单样式表 | `plugin:local:<plugin>:styles` | 样式级联，位于 Tern 自身样式表之后 |
| `tern.css` 样式表 | `plugin:local:<plugin>:<name>` | 样式级联 |
| 远程 host 的样式表 | `plugin:<host>:<plugin>:styles` | 样式级联 |
| 数据文件夹 | `<state>/plugin-data/<plugin>` | `tern.plugin.data`、`TERN_PLUGIN_DATA` |

命令 id（`tern.command`）与样式表名称（`tern.css`）更宽松：ASCII 字母、数字、`_` 与 `-`。命令不能命名为 `bind`，样式表不能命名为 `styles`。

## 模块与 `require` {#modules-and-require}

`require("tern")` 返回 `tern` 表，它同时也是全局的 `tern`。任何其他字符串都是相对于调用 `require` 的文件的路径：

| 调用 | 加载 |
| --- | --- |
| `require("./util")` | 调用者旁边的 `util.luau`、`util.lua`、`util/init.luau` 或 `util/init.lua` |
| `require("./lib/pods")` | `lib/pods.luau`（或其他三种形式） |
| `require("../shared")` | 上一级目录，前提是它仍在包内 |

解析到上述多个文件的路径是错误，离开包目录的路径同样是错误。`.luaurc` 文件与 `@alias` 路径不会被读取。模块在 VM 内按解析后的文件缓存，因此每个半区只加载一次共享模块。参见[运行时、预算与 JIT](runtime.md#modules)。

## 样式 {#styles}

`styles` 中列出的文件在包加载时读取，以换行符连接，总计上限为 256 KiB；文件缺失或总量超限都是该包的问题。在本机上，窗口运行时会把它们作为全局样式表 `plugin:local:<id>:styles` 安装在 Tern 自身样式表之后，对所有设置允许的插件生效，无论其是否有 window 入口，且在该入口运行之前。远程 host 上 Ready 插件的样式随其 catalog 到达，并安装为 `plugin:<host>:<id>:styles`。window 半区可以在运行时用 `tern.css` 添加更多样式表。参见 [chrome 与样式](../guides/chrome.md)。

## 问题与状态 {#problems-and-statuses}

无法成为插件的文件夹是一个**问题**：它会连同错误一起列出，并且不加载任何内容。有效的包有一个**状态**。

| 问题 | 原因 |
| --- | --- |
| `no plugin.toml` | 没有清单的目录。 |
| `plugin.toml is larger than 64 KiB` | 清单过大。 |
| 清单规则，例如 `unsupported schema 2`、`invalid id "X"`、`needs a host or window entry`、`blocks need a host entry` | 清单违反了 schema 1 的规则（[清单参考](../reference/manifest.md)）。 |
| `missing entry host.luau` | 指定的入口文件不存在。 |
| `cannot read style k8s.css: …`、`styles are larger than 256 KiB` | 样式表无法读取，或总量过大。 |
| `link target … is not an absolute path`、`link target … is not a directory` | `.path` 文件指向了不可用的内容。 |
| `duplicate id k8s` | 名称顺序中更早的条目已使用该 id。 |
| `too many plugins` | 有效包超过 64 个；包按 id 排序，第 64 个之后的被略过。 |

| 状态 | 含义 |
| --- | --- |
| Ready | 已加载；其入口已运行。 |
| Disabled | 被 `plugins` 或 `plugins_disabled` 关闭。 |
| Failed | 入口在加载时抛出错误，或让已声明的 block 或 lens 未定义；错误被保留。 |

问题与状态会出现在 `tern plugin list`、偏好设置 › 插件 中，并在 host 的 catalog 变化时作为提示出现。每个半区的状态来源，参见
[生命周期与重新加载](lifecycle.md#the-catalog-and-statuses)。

## 相关页面 {#related-pages}

- [清单参考](../reference/manifest.md)：每个键与规则。
- [生命周期与重新加载](lifecycle.md)：何时再次读取包。
- [限制](../reference/limits.md)：尺寸与数量汇总于一张表。