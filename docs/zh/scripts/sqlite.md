# SQLite block {#sqlite-blocks}

`sqlite` 打开数据库，并驱动其 Structure、Browse、Execute 与 Pragmas 区域、cell 与 plot
侧表，以及数据库对话框与工具。用它复现数据库工作流、检查查询结果，或在不逐一点击窗口的
情况下截取一个 SQLite block。

## 数据库与视图 {#databases-and-views}

| 命令 | 作用 |
| --- | --- |
| `sqlite fixture <name> [ro]` | 从已提交的 SQL 夹具构建一个全新数据库，并在聚焦面板旁打开。 |
| `sqlite open <path> [ro]` | 打开数据库或项目文件。 |
| `sqlite new <path>` | 在聚焦面板旁创建数据库，并替换该路径上已有的文件。 |
| `sqlite memory` | 打开内存数据库。 |
| `sqlite area structure\|browse\|execute\|pragmas` | 显示指定名称的区域。 |
| `sqlite sheet cell\|plot\|schema\|off` | 显示某个侧表，或将其关闭。 |
| `sqlite log on\|off` | 显示或隐藏 SQL Log。 |
| `sqlite write` | 写入待处理的数据库更改。 |
| `sqlite revert` | 回滚待处理的更改前先询问。 |
| `sqlite undo` | 撤销上一个可撤销的数据库操作。 |
| `sqlite exec <sql>` | 在可撤销的保存点中运行 SQL 语句。 |
| `sqlite close` | 通过关闭守卫关闭聚焦的 SQLite block。 |

除四个打开类命令之外，这些命令都需要一个聚焦的 SQLite block；否则会以
`no SQLite block has focus` 失败。`exec` 需要可写数据库。数据库错误可能出现在 block
中，而不是表现为命令回复失败：打开数据库或运行 SQL 后应检查其状态。

`ro` 以只读方式打开。夹具来自
`crates/tern/goldens/fixtures/sqlite/<name>.sql`；每次调用都会用一份全新副本替换其
临时数据库。`new` 同样会替换已有文件：请使用一次性的路径。回滚与存在未写入更改的关闭
都可能请求确认；用 harness 的 `dialog button <n>` 命令回答。

SQLite 命令会按真实时间等待，直到窗口中的**每个 SQLite block** 都完成打开且没有待处理
作业，然后推进 300 ms 应用时间用于绘制。共享的 20 秒超时会在工作始终无法结束时令命令
失败。确认对话框不算未完成的数据库作业，因此下一行脚本即可作答。这些并非仅限无头运行的
命令；脚本运行器可用于原生构建，浏览器构建不支持。打开默认应用或系统文件选择器需要
相应的系统集成；无头运行则改为记录这些请求。

`tern ctl state` 把 SQLite 状态存放在 `sqlite_blocks` 中：其 `blocks[]` 包含 `id`、
`name`、`path`、`memory`、`project`、`phase`、`dirty`、`can_undo`、`read_only`、
`busy`、`area`、`sheet`、`log`、`schema_seq` 与 `data_seq`。`sqlite_blocks.recent`
列出近期路径及其只读标志；`sqlite_blocks.asking` 统计待处理的数据库询问数量。下文中，
`block` 指 `sqlite_blocks.blocks[]` 中的一个条目。

## 结构 {#structure}

| 命令 | 作用 |
| --- | --- |
| `sqlite structure [sheet] open <name>` | 在 Structure 区域展开一个架构或对象。 |
| `sqlite structure [sheet] fold <name>` | 在 Structure 区域折叠一个架构或对象。 |
| `sqlite structure [sheet] select <name>[/<field>]` | 选中一行列表项。 |
| `sqlite structure [sheet] pick <name>[/<field>]` | 在选择集中切换该行的成员状态。 |
| `sqlite structure [sheet] menu` | 打开当前行的上下文菜单。 |
| `sqlite structure [sheet] browse` | 浏览选中的表或视图。 |
| `sqlite structure [sheet] modify` | 打开选中对象的编辑器。 |
| `sqlite structure [sheet] delete` | 通过其确认流程删除选中的对象。 |
| `sqlite structure [sheet] copy-create` | 复制选中对象的 CREATE SQL。 |
| `sqlite structure [sheet] copy-name` | 复制选中的名称。 |
| `sqlite structure [sheet] copy-drop` | 按当前的 drop 选项复制文本。 |
| `sqlite structure [sheet] refresh` | 重新加载架构。 |
| `sqlite structure [sheet] counts` | 切换行数显示。 |
| `sqlite structure [sheet] unfold-all` | 展开列表。 |
| `sqlite structure [sheet] fold-all` | 折叠列表。 |
| `sqlite structure [sheet] menu-key` | 运行列表的键盘菜单操作。 |
| `sqlite structure [sheet] drop-sql <sql>` | 运行拖放到 Structure 区域的 SQL 文本。 |

把 `sheet` 放在操作**之前**，以作用于 Schema 侧表。解析器也接受把它放在 `open`、`fold`
与 `drop-sql` 之前，但这三者仍作用于 Structure 区域。可接受裸对象名或带架构限定的名称。
字段行必须已经可见：先展开其所属对象。缺失的行、`menu` 遇到空选择，或操作不可用，都会
令命令失败。`pick` 切换成员状态，而不是总是将其加入。

