# 文件 block {#file-blocks}

`file` 打开文件，并驱动其文本、图像、3D 模型（OBJ、PLY、VRML）与十六进制视图。可以用它
捕获加载、编辑、磁盘冲突与 git 变更，而无需经由文件选择器导航。命令作用于聚焦的文件
block，或当前标签页中最近聚焦的文件 block；需要 block 的命令在没有时以 `no file block`
失败。

## 打开文件 {#opening-files}

| 命令 | 作用 |
| --- | --- |
| `file open <path> [split\|beside\|tab\|preview] [<line>[:<col>]] [nowait]` | 打开一个路径，可选在某个文本位置处打开。 |
| `file scratch <name> [split\|beside\|tab\|preview] [nowait]` | 把一个已提交的 fixture 复制到新的临时目录，并打开该副本。 |
| `file fixture large\|longline\|mdlong\|huge\|bin4g\|git\|gitmd\|editorconfig\|readonly [split\|beside\|tab\|preview] [nowait]` | 生成一个临时 fixture 并打开它。 |

未指定放置方式时，打开遵循 Tern 的常规放置策略。`split` 与 `beside` 是同义词；`tab`
在标签页中打开，`preview` 请求一个预览 block。放置方式、位置与 `nowait` 可以在路径之后
任意重排。若给出多个放置方式，最后一个生效。

打开通常会等待当前标签页的文件 block 完成加载、高亮并更新完 git 变更，然后稳定 350 ms。
`nowait` 跳过该等待。打开失败会使命令失败。行与列从 1 开始；省略列表示行首。

