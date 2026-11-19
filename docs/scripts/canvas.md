# Canvas Blocks

`canvas` commands open canvas blocks and draw on them: ink, shapes,
arrows and text, with any canvas chord. Use them to build a canvas for a
screenshot or to check that edits reach the canvas's host and its other
blocks.

## Open and wait

| Command | Does |
| --- | --- |
| `canvas new` | Opens a new, empty canvas beside the focused block, on the current host. |
| `canvas second` | Opens another block on the focused block's canvas beside it. |
| `canvas wait` | Waits until every canvas block shows its canvas and its host took every edit. |

`new` and `second` wait until the new block's canvas opened (or failed),
then settle for 350 ms; `wait` waits for the hosts' acknowledgements, with
the script's 20-second timeout.

## Draw

| Command | Does |
| --- | --- |
| `canvas tool <name>` | Picks a tool: `select`, `hand`, `draw`, `highlight`, `eraser`, `arrow`, `line`, `rect`, `ellipse`, `diamond`, `triangle`, `hexagon`, `parallelogram`, `star`, `cylinder`, `pill`, `bracket`, `brace`, `polygon`, `curve` or `text`. |
| `canvas draw <x,y> <x,y> …` | Presses at the first point and drags through the rest with the current tool. |
| `canvas rect <x> <y> <w> <h>` | Draws a rectangle (the rectangle tool, then a drag). |
| `canvas text <x> <y> "<text>"` | Clicks with the text tool and types the text. |
| `canvas key <chord>` | Runs a canvas chord by its id (`undo`, `group`, `copy`, `zoom_to_fit`; see [`canvas.*`](../reference/actions.md#canvas-blocks-canvas)) or presses a key the canvas takes itself: `escape`, `delete`, `enter`, `space`, `tab`, `left`, `right`, `up`, `down`. |
| `canvas select-all` | Selects every shape. |
| `canvas look clean\|mono\|sketch` | Sets the canvas's look. |

Points are the canvas's view pixels from its top-left; at the start a
canvas shows its origin at 100%, so they are page units too. A drag moves
in steps of at most 6 px, a sample every 8 ms, and never rests, so ink is
never snapped into a shape. These commands act on the focused canvas block
and settle for 350 ms; they fail when no canvas block has focus.

## State

`tern ctl state` reports each block in `canvas_blocks[]`: `id`, `canvas`
(`canvas:<id>`), `phase` (`loading`, `ready` or `failed`, with `error`),
`synced` (the host took every edit), `focused`, `saved_camera`, and the
editor's `tool`, `toolLocked`, `selection`, `focus`, `camera`, `shapes`,
`canUndo`, `canRedo`, `editing`, `look` and `paper`.