检查 `block.structure.area` 与 `.sheet` 中的 `open`、`shut`、`selected`、`picked` 和
`rows`。`.objects` 列出架构对象，`.counts` 包含计数状态与行数，`.tools` 保存工具状态。

## 浏览 {#browse}

| 命令 | 作用 |
| --- | --- |
| `sqlite browse table <name>` | 显示表或视图。 |
| `sqlite browse select <row>:<column> [<row>:<column>]` | 选中一个单元格或矩形区域。 |
| `sqlite browse rows <first> <last>` | 选中包含首尾的整条记录范围。 |
| `sqlite browse edit <row>:<column> [<text>]` | 打开内联编辑器，可选择附带替换文本。 |
| `sqlite browse commit` | 提交已打开的内联编辑器。 |
| `sqlite browse set <row>:<column> [<text>]` | 直接写入单元格；省略文本即为空值。 |
| `sqlite browse key <id>` | 运行 Browse 键盘操作。 |
| `sqlite browse copy [headers\|sql]` | 复制选择内容，默认纯文本。 |
| `sqlite browse paste [<text>]` | 把以制表符或换行分隔的文本粘贴到网格中。 |
| `sqlite browse find <text> [case] [whole] [regex]` | 打开 Find 并执行搜索。 |
| `sqlite browse replace <replacement> [all]` | 替换当前匹配项，或替换当前 Find 搜索的所有匹配项。 |
| `sqlite browse menu <row>:<column>` | 选中一个单元格并打开其上下文菜单。 |
| `sqlite browse menu row <n>` | 选中一条记录并打开其表头菜单。 |
| `sqlite browse tab new\|close\|<n>` | 创建、关闭或选择 Data Browser 标签页。 |
| `sqlite browse goto <n>` | 滚动到某条记录。 |
| `sqlite browse jump <row>:<column>` | 跟随该单元格的外键链接。 |

行、数字列与 Browse 标签页都从 1 开始计数；把行或标签页写成 `0` 会被视为 `1`。列可写作
列名、从 1 开始的数据列序号，或表示首列的 `rowid`。表名可带架构限定。`edit`、`set` 与
`paste` 中的文本接受 `\t` 与 `\n`。包含空格的 Find 文本需加引号；其标志可出现于任意
顺序。`replace` 只接受替换文本，不接受另一个搜索词。表缺失、列缺失、未知操作 ID，以及
复制空选择，都会令命令失败。

下面每个操作 ID 都可以在 `sqlite browse key` 之后使用：

| 命令 | 作用 |
| --- | --- |
| `refresh` | 重新读取行。 |
| `previous_table`, `next_table` | 浏览上一个或下一个表，并循环。 |
| `new_tab`, `rename_tab`, `close_tab` | 创建 Data Browser 标签页、请求重命名或关闭。 |
| `new_record` | 使用默认值插入一条记录。 |
| `insert_values` | 打开 Add Record。 |
| `delete_records`, `duplicate_record` | 删除或复制选中的记录。 |
| `copy_above` | 以上方单元格的值开始编辑。 |
| `set_null`, `clear_cells` | 把选中的单元格设为 NULL 或空值。 |
| `delete` | 删除选中的整条记录，否则清空选中的单元格。 |
| `cut`, `copy_headers`, `copy_sql` | 剪切或复制选择内容。 |
| `select_all` | 加载并选中所有单元格。 |
| `edit_cell` | 在 cell 侧表中打开当前单元格。 |
| `find`, `replace` | 打开 Find，或打开 Find and Replace。 |
| `find_next`, `find_previous` | 在匹配项之间移动。 |
| `replace_next`, `replace_all` | 使用 Find 栏替换一个或所有匹配项。 |
| `adjust_rows` | 切换加高并换行的行。 |
| `first_page`, `previous_page`, `next_page`, `last_page` | 在页面之间导航。 |
| `goto_row` | 请求输入记录编号。 |

下一张表中的列 ID 同样可以在 `key` 之后使用。列设置、过滤器与格式属于 Browse，而不是
单独的命令前缀：

