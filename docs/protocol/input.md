# Input and Events

Keys reach the program as they always have: on the pty, as input. What a
pointer does in a surface, and what changes in the pane, comes back as events.

## Keys

Keys reach the program as pty input: the kitty keyboard protocol, bracketed
paste. A focused `editor` or `input` (the `focus` op) shows Tern's caret, but
the text model is yours: you answer keys with `text` or `splice` ops and a new
`cursor`. IME composition happens in Tern's hidden text area, is drawn as
preedit at the field's caret, and is committed to the pty as typed text.

The exceptions are native editing below: keys acting on Tern's selection
become an `edit` event, and the undo key an `undo` event. And in an inline
surface, while the focus is an `editor` in `dock` (a chat's composer) and no
`overlay` is anchored at its caret, plain PgUp and PgDn page the pane, as a
chat app's message field pages its history: `main` scrolls with the pane, so
they never reach you there. A field with `typeahead` holds typing back until
you can read it ([Typeahead](#typeahead)).

## Native editing

With the `edit` program feature in your `hello`, Tern keeps a selection of its
own in your `editor` and `input` fields, as a GUI text field has, unless the
field has a `mode` (a Vim mode) or is `readonly`. The user can turn it off
(Settings › Terminal › Native composer editing). For a program without `edit`
every key stays the program's, since a key acting on Tern's selection would
reach it as an event it drops.

- ⇧ with the arrows (⇧⌥ or ⇧⌃ ←/→ for words, ⇧⌘ ←/→ or ⇧Home/End for the
  line, ⇧⌘ ↑/↓ for the text), or a drag, double or triple click select; ⌘A
  selects all. On PC keyboards Ctrl stands for ⌘ as their text fields have
  it (Ctrl+A, Ctrl+C, Ctrl+X, Ctrl+V, Ctrl+⇧←/→, Ctrl+⇧Home/End); Alt and
  Windows/Super chords stay yours and the app's.
- Tern draws its selection instead of your `cursor` and `anchor` until the
  text changes. With a selection, typing, pasting, IME commits, ⌫, ⌦ (with
  their word and line variants) and ⌘X or ⌃X replace it, ⌘C copies it
  locally, and a plain arrow collapses it. Without one, only the selecting
  keys and the drawn-line moves below are Tern's: ⌘C, ⌘X, ⌃X, deletes and
  on PC keyboards Ctrl+V stay yours. An empty field has nothing to select,
  so every key there stays yours (undo aside).
- A click in the focused field places the caret: an `edit` event with
  `from == to`, sent only when the caret moved. A click in a field without
  the focus sends `focus` instead ([Events](#events)).
- Only Tern knows where text soft-wraps, so a plain ↑ or ↓ moves the caret to
  the drawn line above or below (at the x a run of them started from), and
  ⌘← or ⌘→ (Home, End) to the drawn line's start or end. Each of these goes to
  you as one `edit` event, never as keys.
- Otherwise every key is yours as before: ↑ on the first drawn line and ↓ on
  the last (your history), ↑ and ↓ while an `overlay` anchored at the caret
  is open (its list). On PC keyboards, without a selection, Ctrl+Home/End
  (the text's start or end) and Ctrl+Backspace/Delete stay yours too.
- Over a misspelling decorated `typo`, the context menu leads with the
  platform spell checker's guesses; a pick sends an `edit`.

**Undo.** With the `undo` feature too, ⌘Z or ⌃Z (Ctrl+Z on PC keyboards) in a
natively edited field goes to you as one `undo` event instead of a key, with
or without a selection and in an empty field, so a cleared draft can come
back. The history is yours, each `edit` event one step. In Vim mode, with
native editing off, or without `undo`, ⌃Z stays your key.

**Sending.** With the `send` feature, Tern can submit a prompt into your
composer atomically (an initial prompt for an agent, Carly asking it): a
`send` event, not a paste followed by Enter. A field accepts it only while it
reports `sendable:true` (and is not `readonly`, `disabled` or `hidden`),
meaning its owner, its submission handler and what that depends on are
ready. Writable text and focus are separate: a focused,
editable field can still be `sendable:false` while the program starts. Send a
frame setting `sendable:true` when ready, even if nothing else changed; Tern
holds its prompts until then.

**Replying.** While your focused `editor` sits in `dock` (a chat's composer),
the context menu over a selection in the pane offers Reply with Selection. It
pastes the selected text as a Markdown quote (`> ` before each line, `>` alone
on a blank one, then a blank line) the way any paste reaches you: bracketed,
or as a paste event with mode 5522. Nothing is sent; the quote is your draft
to edit and undo, and the pane takes the keys so the user can type the reply
under it.

## Typeahead

A program that cannot read input yet (it is still starting, its event loop
busy) can set `typeahead: true` on its focused `editor` or `input`, as a
terminal's line discipline echoes typing before a program reads it. While it
is set, Tern keeps what is typed into the field instead of writing it to the
pty, and draws it at your `cursor` as if your text held it: typed text and IME
commits without line breaks or other control characters, and ⌫ over what it
kept. Clear the prop once you read keys again: Tern writes what it kept to
the pty as typed, and draws it on until a frame changes the field's `text`.

Any other key (Enter, an arrow, a shortcut, a paste) goes to the pty as
usual, after what was kept: you read both in the order they were typed.
That key may consume the text (Enter sends the draft) and leave `text` as it
was, so text that went ahead of a key draws until a frame changes `text` or
clears the prop.
Native editing steps aside while Tern holds kept text. A field with a `mode`
or `readonly` keeps nothing; what a field kept is lost when the node or the
surface goes away. A Tern without typeahead ignores the prop: keys reach the
pty as they are typed.

## Pointer actions

The common `actions` prop says what a pointer does on a node. It is an
object with an action per gesture, `{"click": act, "dblclick": act, "menu":
[act…]}`, every key optional:

```json
{"id": "row", "k": "text", "p": {"text": "build.log",
  "actions": {"click": "open-log", "dblclick": "copy", "menu": ["rerun", "sort=name"]}}}
```

| Action | Where it runs | Event |
| --- | --- | --- |
| `toggle` | Tern folds or unfolds the node (a collapsible `card`, `section`, `tool`, `agent`, `checklist`) at once | `{"ev":"toggle","id","collapsed","key?"}` |
| `copy` | Tern copies the node's text (Markdown source for `md`, raw text for `code`, `ansi` and `text`, a `block`'s raw output, the `href` when it has one), flashes the node and shows Copied | none |
| `open` | Tern opens the node's `href` or `path` | none |
| `zoom` | Tern shows the `image` large in its viewer, stepping through the images beside it | none |
| `select` | The program | `{"ev":"select","id","item","values?"}` |
| `activate` | The program | `{"ev":"activate","id","item","values?"}` |
| any other name | The program | `{"ev":"action","id","act","value?","item?","mods?","checked?","values?"}` |

- `click` and `dblclick` give the node `.sf-act` and the pointing-hand
  cursor. A click that opens a link
  (⌘-click, or a plain click on an inline link when Settings › General ›
  Links opens them on a plain click) opens it instead of running `click`.
- `menu` lists context-menu entries, labeled from the action name
  (`open-file` reads Open file), with Tern's Copy appended unless the list
  names `copy`. An entry can also be `"-"` (a separator), `{"header"}` (a
  section title) or an item object with the fields of a
  [`menu`](../elements/lists.md#menu) row: `id` (the action), `label`,
  `icon`, `keys`, `detail`, `checked`, `radio`, `disabled`, `danger` and
  `items` (a submenu). A pick runs the action as a click does, without
  `mods`; a check or radio row's action also carries `checked`, its new
  state.
- `toggle`'s `key` is still the bare node `key` prop, when it has one; the
  event does not qualify it with the parent. Tern remembers the local fold
  by that key among the node's siblings, not surface-wide. A `del` followed
  by an `add` with a new node id and the same key under the same parent
  preserves the fold; the same key under another parent has independent
  state. Without a key, local state uses the node's id.
- For `select` and `activate` on an `item` of a `list`, `id` is the list and
  `item` the item; on a `table` row, `id` is the table and `item` the row's
  `id`; from the other kinds below that pick something (a nav item, a
  crumb, a preset, a frame, a suggestion, a question), `id` is the node and
  `item` what was picked; on any other node both are the node's id.
- `item` on an `action` names the table row a button cell or a row `menu`
  entry ran on, the `menubar` menu a row was chosen from, or the question a
  `questions` step left; other actions have none.
- A custom name with `=` splits into `act` and `value` (`"sort=name"`).
  `mods` lists the modifiers held, in the order `shift`, `ctrl`, `alt`,
  `meta` (⌘ is `meta`), and is absent when none is.
- `values` is there when the node sits in an `el` `form`
  ([Form values](#form-values)).

Hover, scrolling, text selection, tooltips and the context menu are Tern's
own. Some kinds send events of their own without an `actions` prop:

| Kind | Events |
| --- | --- |
| `list` items | `select` on click, `activate` on double click, `id` the list ([Lists](../elements/lists.md#item)); an item's own `click` or `dblclick` action replaces the matching one |
| `table` with `selectable` | `select` on a row click, `activate` on a double click, `id` the table, `item` the row ([Data](../elements/data.md#table)) |
| `table` with `sortable` | `action` `sort` with `value` `{"col","dir"}` on a header click ([Data](../elements/data.md#table)) |
| `table` with `multi` | `change` with `value` the picked row ids; its `bar` buttons `action` with `value` the picked ids ([Data](../elements/data.md#table)) |
| `table` button cells, row `menu` | `action` with the cell's `act` or the menu entry, `item` the row |
| `button` | `action` with `act` its `actions.click`, else `"click"` ([Inputs and Buttons](../elements/input.md#button)) |
| `select` | `change` with `value` the option picked; `toggle` with `open` when the pointer opens or closes its menu ([Inputs and Buttons](../elements/input.md#select)) |
| `switch` | `change` with `value` the new state, `true` or `false` ([Inputs and Buttons](../elements/input.md#switch)) |
| `slider` | `change` on release with `value` a number, or `[lo, hi]` for a range ([Inputs and Buttons](../elements/input.md#slider)) |
| `otp` | `action` `focus` with `value` the cell the caret went to ([Inputs and Buttons](../elements/input.md#otp)) |
| `calendar` | `change` with `value` a `"YYYY-MM-DD"` day or a `[from, to]` range; `select` with `item` a preset's id; `action` `month` with `value` `"YYYY-MM"` ([Inputs and Buttons](../elements/input.md#calendar)) |
| `date` | `toggle` with `collapsed` (`false` when it opened), then `change` and `action` `month` as `calendar` ([Inputs and Buttons](../elements/input.md#date)) |
| `tabs` | `select` with `item` the tab's id ([Tabs](../elements/lists.md#tabs)) |
| `menu` | `action` with `act` the row's id, and `checked` for a check or radio row; `toggle` with `open` ([Menus](../elements/lists.md#menu)) |
| `menubar` | `action` with `act` the row's id, `item` the menu's id, `checked?`; `toggle` with `item` the menu's id and `open` ([Menus](../elements/lists.md#menubar)) |
| `nav` | `select` with `item` the item or sub-item ([Navigation](../elements/lists.md#nav)) |
| `breadcrumb` | `select` with `item` the crumb ([Navigation](../elements/lists.md#breadcrumb)) |
| `pager` | `change` with `value` the page (1-based); `action` `more` ([Navigation](../elements/lists.md#pager)) |
| `tree` | `toggle` with `key` the item ([Data](../elements/data.md#tree)) |
| `split` | `change` on release with `value` every pane's share, summing to 1 ([Layout](../elements/layout.md#split)) |
| `carousel` | `change` with `value` the index of the slide now shown ([Data](../elements/data.md#carousel)) |
| `attachment` | `action` with `act` `remove`, `retry` or one of its `actions` ([Data](../elements/data.md#attachment)) |
| `picker` | `select`, `activate` and `action` ([Picker events](../elements/lists.md#events)) |
| `prefs` | `select`, `activate`, `action`, `focus`, and `change` with `item` and `value` ([prefs](../elements/work.md#prefs)) |
| `checklist` (hud) | `activate` with `item` `"hud"` when its pill opens or closes ([checklist](../elements/work.md#checklist)) |
| `tool` with `confirm` | `action` `allow`, `deny` or `always`, `value` the scope when there is one ([tool](../elements/work.md#tool)) |
| `trace` | `toggle` with `open`, `item` the line's id (none for the head) ([trace](../elements/work.md#trace)) |
| `message` | `change` with `value` a reaction chip's text and `on`; `action` from its action buttons ([message](../elements/work.md#message)) |
| `suggestions` | `activate` with `item` the item's `id`, else its text ([suggestions](../elements/work.md#suggestions)) |
| `questions` | `change` with `item` the question and `value` its answer; `action` `next`, `back` or `skip` with `item`, `submit` with `value` every answer; `select` with `item` in a `list` ([questions](../elements/work.md#questions)) |
| `stacktrace` | `select` and `activate` with `item` the frame's index ([stacktrace](../elements/work.md#stacktrace)) |
| `el` checkbox, radio | `change` ([HTML Elements](../elements/el.md#the-change-event)) |
| `editor`, `input` | `focus`, `edit`, `undo` (above) |
| `input` addons | `action` `clear`, `inc` or `dec`, or an attached button's act ([Inputs and Buttons](../elements/input.md#addons)) |

## Events

Every terminal → program message is an `e` event, `ESC _ tsp;e;{…} ESC \`
(OSC 877 through a Windows ConPTY, see [Transport](transport.md#windows)). An
event about one surface carries its id as `sf`: every event below but
`theme`, `motion`, and a `gone` answering an `adopt`; an `error` has it when
the rejected message named a surface.

| Event | Payload | When |
| --- | --- | --- |
| `ack` | `s` | The highest frame applied *and drawn*; at most one per displayed frame ([Flow control](operations.md#flow-control)). |
| `resize` | `cols`, `cell` (`{"w","h"}`), `visible` | The pane's live surface was first drawn, or the pane's width in columns or its cell size changed. A pane shown in several windows (another computer, a phone, a browser) has one width, that of the window the user worked in last, and only it is reported; the first one may then only come with a change, the `hello` reply's `cols` standing until then. Only needed for `rows` and ANSI-width decisions. |
| `theme` | `dark` | The appearance switched. |
| `motion` | `reduce` | Reduce Motion was toggled. |
| `visible` | `visible` | The pane was hidden (another tab) or shown again: pause expensive work. |
| `toggle`, `select`, `activate`, `action` | above (`item` for list items, tabs, table rows and what the kinds above pick; `checked` from a check or radio menu row; a `toggle` from `select`, `menu`, `menubar` or `trace` carries `open` instead of `collapsed`) | A user action. |
| `change` | `id`, `value`, `checked`, `name?`, `values?`; from `prefs`: `id`, `item`, `value`; from the other kinds above: `id`, `value` (with `item` from `questions`, `on` from `message`) | The user flipped an `el` checkbox or radio ([HTML Elements](../elements/el.md#the-change-event)), changed a `prefs` row's value, or changed a control kind's value (a select, switch, slider, calendar or date, a pager's page, a split's sizes, a carousel's slide, a `multi` table's picks, a reaction, an answer). |
| `focus` | `id` | A click asked for the keys: in an `editor` or `input` (not `readonly`) that isn't the focus, or in a `prefs` node while the focus is in a field outside it. Move your focus there (and answer with a `focus` op), or ignore it: a modal overlay keeps the keys. |
| `edit` | `id`, `from`, `to`, `text`, `cursor`, `len` | Native editing: replace UTF-16 `[from, to)` of field `id`'s text with `text` (one undo step), then put the caret at `cursor`. `from == to` with empty `text` only moves the caret. `len` is the length of the text Tern saw: ignore the event when your text has changed since (keys in flight). Only with the `edit` feature. |
| `undo` | `id` | Undo the last change to field `id` through your own history; nothing when there is none. Written in order with the keys around it. Only with the `undo` feature. |
| `send` | `id`, `text` | Submit `text` through composer `id`'s normal submission path, keeping multi-line text, commands and attachments. Only to a live, editable field reporting `sendable:true` of a program with the `send` feature; anything else is dropped. |
| `error` | `s`, `op`, `msg`; or `msg` (with `s` when known); or `sheet`, `msg`; or `id`, `msg` | A rejected op in frame `s` (`op` its index); a rejected message or a dropped chunk; from the view, a stylesheet's parse errors (`sheet`, the messages joined with `; `) or an `el` with an unknown tag (`id`). |
| `gone` | `ids` | Tern dropped these nodes under its retention budget; dropped a surface whose anchor line left (scrolled out of the scrollback, the scrollback cleared, the alternate screen left), `ids` its own id; or an `adopt` found nothing. Stop referencing them. |

## Form values

An `action`, `select`, `activate` or `change` event whose node sits inside an
`el` `form` carries `values`: each enabled, named control of that form as it
is at that moment. A radio group gives its checked radio's `value` (`null`
when none is), a lone checkbox `true` or `false`, and checkboxes sharing a
name the array of the checked ones' values in document order. The click that
submits a form carries what was picked, so you never have to ask:

```json
{"ev":"action","sf":"pick","id":"go","act":"submit","values":{"size":"l","notify":true,"tags":["a","c"]}}
```

The algorithm, with a worked example, is in
[HTML Elements](../elements/el.md#form-values).

## Only to a listening program

Whatever the terminal writes to the pty is typed text to a shell, so Tern
sends only what a program reads:

- Events Tern originates (`ack`, `resize`, `visible`, `theme`, `motion`,
  pointer and view events) go out only while some surface of the pane is open,
  and an event that names a surface only while that surface is open.
- A surface opened with `listen:false` never hears anything: no acks, events
  or errors about it, and after its `o` no answers at all until your next `q`
  or listening `o`.
- Answers to what you sent (replies to `q`, `error`, `gone`) go out unless the
  program is known to be gone: after a shell prompt, the pane's process
  exiting, or RIS, until something asks (`q`) or opens a surface (`o`). A late
  `f`, or the `x` of a surface the prompt already discarded, gets no answer. A
  program that closed its own surfaces with `x` still hears about its
  mistakes, because it may still be reading ([Leaving](surfaces.md#open-and-close)).