相对路径会先指向 `crates/tern/goldens/fixtures/files` 下已存在的 fixture，否则使用
[脚本](index.md#fixtures)中描述的常规 fixture/路径解析。绝对路径直接使用。`scratch`
接受一个文件名，而不是包含 `/` 的路径；在编辑、保存、覆盖或删除已提交的 fixture 之前
应先使用它。

已提交 fixture 的名称就在该目录中：`anim.gif`、`blob.bin`、`crlf.txt`、`icon.svg`、
`latin1.txt`、`links.txt`、`mixed-eol.txt`、`notes.md`、`photo.jpg`、`report.pdf`、
`sample.rs` 与 `wide.png`。

生成的 fixture：

| 名称 | 内容 |
| --- | --- |
| `large` | 一百万行类 Rust 代码，约 42 MB。 |
| `longline` | 一行 5 MB 的压缩 JavaScript。 |
| `mdlong` | 一份较长的 Markdown 文档，包含正文、列表、代码与表格。 |
| `huge` | 一个 600 MiB 的日志，超出可编辑大小限制的部分为只读。 |
| `bin4g` | 一个稀疏的 4 GiB 二进制文件，按十六进制分页，每 256 MiB 及末尾处有标记记录。 |
| `git` | 位于一个仓库中的 `sample.rs`，带有新增、修改与删除的行。 |
| `gitmd` | 位于一个仓库中的 `notes.md`，带有被修改的正文与表格行、一个被删除的列表项和一个新增的任务。 |
| `editorconfig` | 一个位于要求两个空格缩进的 `.editorconfig` 之下的文件。 |
| `readonly` | 一个没有写权限的文件。 |

大型生成的 fixture 缓存在系统临时目录中。fixture 创建或复制出错会使命令失败。打开情况
反映在 `state.file_blocks[]` 中：`path`、`host`、`kind`、`mode`、`preview` 与 `load`。
`load` 为 `opening`、进度 `{done,total}`、`ready` 或 `failed`。

## 视图、位置与搜索 {#views-positions-and-search}

| 命令 | 作用 |
| --- | --- |
| `file mode rendered\|source\|hex\|image\|model\|text` | 改变文件的显示模式。 |
| `file goto <line>[:<col>]` | 移动到从 1 开始的文本位置；列默认为 1。 |
| `file offset <byte>` | 把十六进制视图移动到十进制或 `0x` 十六进制字节偏移。 |
| `file select <a> <b> [<a> <b> …]` | 按十进制字节偏移设置文本选区；最后一对为主选区。端点相等时形成光标。 |
| `file zoom fit\|100\|actual\|<pct>[%] [<x> <y>]` | 设置图像缩放，可选以视口某点为锚。 |
| `file find "<query>" [regex] [case]` | 在文本或十六进制视图中打开搜索。 |
| `file peek <line>:<col>` | 在从 1 开始的文本位置预览链接或路径，如同强制点击。 |

`select` 至少需要一对完整的参数，并会把偏移限制在文本长度内。`offset` 需要十六进制
视图；`select` 与文本搜索需要代码视图；`zoom` 需要图像视图。不支持的视图会让这些命令
失败。数值缩放百分比必须为正；两个锚点坐标要么都给出，要么都不给。搜索默认按字面、
不区分大小写匹配。`regex` 与 `case` 可以以任意顺序出现；十六进制搜索使用 `case`，
但忽略 `regex`。用 `file wait` 等待十六进制搜索计数完成。

`peek` 在该处没有链接或路径、或没有任何可预览内容时失败。它会实时等待预览文本加载并
高亮完成。该组中的其他命令会稳定 350 ms。

状态会报告 `mode`、文本的 `caret` 与 `selections`、图像的 `zoom`，以及十六进制的
`hex.selection`、`hex.matches`、`hex.counted` 与 `hex.current`。预览或文本搜索查询
没有对应的文件 block 状态字段。

## 保存与磁盘变更 {#saving-and-disk-changes}

| 命令 | 作用 |
| --- | --- |
| `file save` | 请求保存目标 block。 |
| `file disk "<text>"` | 覆盖磁盘上的目标文件，让其监视器重新加载它或显示冲突。 |
| `file delete-on-disk` | 删除磁盘上的目标文件。 |
| `file autosave off\|focus\|<ms>` | 关闭自动保存、在焦点变化时保存，或以毫秒设置其延迟。 |

`save` 稳定 350 ms，并不一定等到保存完成；当结果重要时，随后用 `file wait saved`。
`disk` 与 `delete-on-disk` 在文件系统出错时失败，并实时等待 1.5 秒让监视器处理。这是
固定延迟，而不是检查重新加载或冲突已经到达。自动保存会改变已保存的文件偏好，而不只是
目标 block，并且不需要打开文件 block。

用 `state.file_blocks[].dirty` 与 `bar` 检查未保存的变更以及冲突、文件已删除或其他
提示。这些行中没有自动保存设置。

## 菜单与 git 变更 {#menus-and-git-changes}

| 命令 | 作用 |
| --- | --- |
| `file menu more` | 打开文件 block 的更多菜单。 |
| `file choose <action>` | 不先打开菜单就运行一个文件菜单动作。 |
| `file change <n> hover\|toggle\|revert\|stage` | 显示某个 git 变更的悬停控件、内联切换其旧行、将其作为一个可撤销编辑还原，或将其暂存。 |

动作名有 `compare`、`keep-mine`、`use-disk`、`recreate`、`close`、`discard`、
`reveal`、`open-outside`、`retry`、`save-as`、`view-hex`、`view-text`、`save`、
`revert`、`wrap`、`copy-path`、`copy-relative-path`、`create-folders` 与
`copy-markdown`。也接受这些参数形式：

| 命令 | 作用 |
| --- | --- |
| `file choose mode:rendered\|mode:source\|mode:hex\|mode:image\|mode:model\|mode:text` | 选择一个显示模式。 |
| `file choose eol:lf\|eol:crlf\|eol:cr` | 转换文档的换行符。 |
| `file choose reopen:<encoding>` | 使用某个编码标签重新打开。 |

编码标签有 `utf-8`、`utf-16le`、`utf-16be`、`windows-1252`、`iso-8859-1`、
`iso-8859-15`、`macintosh`、`windows-1250`、`windows-1251`、`koi8-r`、
`windows-1253`、`windows-1254`、`windows-1255`、`windows-1256`、`shift_jis`、
`euc-jp`、`euc-kr`、`gbk`、`gb18030` 与 `big5`。

菜单动作取决于文件的状态与视图。未知的动作名会使脚本失败，并列出有效的动作名。
`menu more` 在没有文件视图时失败。动作所请求的原生对话框或外部应用取决于平台；`file`
系列本身没有仅桌面或仅无头的限制。

git 变更索引从 0 开始。变更需要代码视图和有效的变更索引；无法暂存该变更时，暂存也会
失败。还原与暂存会等待加载、高亮与当前 git 变更；悬停与切换稳定 350 ms。状态会暴露
结果中的 `dirty`、`bar` 与 `mode`，但不包括菜单可见性、自动换行设置或 git hunk 细节。

## 等待 {#waiting}

| 命令 | 作用 |
| --- | --- |
| `file wait` | 等待当前标签页中的每个文件 block 加载、高亮、完成十六进制搜索计数并更新 git 变更。 |
| `file wait loaded` | 等待当前标签页中的每个文件 block 加载完成或失败，然后运行一帧，不等待高亮。 |
| `file wait saved` | 等待直到没有保存正在运行，且没有待处理的自动保存延迟。 |

`wait` 与 `wait loaded` 在当前标签页没有文件 block 时失败。`wait saved` 不需要。
这些等待使用实时时间以及脚本的 20 秒超时；`wait` 与 `wait saved` 还会稳定 350 ms。
加载失败也算作完成，因此应检查 `state.file_blocks[].load`，而不是把等待完成当作文件
已正确加载的证明。`wait loaded` 之后的截图仍可能等待视口高亮。

## 示例 {#examples}

编辑一个 scratch 副本并捕获外部写入冲突，如 file-conflict 场景：

```text
ready
file scratch sample.rs split
file select 0 0
type "// mine\n"
file disk "// theirs\n"
shot file-conflict
```

捕获一次正则搜索，如 file-code-find 场景：

```text
ready
file open sample.rs split
file find "Task::\\w+" regex
shot file-code-find
```

## 另见 {#see-also}

- [脚本](index.md)：运行命令、计时与 fixture 根目录。
- [文件面板](files.md)：在打开文件之前浏览目录。
- [Git Block](git.md)：处理仓库变更。
- [Harness 命令](harness.md)：输入、按键、对话框与截图。
- [调试](../guides/debugging.md)：用脚本驱动窗口。
