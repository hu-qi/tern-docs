# 分发 {#distribution}

插件以目录形式发布，根目录下有 `plugin.toml`，通常是一个 git 仓库。用户用
`tern plugin install` 安装它，该命令会把插件复制到用户的插件文件夹；开发期间，
`tern plugin link` 会就地加载它。本页介绍仓库的布局、每个会改动该文件夹的
`tern plugin` 子命令、插件的启用与停用、版本管理、在 iOS 与远程 host 上的安装位置，
以及查找与分享插件。

```sh
tern plugin install github.com/you/tern-k8s
```

## 打包仓库 {#packaging-a-repository}

`install` 从源的根目录取包：仓库根（或给定的目录）必须包含 `plugin.toml`。git URL
总是从其根目录安装；要在一个 GitHub 仓库中发布多个插件，请给每个插件各自的目录，
并以 `github.com/OWNER/REPO/PATH` 的形式安装（参见[安装](#installing)）。

```text
tern-k8s/
  plugin.toml
  host.luau
  window.luau
  lib/
    pods.luau
  k8s.css
  README.md
  LICENSE
```

源目录中的所有内容都会被复制，`.git` 目录除外，因此安装后的包也带着 README、测试与
截图。加载器只读取 `plugin.toml`、入口、它们 `require` 的模块、`styles` 文件，以及
处理函数用 `tern.fs` 读取的内容；其余内容只占空间。不要把大体积资源和构建产物放进
仓库：包目录会被监视变化，而在 Linux 与 iOS 上，庞大的目录树会耗费监视与轮询资源
（参见[生命周期与重载](../concepts/lifecycle.md#watching)）。

插件在运行时写入的文件应放在 `tern.plugin.data`，绝不放在包中：安装会替换包目录，
而其中的任何改动都会重载插件。

如果提交 `tern plugin types` 生成的 `tern.d.luau`，它会随其余内容一起被复制；运行时
没有任何东西读取它。许多作者忽略它，让每位贡献者为自己的 Tern 版本生成。

## 安装 {#installing}

```sh
tern plugin install SRC [--force]
```

`SRC` 是一个 git URL 或本地目录：

| SRC | 视为 |
| --- | --- |
| 以 `https://`、`http://`、`git@` 或 `ssh://` 开头 | git URL，按原样克隆。 |
| 以 `github.com/` 开头 | `github.com/OWNER/REPO`，从 `https://github.com/OWNER/REPO` 克隆；`REPO` 之后的部分是包在该仓库中的目录（`github.com/stencil-hq/tern-sdk/plugins/examples/jsonx`）。 |
| 其他任何内容 | 目录，相对于当前目录。 |

git 源会从默认分支浅克隆（`--depth 1`）到临时目录，之后该目录被删除。安装需要
`PATH` 中有 `git`（否则报 `installing from git needs git`）。git 运行时关闭终端提示，
因此需要密码的仓库会直接失败而不会询问；对私有仓库请使用带已加载密钥的 SSH URL 或
凭据助手。克隆失败会报告 `git clone URL failed:` 以及 git 的消息。要安装默认分支
以外的标签或分支，请自行克隆后再安装该目录。

复制之前，`install` 会在不运行任何 Lua 的情况下检查包：`plugin.toml` 必须能按
schema 1 解析，`host` 与 `window` 入口以及每个 `styles` 文件都必须存在。不合格的包
会报告 `DIR is not a plugin: WHY`。Lua 错误只有在插件加载后才会显现，因此要读命令
在复制之后打印的内容。

包会被安装为 `<plugins>/<id>`，名称取自清单的 `id`，与源目录叫什么无关：

1. 源被复制（跟随符号链接、跳过 `.git`）到目标旁一个以点开头的暂存目录（加载器会
   跳过点开头的名字，因此半完成的复制永远不会被加载）。
2. 已有的副本被移到另一个以点开头的目录，新副本被重命名到位，旧副本随后被删除。
   若重命名失败，旧副本会被移回。

安装一个已安装的 id 会失败，并提示 `ID is already installed (DIR); --force replaces
it`. With `--force` 时，新副本替换旧副本；若旧副本位于另一个名字的目录中，该目录会
被删除。已链接的包永远不会被替换：无论是否带 `--force`，`install` 都会失败并提示
`ID is linked (DIR); use unlink first`。

```text
$ tern plugin install ~/src/tern-k8s
installed k8s 0.3.0 → /Users/me/Library/Application Support/Tern/plugins/k8s
```

改动之后，该命令会让会话守护进程重载插件，并打印任何加载失败的插件以及文件夹中的
任何问题。若没有守护进程在运行，它会打印
`no daemon running; changes apply at next start`。机器上的窗口会各自监视文件夹来重载其
window 半区。参见
[生命周期与重载](../concepts/lifecycle.md#reloading)。

偏好设置 › 插件 提供同样的安装入口 **Install…**：一个目录或 git URL，被复制到插件
文件夹。它从不替换已安装的副本（没有 `--force`）。目录开头的 `~` 表示主目录，此处
与命令行上都是如此。

## 为开发建立链接 {#linking-for-development}

```sh
tern plugin link ~/src/tern-k8s
```

`link DIR` 像 `install` 那样校验包，然后写入 `<plugins>/<id>.path`，其中是目录的
绝对路径。Tern 从那里加载包并监视该目录，因此保存文件即会重载插件。用另一个目录
再次链接会移动该链接。若已安装了同 id 的另一个包，链接会失败
（`ID is already installed (DIR)`）。

`tern plugin unlink ID` 删除 `.path` 文件，不触碰你的目录。对已安装的副本会失败
（`ID is installed, not linked; use remove`）。

## 移除 {#removing}

`tern plugin remove ID` 删除已安装的副本并重载，与 `install` 相同。它拒绝已链接的
包（`ID is linked; use unlink`）。插件的数据文件夹 `<state>/plugin-data/<id>/` 及其
`kv.json` 会被保留，因此重新安装时能找回它的状态；要重新开始，请手动删除它。

被移除插件所提供的各类型的 block 会在 host 重载时结束，并提示
`no block type KIND on this host`。

## 文件夹的位置 {#where-the-folder-is}

`tern plugin dir` 打印插件文件夹（`<config>/plugins`；参见
[包与清单](../concepts/packages.md#directories)）。每个 `tern plugin` 子命令都接受
`--json` 与 `--window KEY`。

| 子命令 | 打印 |
| --- | --- |
| `dir` | 该文件夹。 |
| `install SRC [--force]` | `installed ID VERSION → DIR` |
| `link DIR` | `linked ID VERSION → DIR` |
| `unlink ID` | `unlinked ID (FILE)` |
| `remove ID` | `removed ID (DIR)` |

每个子命令及其输出参见[命令行](../reference/cli.md)。

## 启用与停用插件 {#turning-plugins-on-and-off}

有两个设置决定一台机器上加载哪些插件：

```json
{
	"plugins": true,
	"plugins_disabled": ["k8s"]
}
```

`plugins = false` 不加载任何插件。`plugins_disabled` 中的 id 保持安装状态但不加载：
`tern plugin list` 中状态为 `disabled`，偏好设置中显示为关闭。被停用的插件不运行任何
Lua、不安装样式，其 block 类型也会从该 host 上消失。

偏好设置 › 插件 有一个总管开关，以及每个插件一个开关；拨动任一开关都会保存设置并
重载该窗口及其守护进程的插件。手动编辑 `settings.json` 之后，请从命令面板依次运行
**Reload settings** 与 **Reload plugins**：守护进程在每次重载时都会读取该文件，但
窗口会一直使用它持有的设置，直到被要求重新读取。

设置是按机器保存的。在笔记本电脑上停用某个插件，并不会在远程 host 上停用它。

## 版本管理 {#versioning}

清单中的 `version` 是自由文本。Tern 会在 `tern plugin list`、偏好设置与安装输出中
显示它，但从不比较它：没有更新命令，也没有依赖解析。用户通过带 `--force` 再次安装
来更新，或在对已链接的检出执行 `git pull` 来更新。

实践中的规则：

- 每次发布都提升 `version`，这样用户与错误报告能说明自己运行的是哪个版本。
- 保持默认分支可安装：`install` 克隆其最新提交。为希望固定版本的用户打标签发布。
- `schema = 1` 是清单格式，不是你的版本；保持原样。
- 插件 API 没有版本号。某个 Tern 版本新增的成员在更旧的版本中不存在，因此依赖新
  功能时请用 `if tern.chrome then … end` 这样的检查来测试。
- 让保存的状态在各版本之间可读。安装会重载 host，运行中的 block 会以旧代码 `save`
  返回的状态在新代码下重启。`tern.kv` 与数据文件夹中的数据也会延续；当其结构可能
  变化时，在旁边存一个格式编号。

## iOS {#ios}

iPhone 与 iPad 上的 Tern 没有命令行，也没有 `git`。其插件文件夹是应用的
`Documents/Plugins`，Files 应用把它显示为 On My iPhone（或 iPad）› Tern › Plugins；
偏好设置 › 插件 会说明位置。用 Files（从 iCloud Drive、共享或 AirDrop）把一个包
文件夹复制到那里，然后使用页面的 **Reload** 按钮或命令面板的 **Reload plugins**；
该文件夹也会每两秒轮询一次变化。

iOS 只运行 window 半区，并且以解释方式运行（无 JIT）。host 入口会被跳过：block 与
lens 来自应用所附着的 host，只要那些 host 安装了该插件就会显示。`tern.process.run`
在 iOS 上会抛出错误，因此兼顾两者的 window 半区要先做检查：

```lua
if tern.runtime.os ~= "ios" then
	tern.process.run({ "git", "status", "--short" }, nil, function(result, _cx)
		tern.log.warn("git status", result.status)
	end)
end
```

参见[支持矩阵](../concepts/support-matrix.md)。

## 远程 host {#remote-hosts}

每个半区都在其上下文所在之处运行，因此请把每个半区安装到运行它的机器上：

| 半区 | 安装到 |
| --- | --- |
| host 半区（block、lens、钩子、`spawn` 过滤器） | 其服务的面板所在的机器。对远程 host，就是那台 host。 |
| window 半区（命令、按键、路由、chrome、布局） | 显示窗口的机器。它作用于其中的每个面板，包括远程面板。 |
| 清单 `styles` | 两者皆可。远程 host 上 Ready 的插件会把其清单样式安装到你的窗口中。 |

要在远程 host 上安装，请在该 host 的面板中运行 `tern plugin install`：那里的 `tern`
会安装到那台机器的插件文件夹，并重载该 host 的守护进程。同时具有两个半区、且希望
用于远程面板的插件，需要在两台机器上都安装。远程 host 的插件以其名称在你的
偏好设置 › 插件 下以只读方式显示，命令面板的 **Reload plugins** 会重载每个已附着的
host。

远程 host 的 window 半区不在你的窗口中运行，其 `tern.css` 样式表也到不了你的窗口；
只有它的清单样式可以。参见
[架构](../concepts/architecture.md#where-each-half-runs)与
[Chrome 与样式](chrome.md#global-css)。

## 查找与分享插件 {#finding-and-sharing-plugins}

Tern 没有官方插件仓库，应用中也没有插件库：偏好设置 › 插件 只安装你提供的源。其他人
编写的插件列在 [Awesome Tern](https://github.com/theblazehen/awesome-tern) 中，那是
Tern 插件、Surface 协议应用与工具的社区目录；kind 为 `plugin` 的条目就是 Luau 插件。
Stencil 不运营也不审核该目录。许多作者还会给仓库打上
[`tern-plugin`](https://github.com/topics/tern-plugin) 这个 GitHub 话题标签。

从 GitHub 仓库安装插件时按其路径指定，包不在仓库根目录时再加上文件夹：

```sh
tern plugin install github.com/OWNER/REPO
tern plugin install github.com/OWNER/REPO/PATH
```

该文件夹必须包含 `plugin.toml`；把多个插件放在子文件夹中的仓库需要指定子文件夹。
GitHub 网页视图中的子文件夹链接
`https://github.com/OWNER/REPO/tree/BRANCH/PATH` 应安装为
`github.com/OWNER/REPO/PATH`：去掉 `https://` 与 `tree/BRANCH`，因为安装总是取默认
分支（参见[安装](#installing)）。同一源也可用于偏好设置 › 插件 › **Install…**。
对其他 git 主机，请给出完整的 git URL；那会从仓库根目录安装。

分享插件时：

1. 把它发布为公开的 git 仓库，使其可用 `tern plugin install` 安装，`plugin.toml`
   位于仓库根目录或它自己的文件夹中（[打包仓库](#packaging-a-repository)）。
2. 在 README 中写上确切的安装命令，并说明它在 `PATH` 上需要什么以及它包含哪些半区
   （[远程 host](#remote-hosts)）。
3. 为仓库添加 `tern-plugin` 话题。
4. 按该目录的
   [贡献指南](https://github.com/theblazehen/awesome-tern/blob/main/CONTRIBUTING.md)
   所述，通过为其 `list.yml` 添加条目的拉取请求来推荐它。

## 信任 {#trust}

安装插件即以你账户的权限运行其代码：`tern.fs` 与 `tern.process` 能够触达你能触达的
一切。安装前请阅读插件，并优先选择能在你所安装的那个提交上审阅的来源。参见
[信任与安全](../concepts/security.md)。

## 另请参见 {#see-also}

- [包与清单](../concepts/packages.md)：包的结构与清单。
- [命令行](../reference/cli.md)：完整的 `tern plugin`。
- [调试](debugging.md)：阅读安装命令打印的内容。
- [Awesome Tern](https://github.com/theblazehen/awesome-tern)：插件的社区目录。
