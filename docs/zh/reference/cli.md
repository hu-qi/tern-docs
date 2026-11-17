# 命令行 {#command-line}

`tern plugin` 管理本机 plugins 文件夹中的包，并请求会话守护进程重新加载它们。它只操作文件和正在运行的守护进程，本身从不运行插件的 Lua 代码。iOS 没有命令行：请改为把包复制到“文件”App 的 Tern › Plugins 文件夹。

## 用法概要 {#synopsis}

```sh
tern plugin list [--json]
tern plugin reload [ID] [--json]
tern plugin dir [--json]
tern plugin install SRC [--force] [--json]
tern plugin remove ID [--json]
tern plugin link DIR [--json]
tern plugin unlink ID [--json]
tern plugin types DIR [--json]
tern plugin --help
```

## 通用行为 {#common-behavior}

| 选项 | 含义 |
| --- | --- |
| `--json` | 以格式化 JSON 而非文本输出结果 |
| `--window KEY` | 每个 `tern` 命令都接受该选项（用于决定使用哪个窗口的守护进程连接：`--window`，否则为命令所在面板的窗口，再否则为第一个窗口）。每个用户只有一个守护进程，因此它不会改变某个子命令能看到哪些插件 |
| `--help`、`-h` | 打印下面的用法并以 0 退出 |

选项可以放在子命令词之前或之后，`--window` 也支持 `--name=value` 形式。其他任何选项都是用法错误。plugins 文件夹属于整台机器，而不属于某个窗口，这正是 `tern plugin --help` 没有窗口说明的原因。

“守护进程”指本机 socket 上的会话守护进程（`$TERN_DAEMON_SOCKET`，否则为运行时目录或设置目录中的 `daemon.sock`）。`tern plugin` 从不启动它。

### 退出码 {#exit-codes}

| 代码 | 场景 |
| --- | --- |
| `0` | 成功，包括后续重载报告了问题的修改类子命令 |
| `1` | 子命令失败（消息输出到标准错误）；当新的目录中存在状态为 Failed 的插件或出现问题时，`reload` 也以 1 退出 |
| `2` | 用法错误：未知选项、缺少或多余的字词。消息之后会输出用法文本 |
| `124` | 守护进程没有在 60 秒内响应 `reload` |

错误以 `tern plugin: <message>` 的形式输出到标准错误。

### 变更后重载 {#reload-after-a-change}

`install`、`remove`、`link` 与 `unlink` 会改动 plugins 文件夹，然后请求守护进程重新加载所有插件，并最多等待 60 秒以取得新的目录。它们在自己的输出行之后打印的内容：

| 结果 | 文本模式（标准输出） | `--json`（标准错误） |
| --- | --- | --- |
| 没有守护进程在运行 | `no daemon running; changes apply at next start` | 相同 |
| 重载成功且全部加载 | 无 | 无 |
| 插件失败或文件夹存在问题 | 状态为 Failed 的每个插件一行 `list` 输出，然后是 `problem …` 行 | 相同 |
| 重载请求失败 | `the daemon did not reload its plugins: <error>` | 相同 |

