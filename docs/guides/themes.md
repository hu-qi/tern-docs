# Custom Themes

Tern uses omp's themes, and you can write your own in CSS. Each theme is
either light or dark, and Tern picks one of each: the dark theme when the
window is dark and the light one when it is light (Settings › Appearance ›
Appearance). Add a theme, then choose it with **Change theme…** (⌃⌘T on
macOS, Ctrl+Shift+M elsewhere) or in Settings › Appearance › Theme.

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

Save this as `<config>/themes/campfire.css` and a dark theme called
`campfire` appears in the picker: gruvbox with a darker terminal, an orange
accent, yellow headings in omp's chats and a bold current tab.

## CSS themes

A CSS theme builds on another theme and lays its rules over it.

- **The base.** A leading `@import "<theme>";` names the theme it builds
  on: a built-in one, one of omp's, or another CSS theme, by the name the
  picker shows. Without one it builds on omp's default theme for its
  appearance (`titanium` dark, `light` light).
- **Light or dark.** `color-scheme: light` or `color-scheme: dark` in a
  `:root` rule makes it that appearance; without one it is its base's, and
  without either, dark. `light-dark(<light>, <dark>)` values pick the side
  of the appearance shown.
- **Every rule wins.** Every declaration counts as `!important`, and the
  sheet comes after Tern's and every plugin's sheets, so a rule of any
  specificity beats theirs. Only an inline `!important` beats it.
- **What to set.** Set the variables Tern draws with on `:root`: the
  terminal's `--tv-bg`, `--tv-fg`, `--tv-cur` and `--ansi0` … `--ansi15`,
  the interface's `--page`, `--accent`, `--ink`, `--t1` … `--t4`, `--ok`,
  `--bad` and `--warn`, highlighted code's `--tk-*`, and the colors of
  omp's chats, `--omp-<token>`. [CSS Variables](../styles/variables.md)
  lists them all. The panel follows `--tv-bg`, and hairlines and chip fills
  follow `--ink`. Any other rule restyles what it selects.
- **Outside CSS.** The picker's swatches and the colors programs get when
  they ask the terminal (OSC 4, 10, 11 and 12) come from the theme's bare
  `:root` rules outside `@media`: `--tv-bg`, `--tv-fg`, `--tv-cur`,
  `--tv-cur-ink`, `--accent` and `--ansi0` … `--ansi15`, as colors,
  `light-dark()` or a `var()` of another variable. Tern uses them as
  written, without the legibility changes it makes to omp's themes.
- **Chains.** A CSS theme built on another gets both sheets, the base's
  first, and can use the base's `:root` variables.

## Where themes live

| Folder | Holds | Read when |
| --- | --- | --- |
| `<config>/themes/`, beside `settings.json` | Tern's CSS themes, `<name>.css` | Always. |
| `Documents/Themes` in Tern's app storage, beside `Plugins` (on iOS, the Files app's On My iPhone or iPad › Tern › Themes) | Tern's CSS themes | On iOS and Android, in place of `<config>/themes/`. |
| omp's `themes/`: `~/.omp/agent/themes/`, or `~/.omp/profiles/<name>/agent/themes/` for a named omp profile | omp's themes, `<name>.json` | omp is set up on this machine. |