| 命令 | 作用 |
| --- | --- |
| `sqlite browse filter <column> [<text>]` | 设置或清除列过滤器。 |
| `sqlite browse global [<text>]` | 设置或清除全局过滤器。 |
| `sqlite browse sort <column> [add]` | 循环切换该列的排序；`add` 保留其他排序列。 |
| `sqlite browse hide <column>` | 隐藏一列。 |
| `sqlite browse show-all` | 显示所有隐藏的列。 |
| `sqlite browse rowid [on\|off]` | 显示 rowid 列，或用 `off` 将其隐藏。 |
| `sqlite browse freeze <column>\|off` | 冻结到某一列为止，或取消冻结。 |
| `sqlite browse width <column> <px>` | 以像素设置列宽。 |
| `sqlite browse format <column> [<preset-or-expression>]` | 设置显示预设，或打开自定义表达式编辑器并校验表达式。 |
| `sqlite browse format-dialog <column>` | 打开显示格式对话框。 |
| `sqlite browse condformat <column> [<filter>]` | 基于过滤器添加条件格式。 |
| `sqlite browse condformats <column>` | 打开条件格式管理器。 |
| `sqlite browse condformats-add` | 在管理器中按下 Add。 |
| `sqlite browse condformats-save` | 保存管理器的更改。 |
| `sqlite browse fmt bold\|italic\|underline\|left\|center\|right\|justify\|clear` | 更改选择内容的格式。 |
| `sqlite browse fmt fg\|bg [<hex>]` | 设置前景色或背景色。 |
| `sqlite browse fmt font [<name>]` | 设置格式字体。 |
| `sqlite browse fmt size <n>` | 设置格式字号。 |
| `sqlite browse select-col <column>` | 选中整列。 |
| `sqlite browse findcol [<text>]` | 打开列搜索并查找名称。 |
| `sqlite browse findcol-next`, `sqlite browse findcol-prev` | 在匹配的列之间移动。 |
| `sqlite browse unlock [<column>[,<column>...]]` | 为编辑视图校验伪主键；空列表则将其锁定。 |
| `sqlite browse lock` | 锁定视图编辑。 |
| `sqlite browse encoding [all] [<name>]` | 设置此表或所有表的文本编码。 |
| `sqlite browse saveview [<name>]` | 为经过过滤与排序的查询创建视图。 |
| `sqlite browse header-menu <column>` | 打开列头菜单。 |
| `sqlite browse filter-menu <column>` | 打开过滤器字段的菜单。 |
| `sqlite browse filter-help` | 打开过滤器语法帮助。 |

`width` 接受 0 到 65535 的无符号整数。`rowid` 默认为开启；只有 `off` 会将其隐藏。
`format ... default` 移除已保存的显示格式。预设键区分大小写：`decimal`、`exponent`、
`hexblob`、`hex`、`octal`、`round`、`appleDate`、`javaEpoch`、`dotNetTicks`、`julian`、
`epoch`、`epochLocalTime`、`webkitEpoch`、`webkitEpochLocalTime`、`winDate`、
`ddmmyyyyDate`、`lower`、`upper`、`guid`、`geomToSVG` 与 `json`。其他文本按自定义
表达式处理。显示格式需要数据列，不能用于 `rowid`。

这些列操作 ID 也可直接以 `sqlite browse <id>`（不带参数）运行，或通过
`sqlite browse key <id>` 运行：

| 命令 | 作用 |
| --- | --- |
| `clear_filters`, `clear_sorting` | 清除过滤器或排序顺序。 |
| `focus_filter`, `global_filter` | 聚焦当前列的过滤器或全局过滤器。 |
| `find_column` | 打开列搜索。 |
| `show_rowid`, `freeze_columns` | 切换 rowid 可见性，或冻结到当前列。 |
| `hide_columns`, `show_all_columns` | 隐藏选中的列，或显示所有列。 |
| `select_column` | 选中当前列。 |
| `unlock_view` | 打开伪主键提示，或锁定已解锁的视图。 |
| `display_format`, `cond_formats` | 打开当前列的格式对话框。 |
| `encoding_all` | 请求为所有表指定编码。 |
| `copy_column_name` | 复制当前列的名称。 |
| `format_toolbar` | 切换格式工具栏。 |
| `bold`, `italic`, `underline` | 切换选择内容的文字样式。 |
| `align_left`, `align_center`, `align_right`, `align_justify` | 设置选择内容的对齐方式。 |
| `clear_format` | 清除选择内容的格式。 |
| `save_as_view` | 请求输入视图名称。 |
| `export_csv`, `export_json` | 为经过过滤与排序的行打开导出。 |
| `sqlite browse key encoding` | 请求为此表指定编码；直接使用 `encoding` 则是上文中的设置命令。 |

不可用的直接列操作会以 `can't run now` 失败；编辑仍遵循网格的只读与选择规则。检查
`block.browse` 中的 `tabs`、`current`、`table`、`sql`、`count`、`loaded`、`selection`、
`cell`、`editing`、`find` 与 `error`。`.columns` 包含 `filters`、`global`、`where`、
`sort`、`hidden`、`frozen`、`show_rowid`、`widths`、`display_formats`、`cond_formats`、
`row_id_formats`、`encoding`、`pseudo_pk`、`editable`、`toolbar`、`find_column`、
`dialog` 与 `cond_editor`。

```text
ready
sqlite fixture sample
sqlite area browse
sqlite browse table tracks
sqlite browse filter milliseconds 200000~400000
sqlite browse filter name e
sqlite browse global o
sqlite browse sort price
sqlite browse sort name add
sqlite browse freeze name
sqlite browse condformat price >1
sqlite browse select 2:5
shot sqlite-browse-filters
```

## 执行 {#execute}

