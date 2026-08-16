# DeepSeek Harness Token Usage & Cost Dashboard

一个直接嵌入 DeepSeek Harness 客户端的 Token 用量与费用统计插件。

它会在侧边栏「设置」按钮上方显示一张轻量卡片，展示当前模型、当前会话 Token 用量和估算费用；点击卡片后打开应用内弹窗，查看全部模型/会话的详细统计。

## ✨ 功能特性

- **轻量卡片**
  - 显示当前模型（如 `deepseek-v4-pro`）
  - 显示当前会话 Token 总量
  - 显示当前会话估算费用
  - 位于侧边栏设置按钮上方，随当前会话切换自动更新

- **完整弹窗统计**
  - 总会话数、总 Token、输入(未缓存)、缓存读取、输出、总估算费用
  - 按模型统计：模型、Provider、会话数、输入、缓存读取、输出、费用
  - 按会话统计：标题、工作区、模型、Token 明细、费用
  - CNY / USD 一键切换
  - 数据实时来自 DSH 本地 API（`session.list` / `session.models` / `session.history`）

- **开源友好**
  - 纯前端客户端插件，无服务器逻辑，无外部依赖
  - 模型价格内置自 DSH 本地 pi-ai 价格库，离线可用
  - 未定价模型会明确显示「未定价/免费」

## 📦 一键安装

### macOS / Linux

```bash
cd token-usage-plugin
./install.sh
```

### Windows

在 PowerShell 中执行以下等效操作：

```powershell
$src = "$PWD\token-usage-plugin"
$dst = "$HOME\.dsh\profiles\node_modules\@deepseek-ai"
New-Item -ItemType Directory -Force -Path "$dst\dsh-token-usage\lib" | Out-Null
Copy-Item "$src\package.json" "$dst\dsh-token-usage\"
Copy-Item "$src\lib\client.js" "$dst\dsh-token-usage\lib\"
Copy-Item "$src\lib\index.js" "$dst\dsh-token-usage\lib\"
$patch = "$HOME\.dsh\profiles\web\cordis.patch.yml"
if (-not (Select-String -Path $patch -Pattern "dsh-token-usage" -Quiet)) {
  Add-Content $patch "`n- insert:`n    - id: token-usage`n      name: '@deepseek-ai/dsh-token-usage'"
}
```

安装后重启 DeepSeek Harness 客户端即可。

## ✅ 安装后验证

1. 打开 DeepSeek Harness 客户端
2. 进入「设置」->「插件列表」
3. 应能看到 `dsh-token-usage`
4. 返回主界面，侧边栏设置按钮上方会出现 Token 用量卡片

## 🔧 手动安装（开发模式）

把本仓库的 `token-usage-plugin` 目录复制为：

```
~/.dsh/profiles/node_modules/@deepseek-ai/dsh-token-usage
```

并在 `~/.dsh/profiles/web/cordis.patch.yml` 追加：

```yaml
- insert:
    - id: token-usage
      name: '@deepseek-ai/dsh-token-usage'
```

## 📁 目录结构

```
token-usage-plugin/
├── install.sh        # 一键安装脚本
├── uninstall.sh      # 卸载脚本
├── package.json      # DSH 插件元数据
├── README.md         # 本说明
└── lib/
    ├── client.js     # 客户端 UI 插件（卡片 + 弹窗 + 数据统计）
    └── index.js      # 宿主侧空实现，用于进入插件加载图