`<config>` is Tern's configuration directory
([Directories](../concepts/packages.md#directories)); Settings › Advanced
shows both folders. Tern doesn't create its `themes` folder, so make it
before you add the first theme.

A phone or tablet connected to a host reads themes from its own folder, not
the host's. To use a theme there that lives on your computer, copy its file
into the `Themes` folder in the Files app, along with the CSS themes it
builds on.

- **Names.** A file's name without its extension is the theme's name. A
  file named after a built-in theme (`titanium.css`) is skipped, as it is in
  omp. When both folders have a theme of the same name, Tern uses its own.
- **Live edits.** Tern watches both folders. A new, changed or deleted file
  shows up within about a second, so you can edit a theme while it is
  showing.
- **Broken files.** Tern leaves out a CSS theme whose `@import` isn't a
  quoted name followed by `;`, or names a theme that doesn't exist or leads
  back to it, and an omp theme that isn't valid JSON, has a section that
  isn't an object, or has an `ansi` list that isn't exactly 16 entries long.
  A CSS declaration Tern can't parse is dropped and the rest applies. The
  [log](debugging.md#log-files) says why, with the line and column.
- **Choosing.** Picking a theme in Tern saves it in `settings.json`
  (`theme_dark` or `theme_light`). Until you pick one, Tern follows the
  `theme.dark` and `theme.light` settings in omp's `config.yml`, which may
  name a theme from either folder. Settings › Appearance › **Follow omp**
  clears your picks so Tern follows omp again.

## omp's themes

An omp theme is a JSON object in omp's format, and every part of it is
optional to Tern:

| Key | Holds |
| --- | --- |
| `vars` | Named colors that the other sections can refer to. |
| `colors` | omp's color tokens (`accent`, `success`, `muted`, `syntaxString`, …). |
| `export` | omp's HTML export colors: `pageBg`, `cardBg`. |
| `terminal` | The terminal the theme is made for: `background`, `foreground`, `chrome`, `widget` and the 16-color `ansi` list. |
| `$schema` | Ignored by Tern; editors use it for completion. |

omp only loads a theme whose `colors` has every one of its tokens; Tern
reads a few of them and works out the rest itself. To check a theme against
omp's schema in your editor, add
`"$schema": "https://raw.githubusercontent.com/can1357/oh-my-pi/main/packages/coding-agent/theme-schema.json"`.

### Color values

Each value in `vars`, `colors`, `export` and `terminal` is one of these:

| Value | Means |
| --- | --- |
| `"#rrggbb"` or `"#rgb"` | That color. Alpha digits (`#rrggbbaa`) are ignored. |
| A number, `0`–`255` | That entry of the xterm 256-color table. |
| `"name"` or `"$name"` | The var called `name`, or the `colors` token of that name. A chain of up to 8 names is followed. |
| `""` | Unset: Tern uses its own color, the same as leaving the key out. |

A value Tern can't resolve, such as a misspelled name, counts as unset.

### What Tern reads

| Key | Tern uses it for | When it is missing |
| --- | --- | --- |
| `terminal.background` | The terminal background. A theme is dark when its background is dark. | `export.pageBg`, then `colors.statusLineBg`, else a near-black. |
| `terminal.foreground` | Text that programs don't color. | `colors.text`, else a neutral of the background's hue. |
| `terminal.chrome` | The sidebar, tab bar and title bar. | A step darker than the background. |
| `terminal.widget` | Raised rows and buttons. | `export.cardBg` when its lightness is close to the background's, otherwise a blend of the background and text. |
| `terminal.ansi` | ANSI colors 0–15, all 16 in order. | Tern makes them from the theme's other colors. |
| `colors.accent` | Selection, focus, the cursor and highlighted controls. | `colors.borderAccent`, else the text color. |
| `colors.borderAccent`, `colors.border` | The second color in the accent gradient. | The accent. |
| `colors.success`, `colors.error`, `colors.warning` | Done, failed and warning marks; also ANSI green, red and yellow when there is no `ansi` list. | The text color. |
| `colors.muted`, `colors.dim` | Secondary and faint interface text; `dim` is also ANSI bright black. | Blends of the text and background. |
| Every other text token in `colors` (`mdHeading`, `mdLink`, `mdCode`, `mdQuote`, `syntaxKeyword`, `toolDiffAdded`, `toolTitle`, `thinkingText`, `statusLineModel`, …) | What omp colors with it, in omp's chats and other native views in panes: headings, links, quotes, highlighted code, diffs, tool titles. | Tern's own color for that kind of text. |

The other tokens ending in `Bg` (`userMessageBg`, `toolErrorBg`, …) are
ignored: cards and selections keep Tern's fills.

Tern ignores an `ansi` list unless all 16 entries are colors it can resolve.
Without one, it builds the table: red, green and yellow come from `error`,
`success` and `warning` when their hues fit, and blue, magenta and cyan from
the theme's colors closest to those hues. The bright colors are lighter
versions of the normal ones. Tern looks for those hues among every color in
`vars` and `colors`, except tokens ending in `Bg`. The same colors supply
the theme's orange, which marks running work.

Programs see the theme too: a program that asks the terminal for its colors
(OSC 4, 10, 11 and 12) gets the theme's ANSI colors, background, foreground
and cursor.

### Legibility

Tern changes an omp theme's colors that would be hard to read on the
background:

- Terminal text gets at least 4.5:1 contrast.
- ANSI colors get at least 3:1. Black on a dark theme and white on a light
  one are left alone, since programs use them as fills.
- The accent gets at least 3:1, and secondary interface text at least 4.5:1
  on every surface it sits on.
- The token colors omp's chats use get at least 4.5:1 on the background,
  code blocks and popovers; comments, borders, separators, `muted` and `dim`
  get 3:1.

A color that is already clear enough stays as you wrote it. One that isn't is
made lighter or darker in its own hue until it reads, so a very dim color in
your file can look brighter in Tern.

## A full example

A light theme of its own, with its whole ANSI table, on omp's default light
theme:

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

## See also

- [CSS Variables](../styles/variables.md): every variable a theme can set.
- [Chrome and Styling](chrome.md): restyle Tern's window from a plugin with
  CSS.