| 命令 | 作用 |
| --- | --- |
| `sqlite execute new [<title>]` | 创建一个 SQL 标签页。 |
| `sqlite execute text [<text>]` | 替换当前标签页的 SQL，并把光标留在末尾。 |
| `sqlite execute type <text>` | 在光标处输入，并像手动输入那样触发补全。 |
| `sqlite execute caret <n>` | 把光标置于某个字节偏移处。 |
| `sqlite execute select <from> <to>` | 选中一个字节范围。 |
| `sqlite execute run` | 执行全部 SQL，或执行选择内容。 |
| `sqlite execute line` | 执行光标所在行的语句。 |
| `sqlite execute stop` | 停止执行。 |
| `sqlite execute tab <n>` | 选择一个 SQL 标签页。 |
| `sqlite execute close` | 关闭当前标签页，必要时先询问。 |
| `sqlite execute rename <title>` | 重命名当前标签页。 |
| `sqlite execute duplicate` | 复制当前标签页。 |
| `sqlite execute move <from> <to>` | 调整 SQL 标签页的顺序。 |
| `sqlite execute complete` | 在光标处打开补全。 |
| `sqlite execute accept` | 插入选中的补全项。 |
| `sqlite execute pick <n>` | 选中一行补全项。 |
| `sqlite execute open <path>` | 把 SQL 文件打开到标签页中。 |
| `sqlite execute save <path>` | 把当前标签页的 SQL 保存到文件。 |
| `sqlite execute view <name>` | 把结果对应的查询保存为视图。 |
| `sqlite execute cell <row> <column>` | 选中一个结果单元格。 |
| `sqlite execute copy [plain\|headers\|sql]` | 复制选中的结果，默认纯文本。 |
| `sqlite execute tiling on\|off` | 把结果放在编辑器旁边，或放在其下方。 |
| `sqlite execute zoom in\|out\|reset` | 更改编辑器缩放。 |
| `sqlite execute focus editor\|results` | 移动键盘焦点。 |
| `sqlite execute chord <id>` | 运行 Execute 键盘操作。 |
| `sqlite execute log-source user\|app\|error` | 选择 SQL Log 的来源。 |
| `sqlite execute log-find <query>` | 搜索已打开的 SQL Log。 |

标签页、补全行、结果行与结果列都**从 0 开始计数**，这一点与 Browse 不同。光标与选择的
偏移以字节计。`text` 与 `type` 接受 `\n` 与 `\t`。所有 Execute 命令都需要已打开的
数据库；需要当前 SQL 标签页的命令在没有标签页时失败。未知标签页、没有选中结果却执行复制，
或搜索已关闭的 SQL Log，也会失败。查询失败会显示在标签页的消息与诊断中。与其他 SQLite
命令一样，执行会等待作业结束；按顺序排列的 `stop` 行无法中断仍在等待的前一条 `run`。

| 命令 | 作用 |
| --- | --- |
| `execute`, `execute_line`, `stop` | 运行全部或选中的 SQL、运行当前行，或停止。 |
| `new_tab`, `open_file` | 创建标签页，或请求选择 SQL 文件。 |
| `save_file`, `save_file_as` | 保存 SQL，必要时请求输入路径。 |
| `close_tab`, `rename_tab`, `duplicate_tab` | 关闭标签页、请求重命名或复制标签页。 |
| `next_tab`, `previous_tab` | 切换当前 SQL 标签页。 |
| `focus_editor`, `focus_results` | 移动焦点。 |
| `complete` | 打开补全。 |
| `zoom_in`, `zoom_out`, `zoom_reset` | 更改编辑器缩放。 |
| `copy_with_headers`, `copy_as_sql` | 复制选中的结果。 |
| `export_csv`, `export_json` | 打开结果导出。 |
| `save_as_view` | 请求输入视图名称。 |
| `toggle_tiling` | 切换结果放在编辑器旁边。 |

检查 `block.execute.tabs[]` 中的 SQL 文本、文件、修改状态、光标、消息、错误、结果与
诊断；`.current`、`.running`、`.zoom`、`.completion` 与 `.log` 描述该区域的其余部分。
`block.log` 报告日志是否已打开。结果并排是已保存的偏好，而不是专门的状态字段。

```text
ready
sqlite fixture sample
sqlite area execute
sqlite execute text SELECT a.title, ar.name AS artist, a.released\nFROM albums a\nJOIN artists ar ON ar.id = a.artist_id\nORDER BY a.released;
sqlite execute run
sqlite execute cell 0 0
sqlite execute tiling on
sqlite log on
shot sqlite-execute-tiled
sqlite execute log-find albums
shot sqlite-execute-log-find
```

## 编译指示（Pragmas） {#pragmas}

| 命令 | 作用 |
| --- | --- |
| `sqlite pragmas set <name> <value>` | 在表单中编辑一个 pragma。 |
| `sqlite pragmas save` | 应用已编辑的 pragma 值。 |
| `sqlite pragmas reset` | 放弃表单中的编辑。 |
| `sqlite pragmas refresh` | 重新读取 pragma 值。 |

`set` 需要可写数据库，且名称必须是表单中提供的项：`page_size`、`auto_vacuum`、
`max_page_count`、`temp_store`、`secure_delete`、`journal_mode`、`journal_size_limit`、
`wal_autocheckpoint`、`synchronous`、`locking_mode`、`fullfsync`、
`checkpoint_fullfsync`、`foreign_keys`、`recursive_triggers`、
`ignore_check_constraints`、`case_sensitive_like`、`automatic_index` 或 `user_version`。

选项值接受其存储值或显示标签，且不区分大小写：

- `auto_vacuum`：`0`/`None`、`1`/`Full`、`2`/`Incremental`。
- `journal_mode`：`Delete`、`Truncate`、`Persist`、`Memory`、`WAL`、`Off`。
- `locking_mode`：`Normal`、`Exclusive`。
- `page_size`：`512`、`1024`、`2048`、`4096`、`8192`、`16384`、`32768`、`65536`，
  或它们的标签（`512 bytes`、`1 KiB`，直到 `64 KiB`）。