```

## 🧩 工作原理

- 插件通过 DSH 客户端模块系统加载，因此在「插件列表」中可见
- 客户端插件挂载到 DOM，监听侧边栏设置按钮，插入卡片
- 点击卡片后调用 DSH 本地 RPC API 获取会话列表、模型信息和完整会话历史
- 在浏览器内解析 `assistant/chunk` 中的 `usage` 事件，按模型/会话/天聚合
- 价格计算使用本地 pi-ai 价格库（USD / 1M tokens），可选 CNY/USD 显示

## 🛠 常见问题

### 插件列表看不到？

- 确认已重启 DeepSeek Harness 客户端
- 确认 `~/.dsh/profiles/node_modules/@deepseek-ai/dsh-token-usage` 存在
- 确认 `~/.dsh/profiles/web/cordis.patch.yml` 中包含 `dsh-token-usage`

### 卡片没有出现？

- 插件列表若显示 `failed`，请打开浏览器开发者工具查看报错
- 当前会话若为空（新会话），卡片会显示 0 Token 和「暂无用量」，这是正常现象

### 费用为什么不准确？

- 模型价格来自本地 pi-ai 价格库；未覆盖的模型会显示「未定价/免费」
- 费用是估算值，实际扣费以模型服务商账单为准

## 📄 License

MIT


---

# DeepSeek Harness Token Usage & Cost Dashboard (English)

A token usage and cost statistics plugin that embeds directly into the DeepSeek Harness desktop client.

It shows a lightweight card above the **Settings** button in the sidebar with the current model, current session token usage, and estimated cost. Clicking the card opens an in-app modal with full per-model and per-session statistics.

## ✨ Features

- **Lightweight card**
  - Shows the current model (e.g. `deepseek-v4-pro`)
  - Shows the current session total token count
  - Shows the estimated cost of the current session
  - Automatically updates when the selected session changes

- **Full statistics modal**
  - Total sessions, total tokens, uncached input, cache reads, output, and estimated cost
  - Per-model statistics: model, provider, session count, input, cache read, output, cost
  - Per-session statistics: title, workspace, model, token breakdown, cost
  - CNY / USD currency toggle
  - Real-time data from DSH local APIs (`session.list` / `session.models` / `session.history`)

- **Open-source friendly**
  - Pure client-side plugin, no server logic, no external dependencies
  - Model prices are bundled from the local DSH pi-ai pricing database, works offline
  - Unpriced models are explicitly shown as “unpriced / free”

## 📦 One-Click Install

### macOS / Linux

```bash
cd token-usage-plugin
./install.sh
```

### Windows

Run the equivalent PowerShell commands from `README.md` (Chinese section above).

Restart DeepSeek Harness after installation.

## ✅ Verification

1. Open DeepSeek Harness.
2. Go to **Settings → Plugin Inventory**.
3. You should see `dsh-token-usage`.
4. Return to the main screen; the token usage card should appear above the Settings button.

## 🔧 Manual Install (Development)

Copy this repository's `token-usage-plugin` directory to:

```
~/.dsh/profiles/node_modules/@deepseek-ai/dsh-token-usage
```

Then append to `~/.dsh/profiles/web/cordis.patch.yml`:

```yaml
- insert:
    - id: token-usage
      name: '@deepseek-ai/dsh-token-usage'
```

## 🧩 How It Works

- The plugin is loaded through the DSH client module system, so it appears in the plugin inventory.
- The client plugin mounts to the DOM, watches the sidebar settings button, and inserts the card.
- Clicking the card calls DSH local RPC APIs to get session lists, model information, and full session history.
- The browser parses `assistant/chunk` `usage` events and aggregates by model/session/day.
- Cost calculation uses the local pi-ai pricing database (USD / 1M tokens), with optional CNY/USD display.

## 🛠 FAQ

### The plugin is not visible in the plugin list?

- Make sure DeepSeek Harness has been restarted.
- Make sure `~/.dsh/profiles/node_modules/@deepseek-ai/dsh-token-usage` exists.
- Make sure `~/.dsh/profiles/web/cordis.patch.yml` contains `dsh-token-usage`.

### The card does not appear?

- If the plugin shows `failed` in the plugin inventory, open the browser developer tools and check for errors.
- If the current session is blank (new session), the card will show 0 tokens and “no usage”, which is expected.

### Why is the cost inaccurate?

- Prices come from the local pi-ai pricing database; models not covered are shown as “unpriced / free”.
- The cost is an estimate. Actual billing is determined by your model provider.

## 📄 License

MIT