这些都不会改变退出码。窗口在发现文件夹变化时会重新加载自己的 window 半区；参见[生命周期与重载](../concepts/lifecycle.md#watching)。

## `tern plugin list` 列出插件 {#tern-plugin-list}

打印正在运行的守护进程的目录，内容为命令连接时的状态：每个已安装插件及其状态，然后是文件夹的问题。没有守护进程时，它直接读取 plugins 文件夹与设置，不运行任何 Lua：设置允许的每个有效包都是 `ready`。加载失败的 window 条目在这里永远不会显示为失败，因为 host 的目录并不知道它。

文本输出，每个插件一行，然后每个问题一行：

```text
hello 0.1.0 Hello — 1 blocks, 1 lenses, window  ready
k8s 0.3.0 Kubernetes — 2 blocks, 1 lenses  disabled
jsonx 1.0.0 JSON Explorer — 0 blocks, 1 lenses  failed: lens tree is declared in plugin.toml but not defined with tern.lens.define
problem /Users/me/Library/Application Support/Tern/plugins/broken: no plugin.toml
```

| 部分 | 含义 |
| --- | --- |
| `ID VERSION NAME` | 来自清单 |
| `— N blocks, M lenses` | `[[blocks]]` 与 `[[lenses]]` 的数量 |
| `, window` | 清单含有 `window` 条目时出现 |
| 状态（位于两个空格之后） | `ready`、`disabled`，或 `failed: ` 加上错误的首行；host 半区钩子因超出预算而被暂停的就绪插件会追加 `, paused over budget: ` 及其名称（`ready, paused over budget: timer`） |
| `problem DIR: ERROR` | 不是可用插件的文件夹条目 |

空文件夹打印 `no plugins`。退出码 0。

`--json` 打印目录：

```json
{
  "plugins": [
    {
      "id": "hello",
      "name": "Hello",
      "version": "0.1.0",
      "description": "The plugin fixture: a greeting lens, a counter block and a few hooks.",
      "icon": "sparkle",
      "css": "…",
      "blocks": [
        { "id": "counter", "title": "Counter", "icon": "sparkle", "files": ["*.json"], "palette": true }
      ],
      "lenses": [{ "id": "greet", "patterns": ["tern-hello *"] }],
      "host": true,
      "window": true,
      "status": "ready"
    }
  ],
  "problems": [{ "dir": "/…/plugins/broken", "error": "no plugin.toml" }],
  "jit": false
}
```

| 字段 | 含义 |
| --- | --- |
| `plugins[]` | 已安装的插件，按 id 排序 |
| `.icon`、`.blocks[].icon` | 解析后的图标名称（未知时为 `puzzle`） |
| `.css` | 清单中的 `styles` 拼接后的结果 |
| `.lenses[].patterns` | 清单中的 `match` glob |
| `.host`、`.window` | 各自条目是否存在 |
| `.status` | `"ready"`、`"disabled"`，或 `{"failed": "<full error>"}` |
| `.paused` | 当前因超出预算而暂停的 host 半区钩子；没有时省略 |
| `problems[]` | 每个不可用文件夹条目对应的 `{dir, error}` |
| `jit` | 守护进程是否以原生代码生成运行 Luau；没有守护进程时始终为 `false` |

## `tern plugin reload` 重新加载插件 {#tern-plugin-reload}

让守护进程重新读取 `settings.json` 和 plugins 文件夹，并重新加载每个插件，或在给出时只重新加载插件 `ID`，然后像 `list` 那样打印新的目录。本机的窗口也同样重载：它们的全部 window 半区，或仅 `ID` 的 window 半区。被重载插件的运行中 block 会从上次保存的状态重新启动；其他插件继续运行，不受影响。版本早于本次的守护进程即使给出 `ID` 也会重载每个插件。参见[生命周期与重载](../concepts/lifecycle.md#reloading)。

在打印目录之后，当某个插件为 Failed 或文件夹存在问题时会以 1 退出，便于脚本与 CI 检查包：

```sh
tern plugin link . && tern plugin reload
tern plugin reload hello   # only the plugin you're working on
```

| 错误 | 退出码 |
| --- | --- |
| `no daemon running` | 1 |
| `the session daemon did not answer`（已过 60 秒） | 124 |

## `tern plugin dir` 插件目录 {#tern-plugin-dir}

打印 plugins 文件夹：`<config>/plugins`，在设置了该变量时为 `$TERN_CONFIG_DIR/plugins`。`--json` 打印 `{"dir": "<path>"}`。该文件夹可能尚不存在；`install` 与 `link` 会创建它。当机器没有配置目录时，以 `no config directory for plugins` 失败。

## `tern plugin install` 安装 {#tern-plugin-install}

```sh
tern plugin install ./my-plugin
tern plugin install github.com/me/tern-k8s
tern plugin install github.com/stencil-hq/tern-sdk/plugins/examples/jsonx
tern plugin install https://example.com/me/tern-k8s.git --force
```

把包复制到 plugins 文件夹中，命名为 `<plugins>/<id>`，名称取自清单中的 id，然后重新加载。

当 `SRC` 以 `https://`、`http://`、`git@` 或 `ssh://` 开头，或是 `github.com/OWNER/REPO[/PATH]` 形式时，它就是 git 源（此时克隆 `https://github.com/OWNER/REPO`，包为其目录 `PATH`）。
git 源使用 `git clone --depth 1 --quiet` 克隆到临时目录，并设置 `GIT_TERMINAL_PROMPT=0`，使私有仓库直接失败而不会提示输入密码。其他形式都是本地目录，相对于当前目录；开头的 `~` 或 `~/` 表示主目录（因此带引号的 `~/src/plugin`，或在偏好设置中输入的同类路径，都能正常工作）。包必须位于源目录的根下，或 `PATH` 的根下。

复制任何内容之前，会先用加载器自身的检查校验源：清单通过全部[文本规则](manifest.md#how-the-manifest-is-read)，清单指定的条目存在，清单指定的样式表可读取且符合大小限制。
复制过程会跟随符号链接，跳过 `.git`，先在加载器会跳过的点号同级目录中暂存，再重命名到位；替换已有副本时，会先移开旧副本，若重命名失败则将其恢复。

| 选项 | 含义 |
| --- | --- |
| `--force` | 替换同 id 的已安装包。如果该包位于 plugins 文件夹内名称不同的文件夹中，则在新副本就位后删除旧文件夹 |

输出：`installed ID VERSION → DIR`。`--json` 打印 `{"id", "version", "dir"}`。

| 错误 | 原因 |
| --- | --- |
| `ID is already installed (DIR); --force replaces it` | 已存在同 id 的包，或名为 `<id>` 的文件或文件夹 |
| `ID is linked (DIR); use unlink first` | 该 id 属于链接的包；`--force` 从不替换链接 |
| `no directory SRC: <io error>` | 本地源不存在 |
| `SRC is not a directory` | 本地源是文件 |
| `DIR is not a plugin: no plugin.toml` | 源目录的根下没有清单 |
| `DIR is not a plugin: <manifest message>` | 某条[清单规则](manifest.md)不通过，或 `plugin.toml is larger than 64 KiB` |
| `DIR is not a plugin: missing entry FILE` | 清单指定的某个条目不存在 |
| `DIR is not a plugin: cannot read style FILE: <io error>` | 清单指定的某个样式表不存在或无法读取 |
| `DIR is not a plugin: styles are larger than 256 KiB` | 样式表合计过大 |
| `installing from git needs git` | `PATH` 中没有 `git` |
| `git clone URL failed: <git's stderr>` | 克隆失败 |
| `no directory PATH in URL` | 克隆结果中没有 `PATH` |
| `PATH is not a directory in URL` | `PATH` 是文件，或指向克隆目录之外（经由 `..` 或符号链接） |

## `tern plugin remove` 移除 {#tern-plugin-remove}

删除清单 id 为 `ID` 的已安装包（即 plugins 文件夹内它的文件夹，无论该文件夹叫什么；符号链接只删除链接本身，不删除其目标），然后重新加载。当没有有效包使用该 id 时，改为删除 plugins 文件夹中名称恰好为 `ID` 的文件或文件夹，这可以清除损坏的包。

输出：`removed ID (DIR)`。`--json` 打印 `{"removed": "<path>"}`。

| 错误 | 原因 |
| --- | --- |
| `ID is linked; use unlink` | 该 id 属于链接的包 |
| `no plugin ID in DIR` | 没有该 id 或该名称的内容 |
| `no plugin id ID` | `ID` 为空、以 `.` 开头，或包含 `/` 或 `\` |

## `tern plugin link` 链接 {#tern-plugin-link}

```sh
tern plugin link ~/src/tern-k8s
```

就地使用包：写入 `<plugins>/<id>.path`，内容为包的绝对规范路径加一个换行，然后重新加载。Tern 从该目录加载包并监视它，因此编辑后无需复制即可重新加载。这是开发时的用法；参见[快速开始](../guides/getting-started.md)。

目录的检查与 `install` 相同。对已链接的 id 再次执行链接会重新指向该链接。

输出：`linked ID VERSION → DIR`。`--json` 打印 `{"id", "version", "dir"}`。

| 错误 | 原因 |
| --- | --- |
| `ID is already installed (DIR)` | 该 id 上已有安装副本（非链接）；请先 `remove` |
| `DIR is not UTF-8` | 包路径无法写入 `.path` 文件 |
| `no directory …`、`… is not a directory`、`… is not a plugin: …` | 与 `install` 相同 |

## `tern plugin unlink` 取消链接 {#tern-plugin-unlink}

删除链接 `ID` 的 `.path` 文件（通常是 `<id>.path`，或任何指定该包目录的 `.path` 文件），然后重新加载。包目录本身不受影响。

输出：`unlinked ID (FILE)`。`--json` 打印 `{"removed": "<path>"}`。

| 错误 | 原因 |
| --- | --- |
| `ID is installed, not linked; use remove` | 该 id 属于 plugins 文件夹中的副本 |
| `no plugin ID in DIR` | 没有该 id 的内容 |
| `no plugin id ID` | `ID` 为空、以 `.` 开头，或包含 `/` 或 `\` |

## `tern plugin types` 类型定义 {#tern-plugin-types}

```sh
tern plugin types .
```

写出 `DIR/tern.d.luau`，即此 Tern 随附的 `tern` 模块的 Luau 定义文件，必要时创建 `DIR`（相对于当前目录）。它会覆盖已有文件。输出：`wrote FILE`；`--json` 打印 `{"file": "<path>"}`。它不会改动 plugins 文件夹或守护进程。luau-lsp 的设置参见 [API 参考](api.md#types-for-luau-lsp)。

## 错误 {#errors}

用法错误以 2 退出，先打印消息，再打印用法：

| 消息 | 原因 |
| --- | --- |
| `tern plugin: plugin takes other arguments` | 没有子命令、未知子命令，或字词数量不对（如 `tern plugin install` 未给出 `SRC`） |
| `tern plugin: unknown flag --NAME` | 子命令不接受的选项（`--force` 是 `install` 唯一的选项） |
| `tern plugin: --window takes a value` | `--window` 位于行尾 |

其他所有失败都以 1 退出（超时以 124 退出），并输出 `tern plugin: <message>`；这些消息见上文各子命令的表格，以及[错误](errors.md#command-line)。

## 相关页面 {#related-pages}

- [分发](../guides/distribution.md)：发布包。
- [包与清单](../concepts/packages.md#the-plugins-folder)：文件夹布局与 `.path` 链接。
- [清单参考](manifest.md)：`install` 与 `link` 所检查的规则。