- `synchronous`：`0`/`Off`、`1`/`Normal`、`2`/`Full`、`3`/`Extra`。
- `temp_store`：`0`/`Default`、`1`/`File`、`2`/`Memory`。

复选框值只有在对确切词语 `1`、`on` 或 `true` 时才视为开启；其他任何内容都表示关闭。
数字类表单值会传给表单进行校验。`fullfsync` 与 `checkpoint_fullfsync` 影响 macOS 同步。
检查 `block.pragmas.values`、`.edits`、`.read`、`.reading` 与 `.error`。

## 单元格 {#cell}

| 命令 | 作用 |
| --- | --- |
| `sqlite cell load <table> <rowid> <column>` | 从 `main` 中的表加载单元格，并打开 Edit Cell 侧表。 |
| `sqlite cell mode text\|rtl\|binary\|image\|json\|xml\|svg\|evaluation` | 更改编辑器模式。 |
| `sqlite cell type [<text>]` | 替换文本编辑器的内容。 |
| `sqlite cell hex-goto <offset>` | 移动十六进制光标；接受十进制与 `0x` 十六进制。 |
| `sqlite cell hex-type <digits>` | 在二进制编辑器中输入十六进制数字。 |
| `sqlite cell apply` | 应用缓冲区中的值。 |
| `sqlite cell null` | 把缓冲区设为 NULL。 |
| `sqlite cell discard` | 放弃缓冲区中的编辑。 |
| `sqlite cell import <path>` | 把文件内容导入缓冲区。 |
| `sqlite cell import-ref <path>` | 导入文件引用。 |
| `sqlite cell export <path>` | 导出单元格内容。 |
| `sqlite cell export-dump <path>` | 导出十六进制/ASCII 转储。 |
| `sqlite cell external` | 写出临时文件，用其默认应用打开并监视更改。 |
| `sqlite cell external-apply` | 读回外部文件，应用其内容并删除该文件。 |
| `sqlite cell external-cancel` | 停止监视并删除临时文件。 |
| `sqlite cell open-default` | 在默认应用中打开该值的 URL 或已存在的文件。 |
| `sqlite cell copy-hex` | 复制十六进制/ASCII 表示。 |
| `sqlite cell auto-switch on\|off` | 设置自动选择模式。 |
| `sqlite cell wrap on\|off` | 设置编辑器自动换行。 |
| `sqlite cell format on\|off` | 设置结构化文本格式化。 |
| `sqlite cell sort-keys on\|off` | 设置 JSON 键排序。 |
| `sqlite cell overwrite on\|off` | 设置二进制覆盖模式。 |

除 `load` 之外的每个命令都需要已加载的单元格。rowid 是数据库中有符号的实际 rowid，而不是
Browse 中显示的行号。`type` 需要可编辑的文本模式；`hex-type` 需要可编辑的二进制模式。
Apply 可能就无效的结构化文本或待处理的编辑发起询问；用 `dialog button <n>` 回答由此
产生的系统对话框。外部文件的更改按应用时间每秒检查一次；`external` 不会等待其他应用
完成编辑。没有监视任何文件时，external apply/cancel 不执行任何操作。

检查 `block.cell.cell` 中的来源、表、行、列、键与值类别；`.mode`、`.read_only`、`.why`、
`.modified`、`.null`、`.text`、`.invalid`、`.diagnostics`、`.hex`、`.overwrite`、
`.evaluating`、`.external` 与 `.asking` 描述编辑器。状态文本限制为 4000 个字符。四个
编辑器偏好没有专门的状态字段。

## 绘图 {#plot}

| 命令 | 作用 |
| --- | --- |
| `sqlite plot x <column>` | 设置 X 列；`Row #` 表示使用行号。 |
| `sqlite plot y1\|y2 <column>` | 在左或右 Y 轴上切换一列。 |
| `sqlite plot color y1\|y2 <hex> <column>` | 设置某个序列的颜色。 |
| `sqlite plot line <style>` | 设置线条样式。 |
| `sqlite plot point <shape>` | 设置点形状。 |
| `sqlite plot legend on\|off` | 设置图例可见性。 |
| `sqlite plot stacked on\|off` | 设置堆叠柱状图。 |
| `sqlite plot fixed on\|off` | 设置固定数字格式。 |
| `sqlite plot log-x on\|off` | 设置 X 轴的对数缩放。 |
| `sqlite plot log-y on\|off` | 设置 Y 轴的对数缩放。 |
| `sqlite plot load-all` | 加载所有源行用于绘图。 |
| `sqlite plot hover <row>` | 显示某个源行第一个有限点的读数。 |
| `sqlite plot pick <row>` | 在网格中选中该点的源行。 |
| `sqlite plot zoom <percent>` | 缩放当前范围；低于 100 表示放大。 |
| `sqlite plot reset` | 重置绘图缩放。 |
| `sqlite plot save <path>` | 写出图像，按扩展名选择格式。 |
| `sqlite plot copy` | 复制绘图图像。 |

选定 Browse 表或 Execute 结果之后，用 `sqlite sheet plot` 打开绘图。列名必须存在于绘图
中。`hover` 与 `pick` 使用的源行号**从 0 开始计数**；没有已绘制的有限点的行会失败。
`zoom` 需要正整数百分比。无效的颜色、样式与形状在解析阶段失败。

