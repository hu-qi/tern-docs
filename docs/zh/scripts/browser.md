# 浏览器 block {#browser-blocks}

浏览器命令可以在终端旁打开网页，并聚焦其地址栏。把它们与 `webview` 报告配合使用，
即可在无头脚本中构造出页面的标题、加载状态与导航控件，而无需抓取真实网站。

## 打开与地址定位 {#opening-and-addressing}

| 命令 | 作用 |
| --- | --- |
| `browser open [<address or search>...]` | 在聚焦面板旁打开一个浏览器 block。不带输入时，打开空白页面并聚焦其地址栏。 |
| `browser address` | 聚焦当前浏览器 block 的地址栏并选中其中的文本，相当于 ⌘L。 |

`open` 会把其余所有单词用空格连接起来。含空格的地址或搜索词建议加引号。
首尾空白会被去掉；输入为空则打开空白页面。显式写出的 scheme 会保留，
带点的主机名会补上 `https://`，`localhost` 或 IP 地址会补上 `http://`。
其他文本则作为网页搜索。

当聚焦面板不是浏览器 block 时，`address` 不做任何事。它的解析器同样接受并忽略后续
单词；这些单词没有实际作用。两个命令都会等待 450 ms 后视为完成。这并不是真正的
页面加载等待：这一组命令里没有浏览器就绪命令，也没有网络超时。它们不限于桌面版本，
但在 Web 客户端中不会运行。

## 上报页面 {#reporting-a-page}

无头运行时显示的是页面卡片，而不是原生 Web 视图。`webview` 发送原生页面会报告的
事件；它不加载网站，也不执行网站的 JavaScript。该命令在实时窗口中同样可用。

| 命令 | 作用 |
| --- | --- |
| `webview <selector> title <text>` | 上报页面标题。 |
| `webview <selector> url <text>` | 上报当前地址，例如重定向之后。 |
| `webview <selector> loading <progress>` | 上报 `0` 到 `1` 之间的加载进度；`1` 表示加载完成。 |
| `webview <selector> failed <message>` | 上报加载失败并结束加载。 |
| `webview <selector> history <true\|false> <true\|false>` | 按顺序设置“后退”与“前进”是否可用。 |
| `webview <selector> focus <on\|off>` | 上报页面是否拥有键盘焦点。 |
| `webview <selector> new-window <url>` | 上报打开另一个页面的请求；通常会在本 block 旁打开一个浏览器 block。 |
| `webview <selector> inspector-page <url>` | 把页面的 Web Inspector 上报为位于该地址的页面（WPE WebKit 的 inspector 服务器）；并在此 block 旁打开一个指向它的浏览器 block。 |
| `webview <selector> inspector-unavailable <message>` | 上报页面的 Web Inspector 无法在 Tern 中打开；以 toast 形式显示该消息。 |
| `webview <selector> security-key` | 上报页面请求了安全密钥或 passkey（WebAuthn）而引擎拒绝了该请求；在工具栏下方显示提示，提供 **Open in default browser**。 |
| `webview <selector> media-blocked <hint>` | 上报页面尝试播放引擎无法加载的音频或视频（Linux 上的 WebKitGTK）；在工具栏下方的提示中显示该 hint，并提供 **Open in default browser**。 |

选择器指向第一个带 Web 视图的匹配元素。聚焦的浏览器 block 使用
`".tn-pane.on .kit-web-page"`；浮动浏览器使用 `".tn-pane.pip .kit-web-page"`。
格式错误的选择器，或找不到匹配 Web 视图的选择器，都会使命令失败。文本形式需要且仅
需要一个参数，因此含空格的标题、消息和 URL 要加引号。进度超出 `0`–`1`、缺少参数
以及无效标志同样会失败。

报告的生效无需等待真实页面加载完成。URL 为空或为 `about:blank` 的报告不会改变
已存的地址。低于 `1` 的进度报告会开始或继续加载；在加载结束后再次开始加载会清除
先前的错误。标题、URL、进度、失败与历史报告会更新会话中的页面，因此该会话的其他
窗口也能看到。对于由浏览器自动化驱动的浏览器，`new-window` 会被记录为一条报告，
而不是打开一个 block。

## 安全密钥与 passkey {#security-keys-and-passkeys}

在 macOS 上，WebKit 只向已获得 Apple 浏览器公钥凭据授权
（browser public-key-credential entitlement）的浏览器提供安全密钥（YubiKey 及其他
FIDO 密钥）与 passkey，而 Tern 没有该授权。当页面请求的安全密钥或 passkey 被拒绝
时，浏览器 block 会在工具栏下方显示一条提示，附带 **Open in default browser** 按钮，
点击后会在系统浏览器中打开该页面，可在那里用密钥登录。提示可用其 ✕ 按钮关闭，
页面再次加载时也会消失。静默的 passkey 自动填充请求（`mediation: "conditional"`）
以及页面自行中止的请求不会显示它。Linux 与 Windows 的浏览器 block 不显示该提示。

## 状态与示例 {#state-and-examples}

`tern ctl state` 通过 `focused.id`、`focused.label`、`panes` 以及标签页的面板数量
反映新打开的 block。`focused_element` 显示地址栏的焦点。`state` 中没有专门的浏览器
页面条目；要查看上报的地址、标题与原生页面焦点，请使用 `tern ctl stats` 及其
`webviews` 条目。页面错误与导航控件在 block 本身即可见。

下面的工具栏场景对应 Tern goldens 中的 `browser-toolbar.txt`：

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

## 另见 {#see-also}

- [Harness 命令](harness.md)：页面报告、输入与截图。
- [控制命令](control.md)：用 `stats` 检查 Web 视图。
- [画中画](pip.md)：浮动的浏览器 block。
- [调试](../guides/debugging.md)：从脚本驱动窗口。
