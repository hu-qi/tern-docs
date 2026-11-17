# Events

`tern.on(name, fn)` subscribes a handler to an event. The two contexts have
separate event sets: host events describe the panes running on one machine
and are heard by the host half there; window events describe what one Tern
window shows and are heard by the window half in that window. This page
lists every event with its payload, when it fires and in what order.

For the registration call itself see [Host API](api-host.md#ternon) and
[Window API](api-window.md#ternon).

## Choosing a side

Several events exist in both contexts under the same name. They describe the
same thing from different places:

| | Host event | Window event |
| --- | --- | --- |
| Heard by | The host half on the machine running the pane | The window half in every window showing the pane |
| Panes covered | Every pane on that host, whichever windows show it, or none | Every pane in that window's sessions, on any host |
| Fires when no window is open | Yes (the daemon keeps running) | No |
| Runs on | The plugin's worker thread, 2 s budget | The window's UI thread, 50 ms budget |
| `cx` | [Effect cx](api-host.md#effect-cx): toast, open, copy for the pane's windows | [Window cx](api-window.md#window-cx): the session, layout, commands |
| Pane ids | The host's own ids, as `tern.pane.write` takes | The window's ids, with remote hosts' tags ([Pane and tab ids](api-window.md#pane-and-tab-ids)) |

Use a host event for work tied to the machine (record command history,
write to a pane, run a local tool); use a window event for work tied to what
the user sees (rearrange panes, retitle, toast in this window only). A
window half with two windows open hears each window event once per window.

## Host events

| Event | Handler | Payload |
| --- | --- | --- |
| `command_started` | `(ev, cx)` | `{pane: number, line: string, cwd: string?}` |
| `command_finished` | `(ev, cx)` | `{pane: number, line: string, status: number, took_ms: number}` |
| `cwd` | `(ev, cx)` | `{pane: number, path: string}` |
| `title` | `(ev, cx)` | `{pane: number, title: string}` |
| `pane_exited` | `(ev, cx)` | `{pane: number, status: number}` |
| `spawn` | `(spec) -> spec?` | See [The spawn filter](#the-spawn-filter) |

Any other name raises `tern.on: unknown host event "<name>" (spawn,
command_started, command_finished, cwd, title, pane_exited)`.

### `command_started`

A shell in a pane on this host began running a command line: the shell's
integration reported OSC 133;C. Panes without shell integration never fire
it.

| Field | Meaning |
| --- | --- |
| `pane` | The pane |
| `line` | The command line as the shell reported it |
| `cwd` | The pane's working directory at that moment, from its last OSC 7 report; `nil` when the shell never reported one |

### `command_finished`

The command line ended (OSC 133;D). It fires only after a
`command_started` in the same pane; a finish without a start is ignored.

| Field | Meaning |
| --- | --- |
| `pane` | The pane |
| `line` | The command line, as in `command_started` |
| `status` | The exit status the shell reported |
| `took_ms` | Milliseconds from the start report to the finish report, measured by the host |

### `cwd`

The pane's shell reported a new working directory (OSC 7). Repeated reports
of the same directory don't fire it; a report with no usable path doesn't
either. A pane running a command whose shell reports none (an agent block)
follows its program instead: Tern reads where the program works every couple
of seconds and when it sets its title, and fires `cwd` when that moved
(macOS and Linux).

| Field | Meaning |
| --- | --- |
| `pane` | The pane |
| `path` | The new directory, as an absolute path |

### `title`

The pane's program set its title (OSC 0 or 2), or its icon title (OSC 1).
Setting the same titles again doesn't fire it. A change to the icon title
alone fires with `title` unchanged.

| Field | Meaning |
| --- | --- |
| `pane` | The pane |
| `title` | The pane's title after the change (may be `""`) |

### `pane_exited`

A pane's program on this host exited: a shell, the command a pane ran, or a
plugin block that ended. It fires once per pane, when the host notices the
exit.

| Field | Meaning |
| --- | --- |
| `pane` | The pane |
| `status` | The exit status (a plugin block's `cx:exit` code, `1` when it failed) |

### Delivery and ordering

- The host sends each event to every plugin's worker; a plugin with no
  handler for it ignores it. Each worker handles its queue in order, so a
  plugin sees one pane's events in the order they happened.
- Workers run in parallel. Handlers of different plugins run concurrently
  and in no defined order relative to each other.
- Within one plugin, handlers of an event run in registration order. They
  receive the same payload table and the same `cx`: a field one handler
  changes is visible to the next.
- A handler that raises is reported as "Plugin *name*: *event* failed" in
  the windows showing the pane, and the next handler still runs. A handler
  that trips its budget disables that event's handlers in that plugin until
  the next reload ([Runtime](../concepts/runtime.md#a-tripped-budget)).
- Events are handled between other requests to the worker: a block's key
  press and a `command_finished` queued before it are handled in arrival
  order.
- Where the panes run decides who emits: the session daemon emits them for
  its panes; a window that runs its panes without a daemon emits them for
  its local panes itself. iOS runs no host halves, so no host event fires
  there.

## The spawn filter

```lua
tern.on("spawn", function(spec)
	spec.env.EDITOR = "nvim"
	return spec
end)
```

`spawn` is not a notification: it is a synchronous filter over every process
pane this host is about to start (shells, and panes started with a command).
Plugin blocks are not filtered. The handler receives a `SpawnSpec` and returns
a spec to use instead, or `nil` to keep it.

| Field | Type | Meaning |
| --- | --- | --- |
| `program` | `string` | The program to run |
| `args` | `{ string }` | Its arguments |
| `cwd` | `string?` | The working directory |
| `env` | `{ [string]: string }` | The variables Tern sets on top of the inherited environment |

A returned table is read field by field:

| Field returned | Effect |
| --- | --- |
| `program`, `args` | Replace the old value; absent keeps it |
| `cwd` | Replaces the directory when it names an existing directory (a leading `~` is expanded); absent, or not a directory, keeps the pane's directory |
| `env` | The complete set of variables: names missing from it are removed, names already present keep their position, new names follow sorted. Absent removes them all |

Modify and return the table you received rather than building a partial
one.

Semantics:

- Only plugins that registered a `spawn` handler are asked. Plugins run in
  id order; each sees the spec the previous one returned.
- Within one plugin, its `spawn` handlers run in registration order, each
  receiving the previous handler's result.
- The pane waits at most 50 ms for each plugin's answer. The request queues
  behind whatever that plugin's worker is already doing, so a busy worker
  can miss the window. A late answer is discarded, the spec stays as it was
  before that plugin, and the host logs `plugin spawn filter took over 50 ms;
  skipped`. The handler itself still runs to completion under the 2 s budget.
- A handler that returns something other than a table or `nil` is reported
  as `spawn must return a spec table or nil, got <type>`; a table whose
  fields have the wrong types is reported with the conversion error. In both
  cases that handler's result is ignored. `spawn` failures toast in every
  window of the host.

See [Host Hooks and the Spawn Filter](../guides/hooks.md).

## Window events

| Event | Handler | Payload |
| --- | --- | --- |
| `window_start` | `(cx)` | none |
| `focus` | `(ev, cx)` | `{pane: number, tab: number}` |
| `pane_created` | `(ev, cx)` | `{pane: number}` |
| `pane_closed` | `(ev, cx)` | `{pane: number}` |
| `tab_created` | `(ev, cx)` | `{tab: number}` |
| `tab_closed` | `(ev, cx)` | `{tab: number}` |
| `command_started` | `(ev, cx)` | `{pane: number, line: string}` |
| `command_finished` | `(ev, cx)` | `{pane: number, line: string, status: number, took_ms: number}` |
| `cwd` | `(ev, cx)` | `{pane: number, path: string}` |
| `title` | `(ev, cx)` | `{pane: number, title: string}` |
| `agent_state` | `(ev, cx)` | `{pane: number, old: string?, new: string}` |
| `agent_finished` | `(ev, cx)` | `{pane: number, result: "done" \| "failed" \| "exited" \| "closed"}` |
| `float_moved` | `(ev, cx)` | `{pane: number, tab: number, over: number, corner: string?, stashed: string?, docked: string?}` |
| `session_ended` | `(ev, cx)` | `{session: number, name: string, shown: boolean}` |
| `budget` | `(ev, cx)` | `{hook: string, state: "paused" \| "resumed", ms: number?, paused_ms: number?}` |
| `canvas_action` | `(ev, cx) -> boolean?` | `CanvasAction`: `{pane, owner, act, node, value?, mods?, text?, title?, about?}` |

Any other name raises ``tern.on: unknown window event `<name>` ``.

### `window_start`

Runs once per plugin per window, after the window's session has settled:
saved tabs restored, or the first tab started. It is the place for workspace
setup that must see the tabs it adds to. A reload doesn't run it again for
plugins that already ran it in this window; a plugin installed or enabled
since does get it. It receives only `cx`. See
[Layout and Workspaces](../guides/layout.md#a-workspace-at-launch).

### `focus`

The focused pane of the window's active tab changed: a click, a key, a tab or
session switch, a split, a close. It is deduplicated by pane: it fires only
when the pane differs from the one the last `focus` named, so focusing the
already focused pane again, or moving it to another tab where it keeps the
focus, doesn't fire it (`tab` is not compared). Leaving the
window with no active tab fires nothing; the next focused pane fires again,
even if it is the one named last.

| Field | Meaning |
| --- | --- |
| `pane` | The newly focused pane |
| `tab` | Its tab |

The window gaining or losing system focus is not a `focus` event.

### `pane_created`, `pane_closed`

`pane_created` fires when this window adds a pane of any kind: a new tab, a
split, a pane started from the palette, a plugin block, a pane from
`cx.layout`, and every native block (browser, including the pictures in
picture `tern browser` opens, file, git, database, notebook, board, canvas,
processes, screen, profile and Carly blocks).
`pane_closed` fires for each pane this window closes, including every pane of
a closed tab. Panes and tabs that arrive from the daemon instead (restored
when the window attaches, or created by another window on the same session)
don't fire `pane_created` or `tab_created`.

| Field | Meaning |
| --- | --- |
| `pane` | The pane |

### `tab_created`, `tab_closed`

A tab opened or went away in this window, including a tab made by moving a
pane into a tab of its own, and a tab that disappears because its only pane
moved out. Closing a tab fires `tab_closed` before the `pane_closed` of its
panes.

| Field | Meaning |
| --- | --- |
| `tab` | The tab |

### `command_started`, `command_finished`

As the host events of the same name, for every pane in this window's
sessions, local or remote, but without `cwd` in `command_started`. Read the
pane's directory with `cx.session:panes()` when needed. `took_ms` is measured
by the window, from the start report it saw to the finish report.

### `cwd`, `title`

As the host events of the same name, for every pane in this window's
sessions. A remote pane's `path` is a path on its host.

### `agent_state`

An agent block's state changed, as `cx.agents:list()` reports it:
`working`, `waiting_input` (a question or permission prompt waits, or a
prompt could not be delivered), `idle` or `exited`. It fires once per
change, for agents in every session of the window. The window compares
states after a render, at most every 250 ms, and only while some plugin
listens: the first comparison after a load only learns the states, and a
change that reverts within one look fires nothing. An agent that appeared
since the last look fires with `old` nil. A closed agent fires
`agent_finished` instead.

| Field | Meaning |
| --- | --- |
| `pane` | The agent's pane |
| `old` | Its state at the last look (`nil`: new since) |
| `new` | Its state now |

### `agent_finished`

An agent block's turn ended, or the agent did. A turn that ends while a
prompt waits for the agent is not reported.

| Field | Meaning |
| --- | --- |
| `pane` | The agent's pane |
| `result` | `"done"` or `"failed"` as the agent reported it, `"exited"` when its program exited, `"closed"` when its block closed while the program ran |

### `float_moved` {#float_moved}

The user let go of a floating block (a picture in picture) they dragged or
threw, whether or not it moved: once per release, after Tern snapped it into
place. Floats always land in a corner of the block they float over, slide off
an edge as an edge tab, or dock into the split tree. Moving a float with the
keyboard, the menu or `cx.layout:float` doesn't fire it, and neither does
resizing one with its grips.

| Field | Meaning |
| --- | --- |
| `pane` | The floating block |
| `tab` | Its tab |
| `over` | The block it floats over now, or the block it docked beside |
| `corner` | The corner of `over` it snapped to: `"tl"`, `"tr"`, `"bl"` or `"br"`; `nil` when it docked |
| `stashed` | `"left"` or `"right"` when it slid off that edge (it keeps `corner` to come back to); else `nil` |
| `docked` | `"left"`, `"right"`, `"up"` or `"down"` when it docked into the tree on that side of `over` and no longer floats; else `nil` |

### `session_ended`

A session of this window went away: closed in this window (Close session,
`cx.sessions:close`), ended by a block started with `--end-on-success`
whose program exited with status 0, or closed by another window on the
same sessions or by `tern kill session`. It fires after the `tab_closed`
and `pane_closed` of what it held, when this window closed it. Closing a
session's last tab leaves the session there, empty, and fires nothing; so
does closing a window's only session, and a host disconnecting doesn't end
its sessions either.

When the session ended was the one the window showed, the window shows the
session it showed before it (the most recent one still there), else the
next one in the list; `cx.sessions:current()` already names it when the
handler runs.

| Field | Meaning |
| --- | --- |
| `session` | The session's id, as `cx.session:sessions()` gave it |
| `name` | Its name |
| `shown` | The window showed it when it ended |

### `budget`

One of this plugin's own hooks ran over its budget and is paused, or its
pause ended ([Runtime, Budgets, and JIT](../concepts/runtime.md#a-tripped-budget)).
Only the plugin whose hook it is hears it, in the window where it tripped.
Host-half pauses are not delivered here; `tern plugin list` shows them.

| Field | Meaning |
| --- | --- |
| `hook` | The hook (`timer`, `command <id>`, `status`, …) |
| `state` | `"paused"` or `"resumed"` |
| `ms` | The budget it ran over (`paused` only) |
| `paused_ms` | How long it is paused (`paused` only) |

### `canvas_action`

A click on a node with a custom `actions` name in a canvas this plugin owns
([Canvas cx](api-window.md#canvas-cx)), in the clicking window only. Only the
owner's handlers run, in registration order, and the first truthy return
consumes the click; with none, the window toasts `Nothing handles “<act>”
here`. `cx.session:event(pane, {ev = "action", id = node, act = name})`
delivers the same action without a pointer, after the calling handler
returns; `id` is the node's id as a click reports it, and `text`, `title`
and `about` are read from the canvas as the call left it, updates made just
before included. Toggle, selection and Tern's own actions (`copy`, `open`,
`zoom`) never arrive, except a `toggle`, `open` or `zoom` with nothing to
collapse, open or zoom, which arrives as a custom action.

| Field | Meaning |
| --- | --- |
| `pane` | The canvas pane |
| `owner` | The plugin id that opened it |
| `act`, `value` | The action name up to its first `=`, and the rest |
| `node` | The clicked node's id |
| `mods` | Modifiers held, when any |
| `text` | The clicked node's text |
| `title`, `about` | The canvas's title and purpose |

### Delivery and ordering

- The session queues events as they happen. After each render the window
  hands the queue to the plugins: for each event in order, every plugin in id
  order, and within a plugin every handler in registration order. Each
  handler gets a fresh `cx`.
- Events caused by a handler (a split made through `cx.layout`, a tab closed
  through `cx:command`) are queued and delivered after the current batch, in
  the next round; handlers are never re-entered from inside a handler.
- Events that happen while the window has no loaded window half are dropped,
  not saved for later.
- A handler that raises toasts "Plugin *name*: *event* failed" in this
  window; the next handler still runs. A trip of the 50 ms budget pauses
  that event's handlers in that plugin, in this window (5 s, longer if it
  keeps tripping); events during the pause are skipped.
- The web client runs no Lua; its window hears nothing.

## Related pages

- [Host Hooks and the Spawn Filter](../guides/hooks.md) for worked host
  examples.
- [Layout and Workspaces](../guides/layout.md#window-events) for window
  examples.
- [Limits](limits.md) for budgets and waits.