样式（不区分大小写）：`None`、`Line`、`StepLeft`、`StepRight`、`StepCenter`、`Impulse`。
形状（不区分大小写）：`None`、`Cross`、`Plus`、`Circle`、`Disc`、`Square`、`Diamond`、
`Star`、`Triangle`、`TriangleInverted`、`CrossSquare`、`PlusSquare`、`CrossCircle`、
`PlusCircle`、`Peace`。`Dot` 不是可选用的脚本形状。默认样式为 Line 配 Disc 标记，除非
偏好设置将其覆盖。保存支持 PNG、BMP、JPG/JPEG、SVG 与 PDF；扩展名未知或缺失时会追加
`.png`。

检查 `block.plot.source`、`.columns`、`.x`、`.y1`、`.y2`、`.options`、`.rows`、
`.loaded`、`.total`、`.bars`、`.sorted`、`.x_type`、`.drawn`、`.x_ticks`、`.zoomed`、
`.selected`、`.line`、`.point` 与 `.hover`。

## 对话框 {#dialogs}

| 命令 | 作用 |
| --- | --- |
| `sqlite dialogs create-table` | 打开 Create Table。 |
| `sqlite dialogs edit-table <name>` | 打开 Edit Table。 |
| `sqlite dialogs create-index [<table>]` | 打开 Create Index，可选择作用于某个表。 |
| `sqlite dialogs edit-index <name>` | 打开 Edit Index。 |
| `sqlite dialogs add-record <table>` | 打开 Add Record。 |
| `sqlite dialogs import-csv <path>...` | 为一个或多个文件打开 CSV 导入。 |
| `sqlite dialogs import-csv-text <text>` | 为剪贴板式文本打开 CSV 导入。 |
| `sqlite dialogs import-sql <path> [new <database-path>]` | 把 SQL 文件导入此数据库或一个新数据库。 |
| `sqlite dialogs export-csv [<table>...]` | 打开 CSV 导出。 |
| `sqlite dialogs export-json [<table>...]` | 打开 JSON 导出。 |
| `sqlite dialogs export-query csv\|json <sql>` | 为一条 SQL 查询打开导出。 |
| `sqlite dialogs export-sql [<table>...]` | 打开 SQL 导出。 |
| `sqlite dialogs accept [<path>]` | 按下当前打开对话框的主要操作；导出会使用提供的目标位置，而不是发起询问。 |
| `sqlite dialogs cancel` | 关闭当前打开的对话框。 |

`sqlite dialogs` 之后的其他词会作用于当前打开的对话框。下面的各表都使用同一前缀；它们
并不嵌套在 `edit-table`、`import-csv` 等之下。对话框不匹配的命令、缺失的对象、越界的
行号，以及对话框未打开，都会失败。对话框行号从 1 开始计数，且必须存在。此区域中的布尔
参数接受 `on|yes|true` 或 `off|no|false`。

包含空格的路径、名称、CSV 文本与 SQL 需要加引号；打开类命令各把每一项视为一个参数。
省略导出表列表会打开选择器，而不是要求在脚本中提供列表。Accept 可能因校验错误或数据库
错误而让对话框保持打开；import 可能就已存在的表发起询问。继续之前应先检查对话框。

### 创建与编辑表 {#create-and-edit-table}

| 命令 | 作用 |
| --- | --- |
| `sqlite dialogs name [<name>]` | 设置表名。 |
| `sqlite dialogs schema <name>` | 选择一个可用的架构。 |
| `sqlite dialogs without-rowid on\|off` | 设置 WITHOUT ROWID。 |
| `sqlite dialogs strict on\|off` | 设置 STRICT 模式。 |
| `sqlite dialogs conflict none\|rollback\|abort\|fail\|ignore\|replace` | 设置主键冲突处理动作。 |
| `sqlite dialogs tab fields\|constraints` | 显示字段或表约束。 |
| `sqlite dialogs add-field` | 添加一个字段。 |
| `sqlite dialogs remove-field <n>` | 删除一个字段。 |
| `sqlite dialogs move-field <n> up\|down\|top\|bottom` | 调整字段的顺序。 |
| `sqlite dialogs select <n>` | 选中一行字段。 |
| `sqlite dialogs field <n> name\|type\|default\|check\|collation [<text>]` | 编辑字段的某项属性。 |
| `sqlite dialogs field <n> nn\|pk\|ai\|unique on\|off` | 设置非空、主键、自增或唯一。 |
| `sqlite dialogs field <n> fk [none\|<table> [<column> [<clauses>...]]]` | 清除或设置内联外键目标。 |
| `sqlite dialogs add-pk` | 添加主键约束。 |
| `sqlite dialogs add-unique` | 添加唯一约束。 |
| `sqlite dialogs add-fk` | 添加外键约束。 |
| `sqlite dialogs add-check` | 添加 CHECK 约束。 |
| `sqlite dialogs key <n> columns <column>[,<column>...]` | 设置某个键的列。 |
| `sqlite dialogs key <n> kind pk\|unique` | 更改键的类型；除 `pk` 之外的任何词都选择唯一。 |
| `sqlite dialogs key\|fk\|check <n> name [<text>]` | 为约束命名。 |
| `sqlite dialogs fk <n> columns <column>[,<column>...]` | 设置外键的源列。 |
| `sqlite dialogs fk <n> references [none\|<table> [<column> [<clauses>...]]]` | 清除或设置外键目标。 |
| `sqlite dialogs check <n> expr [<expression>]` | 设置 CHECK 表达式。 |
| `sqlite dialogs remove-key\|remove-fk\|remove-check <n>` | 删除该类型的约束。 |
| `sqlite dialogs popover key\|fk-columns\|fk\|field-fk <n>` | 在已显示的行上打开列选择器或外键选择器。 |
| `sqlite dialogs columns <column>[,<column>...]` | 在打开的列选择器中应用列。 |

