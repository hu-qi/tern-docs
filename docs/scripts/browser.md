# Browser Blocks

Browser commands open web pages beside terminals and focus their address
fields. Use them with `webview` reports to stage a page's title, loading
state and navigation controls in a headless script, without fetching a real
website.

## Opening and addressing

| Command | Does |
| --- | --- |
| `browser open [<address or search>...]` | Opens a browser block beside the focused pane. With no input, opens a blank page with its address field focused. |
| `browser address` | Focuses the focused browser block's address field and selects its text, like ⌘L. |

`open` joins all remaining words with spaces. Quote an address or search
containing spaces for clarity. Leading and trailing whitespace is removed;
blank input opens a blank page. An explicit scheme is kept, dotted host
names gain `https://`, and `localhost` or IP addresses gain `http://`.
Other text becomes a web search.

`address` does nothing when the focused pane is not a browser block. Its
parser also accepts and ignores trailing words; they have no effect.
Both commands settle for 450 ms. This is not a real-time page-load wait:
there is no browser readiness command or network timeout in this family.
They are not restricted to desktop builds, but do not run in the web client.

## Reporting a page

Headless runs show a page card rather than a native web view. `webview`
sends the events a native page would report; it does not load a website or
execute its JavaScript. The command also works in a live window.

| Command | Does |
| --- | --- |
| `webview <selector> title <text>` | Reports the page title. |
| `webview <selector> url <text>` | Reports the current address, for example after a redirect. |
| `webview <selector> loading <progress>` | Reports loading progress from `0` to `1`; `1` finishes loading. |
| `webview <selector> failed <message>` | Reports a load failure and ends loading. |
| `webview <selector> history <true\|false> <true\|false>` | Sets whether Back and Forward are available, in that order. |
| `webview <selector> focus <on\|off>` | Reports whether the page has keyboard focus. |
| `webview <selector> new-window <url>` | Reports a request to open another page; ordinarily opens a browser block beside this one. |
| `webview <selector> inspector-page <url>` | Reports the page's Web Inspector as a page at this address (WPE WebKit's inspector server); opens a browser block on it beside this one. |
| `webview <selector> inspector-unavailable <message>` | Reports that the page's Web Inspector cannot open in Tern; shows the message as a toast. |
| `webview <selector> security-key` | Reports that the page asked for a security key or passkey (WebAuthn) and the engine refused it; shows the note under the toolbar offering **Open in default browser**. |
| `webview <selector> media-blocked <hint>` | Reports that the page tried to play audio or video the engine cannot load (WebKitGTK on Linux); shows the hint in a note under the toolbar, with **Open in default browser**. |

The selector targets the first matching element that has a web view.
For the focused browser block, use `".tn-pane.on .kit-web-page"`; for a
floating browser, use `".tn-pane.pip .kit-web-page"`. A malformed selector or
one with no matching web view fails the command. Text forms require exactly
one argument, so quote titles, messages and URLs containing spaces. Progress
outside `0`–`1`, missing arguments and invalid flags also fail.

Reports are applied without waiting for a real page to load. An empty URL
or `about:blank` report leaves the stored address unchanged. A progress
report below `1` starts or continues loading; starting loading after it has
ended clears the previous error. Title, URL, progress, failure and history
reports update the session's page so other windows of that session see them
too. For a browser driven by browser automation, `new-window` is recorded as
a report instead of opening a block.

## Security keys and passkeys

On macOS, WebKit serves security keys (YubiKey and other FIDO keys) and
passkeys only to browsers Apple has granted its browser public-key-credential
entitlement, which Tern doesn't have. When a page's security key or passkey
request is refused, the browser block shows a note under its toolbar with an
**Open in default browser** button, which opens the page in your system
browser, where you can sign in with the key. The note closes with its ✕
button and goes away when the page loads again. Silent passkey autofill
requests (`mediation: "conditional"`) and requests the page aborts itself
don't show it. Linux and Windows browser blocks don't show the note.

## State and examples

`tern ctl state` reflects the new block through `focused.id`,
`focused.label`, `panes` and the tab's pane count. `focused_element` shows
address-field focus. There is no dedicated browser-page entry in `state`;
use `tern ctl stats` and its `webviews` entries for the reported address,
title and native-page focus. Page errors and navigation controls are visible
in the block itself.

This toolbar scene follows `browser-toolbar.txt` in Tern's goldens:

```text
ready
browser open "example.com"
webview ".tn-pane.on .kit-web-page" url "https://example.com/"
webview ".tn-pane.on .kit-web-page" title "Example Domain"
webview ".tn-pane.on .kit-web-page" history true false
webview ".tn-pane.on .kit-web-page" loading 1
browser address
shot browser-toolbar
```

## See also

- [Harness Commands](harness.md): page reports, input and screenshots.
- [Control Commands](control.md): inspecting web views with `stats`.
- [Pictures in Picture](pip.md): floating browser blocks.
- [Debugging](../guides/debugging.md): driving a window from a script.
