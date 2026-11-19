# 自定义主题 {#custom-themes}

Tern 使用 omp 的主题，也可以用 CSS 自己编写主题。每个主题要么是浅色，要么是深色，
Tern 会各选一个：窗口为深色时用深色主题，为浅色时用浅色主题（Settings › Appearance ›
Appearance）。添加主题后，用 **Change theme…**（macOS 上为 ⌃⌘T，其他平台为
Ctrl+Shift+M）选择它，或在 Settings › Appearance › Theme 中选择。

```css
@import "dark-gruvbox";

:root {
	--tv-bg: #1d2021;
	--accent: #fe8019;
	--omp-mdHeading: #fabd2f;
}

[role='tab'][aria-selected='true'] {
	font-weight: 600;
}
```

把它保存为 `<config>/themes/campfire.css`，选择器中就会出现一个名为 `campfire` 的
深色主题：gruvbox 配更深的终端、橙色强调色、omp 聊天中的黄色标题，以及加粗的当前
标签页。

## CSS 主题 {#css-themes}

CSS 主题建立在另一个主题之上，并把自身的规则叠加在它上面。

- **基础主题。** 开头的 `@import "<theme>";` 指明它建立在哪个主题上：内置主题、omp 的
  主题，或另一个 CSS 主题，用选择器显示的名称指定。没有这一行时，它建立在 omp 为其
  外观准备的默认主题上（深色为 `titanium`，浅色为 `light`）。
- **浅色或深色。** `:root` 规则中的 `color-scheme: light` 或 `color-scheme: dark`
  决定它的外观；没有这一项时继承基础主题的外观，两者都没有时为深色。
  `light-dark(<light>, <dark>)` 值会取当前所示外观对应的那一侧。
- **所有规则都优先。** 每条声明都算作 `!important`，而且样式表排在 Tern 与所有插件的
  样式表之后，因此任何优先级的规则都能胜过它们。只有行内 `!important` 能胜过它。
- **该设置什么。** 在 `:root` 上设置 Tern 绘制所用的变量：终端的 `--tv-bg`、`--tv-fg`、
  `--tv-cur` 与 `--ansi0` … `--ansi15`，界面的 `--page`、`--accent`、`--ink`、
  `--t1` … `--t4`、`--ok`、`--bad` 与 `--warn`，高亮代码的 `--tk-*`，以及 omp 聊天的
  颜色 `--omp-<token>`。[CSS 变量](../styles/variables.md) 列出了全部变量。面板跟随
  `--tv-bg`，细线与 chip 填充跟随 `--ink`。其他任何规则都会重新设置其选中内容的样式。
- **CSS 之外。** 选择器中的色块，以及程序向终端查询颜色（OSC 4、10、11 与 12）时得到
  的颜色，来自主题在 `@media` 之外的裸 `:root` 规则：`--tv-bg`、`--tv-fg`、
  `--tv-cur`、`--tv-cur-ink`、`--accent` 与 `--ansi0` … `--ansi15`，取值为颜色、
  `light-dark()` 或另一个变量的 `var()`。Tern 按原样使用它们，不做它针对 omp 主题
  所做的可读性调整。
- **链。** 建立在另一个主题之上的 CSS 主题会得到两张样式表，基础主题的在前，并且可以
  使用基础主题的 `:root` 变量。

## 主题的存放位置 {#where-themes-live}

| 文件夹 | 内容 | 读取时机 |
| --- | --- | --- |
| `<config>/themes/`，与 `settings.json` 同目录 | Tern 的 CSS 主题，`<name>.css` | 始终读取。 |
| Tern 应用存储中的 `Documents/Themes`，与 `Plugins` 同目录（iOS 上为 Files 应用的 On My iPhone 或 iPad › Tern › Themes） | Tern 的 CSS 主题 | iOS 与 Android 上，替代 `<config>/themes/`。 |
| omp 的 `themes/`：`~/.omp/agent/themes/`，或具名 omp 配置文件的 `~/.omp/profiles/<name>/agent/themes/` | omp 的主题，`<name>.json` | 本机已配置 omp 时。 |