键、外键与检查约束各自独立编号。空的列列表参数会清空列表。省略外键目标会将其清除。可在
目标列之后使用 `ON DELETE CASCADE` 之类的子句。选择器行必须在当前标签页中显示。只有
`constraints` 会选择约束标签页；其他词都选择字段。重复的字段、无效的主键组合，以及对
被引用列的禁止修改，可能立即失败；无效的表定义也会在 accept 时报告。

### 创建与编辑索引 {#create-and-edit-index}

| 命令 | 作用 |
| --- | --- |
| `sqlite dialogs name [<name>]` | 设置索引名。 |
| `sqlite dialogs table [<name>]` | 选择一个提供的表。 |
| `sqlite dialogs unique on\|off` | 设置唯一性。 |
| `sqlite dialogs where [<expression>]` | 设置或清除部分索引条件。 |
| `sqlite dialogs add <column>` | 添加一个可用的表列。 |
| `sqlite dialogs add-expr [<expression>]` | 添加一个表达式行。 |
| `sqlite dialogs remove <n>` | 删除一个索引行。 |
| `sqlite dialogs order <n> asc\|desc\|none` | 设置或清除某行的排序顺序；空字符串也会将其清除。 |
| `sqlite dialogs expr <n> [<expression>]` | 编辑一个表达式行。 |
| `sqlite dialogs up\|down <n>` | 调整某行的顺序。 |

表与列的匹配不区分大小写。对普通列行使用 `expr` 会失败。接受需要有效的名称、表与索引
内容。

### 添加记录 {#add-record}

| 命令 | 作用 |
| --- | --- |
| `sqlite dialogs value <n> [<text>]` | 设置某个列值；空文本会恢复其默认值。 |
| `sqlite dialogs null <n>` | 把某列设为 NULL。 |
| `sqlite dialogs empty <n>` | 设置显式的空字符串。 |
| `sqlite dialogs default <n>` | 恢复某列的默认值。 |
| `sqlite dialogs restore` | 恢复所有默认值。 |

生成列不能赋值。约束失败会让对话框保持打开，以便修正其中的值并再次接受。

### CSV 导入 {#csv-import}

| 命令 | 作用 |
| --- | --- |
| `sqlite dialogs header\|trim\|separate\|no-types\|local\|fail-missing\|ignore-defaults\|sanitize on\|off` | 设置对应的导入选项。 |
| `sqlite dialogs advanced on\|off` | 显示或隐藏高级选项。 |
| `sqlite dialogs separator comma\|semicolon\|tab\|pipe\|<character>` | 设置字段分隔符。 |
| `sqlite dialogs separator other <character>` | 使用自定义分隔符。 |
| `sqlite dialogs separator code <n>` | 使用字符编码；0 表示无分隔符。 |
| `sqlite dialogs quote double\|single\|none\|<character>` | 设置引号字符。 |
| `sqlite dialogs quote other <character>` | 使用自定义引号字符。 |
| `sqlite dialogs quote code <n>` | 使用字符编码；0 表示不使用。 |
| `sqlite dialogs encoding <name>` | 选择 UTF-8、UTF-16、ISO-8859-1 或其他具名编码。 |
| `sqlite dialogs conflict abort\|ignore\|replace` | 设置冲突记录的处理方式。 |
| `sqlite dialogs table <name>` | 设置目标名称，或在分表模式下设置当前文件的名称。 |
| `sqlite dialogs file <n>` | 选择用于预览的文件。 |
| `sqlite dialogs file <n> table <name>` | 设置某个文件的目标表。 |
| `sqlite dialogs file <n> on\|off` | 包含或排除某个文件。 |
| `sqlite dialogs all on\|off` | 包含或排除所有文件。 |
| `sqlite dialogs match-similar` | 选择结构相似的文件。 |
| `sqlite dialogs answer yes\|no\|all\|cancel` | 回答当前关于已存在表的问题。 |

字面分隔符与引号必须为单个字符。字符编码是无符号十进制数字。自定义的 `other` 值可以为
空，表示不使用。错误的编码名称会在预览中显现。仅在有待回答的问题时可使用 `answer`，
否则失败；`all` 会对所有剩余问题回答 Yes。

### CSV 与 JSON 导出 {#csv-and-json-export}

| 命令 | 作用 |
| --- | --- |
| `sqlite dialogs select <name> on\|off` | 包含或排除列出的表。 |
| `sqlite dialogs all`, `sqlite dialogs none` | 选中所有表或不选任何表。 |
| `sqlite dialogs header on\|off` | 设置 CSV 列标题。 |
| `sqlite dialogs separator ,\|;\|tab` | 设置 CSV 分隔符。 |
| `sqlite dialogs separator "\|"` | 使用字面竖线作为 CSV 分隔符。 |
| `sqlite dialogs separator other [<character>]` | 设置自定义 CSV 分隔符。 |
| `sqlite dialogs quote "\|'\|none` | 设置 CSV 引号字符；字面双引号需作为脚本字符串加引号。 |
| `sqlite dialogs quote other [<character>]` | 设置自定义 CSV 引号。 |
| `sqlite dialogs newline crlf\|lf` | 设置 CSV 行尾。 |
| `sqlite dialogs newline other [<text>]` | 设置自定义 CSV 行尾。 |
| `sqlite dialogs pretty on\|off` | 设置 JSON 美化输出。 |

CSV 相关控件在 JSON 导出中会失败，`pretty` 在 CSV 导出中会失败。查询导出没有表选择器，
因此在其中 `select`、`all` 与 `none` 会失败。

### SQL 导出 {#sql-export}

| 命令 | 作用 |
| --- | --- |
| `sqlite dialogs select <name> on\|off` | 包含或排除列出的表。 |
| `sqlite dialogs all`, `sqlite dialogs none` | 选中所有表或不选任何表。 |
| `sqlite dialogs what everything\|schema\|data` | 选择转储内容。 |
| `sqlite dialogs column-names on\|off` | 在 INSERT 语句中包含列名。 |
| `sqlite dialogs multi-row on\|off` | 在多行 INSERT 语句中合并记录。 |
| `sqlite dialogs keep-original on\|off` | 保留原始 CREATE SQL。 |
| `sqlite dialogs keep-schema on\|off` | 保留原始架构名称。 |

`block.dialogs.open` 标识对话框；`.dialog` 包含其字段、选项、预览、选择与校验状态。
`.job` 报告进度，`.popover` 描述已打开的选择器。对于导入，发送回答前应检查对话框的
问题与剩余文件。

## 工具 {#tools}

| 命令 | 作用 |
| --- | --- |
| `sqlite tools compact` | 打开 Compact 对话框。 |
| `sqlite tools integrity` | 运行完整的完整性检查。 |
| `sqlite tools quick-check` | 运行快速完整性检查。 |
| `sqlite tools fk-check` | 检查外键。 |
| `sqlite tools optimize` | 运行 SQLite 优化。 |
| `sqlite tools row-counts` | 在新的 Execute 标签页中运行查询，列出各表与视图的行数。 |
| `sqlite tools save-project` | 保存项目，必要时请求输入路径。 |
| `sqlite tools save-all` | 保存数据库与项目。 |
| `sqlite tools close-project` | 关闭关联的项目。 |
| `sqlite tools detach-menu` | 分离唯一已附加的数据库，存在多个时则打开菜单。 |
| `sqlite tools save-project-as-dialog` | 请求输入新的项目目标位置。 |
| `sqlite tools save-database-as-dialog` | 请求输入数据库副本的目标位置。 |
| `sqlite tools pick <schema> on\|off` | 在 Compact 中设置某个架构的复选框。 |
| `sqlite tools alias <name>` | 设置 Attach 对话框的别名。 |
| `sqlite tools ok` | 运行当前打开的 Compact 或 Attach 对话框。 |
| `sqlite tools cancel` | 关闭工具类对话框。 |
| `sqlite tools load-extension <path>` | 加载 SQLite 扩展。 |
| `sqlite tools attach <path>` | 为该数据库文件打开 Attach；`:memory:` 会附加内存数据库。 |
| `sqlite tools detach <name>` | 分离某个数据库别名。 |
| `sqlite tools open-project <path>` | 打开项目文件。 |
| `sqlite tools save-project-as <path>` | 把项目保存到某个路径，必要时追加项目扩展名。 |
| `sqlite tools save-database-as <path>` | 把数据库复制到新文件。 |
| `sqlite tools drop select\|insert\|names` | 选择删除架构对象时生成的文本。 |
| `sqlite tools drop qualified\|quoted` | 切换生成的 drop 文本中的架构限定或名称加引号。 |

Compact 需要可写数据库。检查、优化与行数统计需要一个已打开的数据库。保存项目需要已打开
且基于文件的数据库；关闭项目需要有已关联的项目文件。存在未写入的更改时，Save Database As
不可用。不可用的操作会以 `can't run now` 失败。`pick`、`alias` 与 `ok` 在没有对应对话框
时失败。与数据库对话框的布尔别名不同，工具中的 `pick` 只接受 `on` 或 `off`。没有工具类
对话框时，`cancel` 不产生任何影响。

检查 `block.structure.tools.tasks`、`.compact` 与 `.attach`，以了解作业与对话框；
`.compact` 列出 Compact 提供的架构，而不只是已勾选的架构。`block.project`、`.path`、
`.dirty` 与 `.structure.objects` 反映项目、文件与附加操作。检查、优化与 `row-counts`
会打开 Execute 标签页；检查 `block.execute.tabs[].results` 获取其输出。drop 文本偏好
没有专门的状态字段。

## 另见 {#see-also}

- [脚本](index.md)：运行、计时、夹具与共享语法。
- [Harness 命令](harness.md)：确认对话框、输入与截取。
- [控制命令](control.md)：检查状态、树与布局。
- [文件面板](files.md)：从列表打开数据库文件。
- [调试](../guides/debugging.md)：通过脚本驱动窗口。