`<config>` 是 Tern 的配置目录
（[目录](../concepts/packages.md#directories)）；Settings › Advanced 会显示这两个
文件夹。Tern 不会创建自己的 `themes` 文件夹，因此在添加第一个主题之前要先创建它。

连接到 host 的手机或平板从自己的文件夹读取主题，而不是 host 的文件夹。要在那里使用
位于电脑上的主题，请把它的文件复制到 Files 应用中的 `Themes` 文件夹，并连同它所依赖
的 CSS 主题一起复制。

- **名称。** 文件名去掉扩展名就是主题名。以内置主题命名的文件（`titanium.css`）会被
  跳过，与 omp 中的行为相同。两个文件夹中存在同名主题时，Tern 使用自己的那个。
- **实时编辑。** Tern 监视两个文件夹。新增、修改或删除的文件会在大约一秒内生效，因此
  可以在主题显示的同时编辑它。
- **损坏的文件。** 对于 `@import` 不是带引号名称后跟 `;`、或引用了不存在或会指回自身
  的主题的 CSS 主题，以及不是合法 JSON、有某个部分不是对象、或 `ansi` 列表长度不是
  恰好 16 项的 omp 主题，Tern 都会将其排除。Tern 无法解析的 CSS 声明会被丢弃，其余
  部分照常生效。[日志](debugging.md#log-files) 会说明原因，并给出行号与列号。
- **选择。** 在 Tern 中选择主题会把它保存到 `settings.json`（`theme_dark` 或
  `theme_light`）。在你选择之前，Tern 遵循 omp `config.yml` 中的 `theme.dark` 与
  `theme.light` 设置，它们可以指定任一文件夹中的主题。Settings › Appearance ›
  **Follow omp** 会清除你的选择，让 Tern 重新遵循 omp。

## omp 的主题 {#omp-s-themes}

omp 主题是 omp 格式的 JSON 对象，其中每一部分对 Tern 来说都是可选的：

| 键 | 内容 |
| --- | --- |
| `vars` | 其他部分可以引用的具名颜色。 |
| `colors` | omp 的颜色 token（`accent`、`success`、`muted`、`syntaxString` 等）。 |
| `export` | omp 的 HTML 导出颜色：`pageBg`、`cardBg`。 |
| `terminal` | 主题所面向的终端：`background`、`foreground`、`chrome`、`widget`，以及 16 色的 `ansi` 列表。 |
| `$schema` | Tern 忽略；编辑器用它做补全。 |

omp 只加载 `colors` 中具备 omp 全部 token 的主题；Tern 只读取其中几个，其余自行推导。要在
编辑器中按 omp 的 schema 校验主题，请添加
`"$schema": "https://raw.githubusercontent.com/can1357/oh-my-pi/main/packages/coding-agent/theme-schema.json"`。

### 颜色值 {#color-values}

`vars`、`colors`、`export` 与 `terminal` 中的每个值都是下列之一：

| 值 | 含义 |
| --- | --- |
| `"#rrggbb"` 或 `"#rgb"` | 该颜色。Alpha 位（`#rrggbbaa`）会被忽略。 |
| 数字 `0`–`255` | xterm 256 色表中对应的条目。 |
| `"name"` 或 `"$name"` | 名为 `name` 的变量，或该名称的 `colors` token。最多沿 8 个名称的链条查找。 |
| `""` | 未设置：Tern 使用自己的颜色，等同于省略该键。 |

Tern 无法解析的值（例如拼错的名称）视为未设置。

### Tern 读取的内容 {#what-tern-reads}

| 键 | Tern 的用途 | 缺失时 |
| --- | --- | --- |
| `terminal.background` | 终端背景。背景为深色时主题即为深色。 | `export.pageBg`，其次 `colors.statusLineBg`，否则用接近黑色的颜色。 |
| `terminal.foreground` | 程序未着色的文本。 | `colors.text`，否则用与背景同色相的中性色。 |
| `terminal.chrome` | 侧边栏、标签栏与标题栏。 | 比背景深一档的颜色。 |
| `terminal.widget` | 抬升的行与按钮。 | 亮度接近背景时用 `export.cardBg`，否则用背景与文本的混合色。 |
| `terminal.ansi` | 按顺序排列的全部 16 个 ANSI 颜色 0–15。 | Tern 用主题的其他颜色生成。 |
| `colors.accent` | 选中、焦点、光标与高亮的控件。 | `colors.borderAccent`，否则用文本色。 |
| `colors.borderAccent`、`colors.border` | 强调渐变中的第二种颜色。 | 强调色。 |
| `colors.success`、`colors.error`、`colors.warning` | 完成、失败与警告标记；没有 `ansi` 列表时也用作 ANSI 绿、红与黄。 | 文本色。 |
| `colors.muted`、`colors.dim` | 次要与弱化的界面文本；`dim` 也用作 ANSI 亮黑。 | 文本与背景的混合色。 |
| `colors` 中其他每种文本 token（`mdHeading`、`mdLink`、`mdCode`、`mdQuote`、`syntaxKeyword`、`toolDiffAdded`、`toolTitle`、`thinkingText`、`statusLineModel` 等） | omp 用它着色的内容，即面板中 omp 聊天与其他原生视图的标题、链接、引用、高亮代码、差异与工具标题。 | Tern 为该类文本自带的颜色。 |

其他以 `Bg` 结尾的 token（`userMessageBg`、`toolErrorBg` 等）会被忽略：卡片与选中项
保留 Tern 的填充。

除非 `ansi` 列表的 16 项都是它能解析的颜色，否则 Tern 会忽略该列表。没有列表时，它
自行构建色表：色相合适时，红、绿、黄取自 `error`、`success` 与 `warning`，蓝、洋红与
青取自主题中最接近这些色相的颜色。亮色是普通色的较浅版本。Tern 在 `vars` 与 `colors`
的所有颜色（以 `Bg` 结尾的 token 除外）中寻找这些色相。同一批颜色也提供主题的橙色，
用于标记正在运行的工作。

程序也能看到主题：向终端查询自身颜色（OSC 4、10、11 与 12）的程序会得到主题的 ANSI
颜色、背景、前景与光标。

### 可读性 {#legibility}

Tern 会调整 omp 主题中在背景上难以阅读的颜色：

- 终端文本至少获得 4.5:1 的对比度。
- ANSI 颜色至少 3:1。深色主题上的黑色与浅色主题上的白色保持不变，因为程序把它们用作
  填充色。
- 强调色至少 3:1，次要界面文本在其所处的每个表面上至少 4.5:1。
- omp 聊天使用的 token 颜色在背景、代码块与浮层上至少 4.5:1；注释、边框、分隔线、
  `muted` 与 `dim` 为 3:1。

已经足够清晰的颜色会按你写的保留。不够清晰的颜色会在自身色相内调亮或调暗直到可读，
因此文件中很暗的颜色在 Tern 里可能显得更亮。

## 完整示例 {#a-full-example}

一个自成一体、带完整 ANSI 色表的浅色主题，建立在 omp 默认浅色主题之上：

```css
:root {
	color-scheme: light;
	--paper: #fbf8f1;
	--ink: #1f2328;

	--tv-bg: var(--paper);
	--tv-fg: var(--ink);
	--tv-cur: #2f5f9e;
	--tv-cur-ink: var(--paper);
	--accent: #2f5f9e;
	--ok: #4d7a35;
	--bad: #b0412e;
	--warn: #9a6a00;

	--ansi0: #1f2328;
	--ansi1: #b0412e;
	--ansi2: #4d7a35;
	--ansi3: #9a6a00;
	--ansi4: #2f5f9e;
	--ansi5: #8a3f8f;
	--ansi6: #1f7a7a;
	--ansi7: #d8d2c4;
	--ansi8: #6b6459;
	--ansi9: #c4513c;
	--ansi10: #5e9142;
	--ansi11: #b07d0a;
	--ansi12: #3d72b8;
	--ansi13: #a04ea6;
	--ansi14: #2a9090;
	--ansi15: var(--paper);

	--omp-mdHeading: #8a3f8f;
	--tk-keyword: #b0412e;
	--tk-string: #4d7a35;
}

#statusline {
	letter-spacing: 0.01em;
}
```

## 另见 {#see-also}

- [CSS 变量](../styles/variables.md)：主题可以设置的每个变量。
- [chrome 与样式](chrome.md)：在插件中用 CSS 重新设置 Tern 窗口的样式。
