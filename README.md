# kamiyu

## Chrome MCP 接続

Chrome を MCP（Model Context Protocol）経由で Claude Code から操作できるように設定しています。
ブラウザの起動・ページ遷移・DOM やコンソールの取得・スクリーンショットなどを AI から実行できます。

### 前提

- Node.js 20 以上（`npx` が使えること）
- Google Chrome がインストールされていること

### 設定内容

リポジトリ直下の [`.mcp.json`](./.mcp.json) に、Google 公式の
[chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) サーバーを登録しています。

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

### 使い方

1. このリポジトリを開いた状態で Claude Code（CLI / IDE 拡張）を起動します。
2. プロジェクトスコープの MCP サーバーとして `chrome-devtools` が検出されるので、初回は接続を許可します。
   - CLI では `/mcp` コマンドで接続状態を確認できます。
3. 許可すると `npx` 経由で `chrome-devtools-mcp` が起動し、Chrome を操作するツールが利用可能になります。

### 補足

- `chrome-devtools-mcp` は起動時にヘッドレスまたは通常の Chrome を自動で立ち上げます。
  既存の Chrome を使いたい場合は `--browserUrl`（リモートデバッグ用エンドポイント）などの
  引数を `.mcp.json` の `args` に追加してください。
- Playwright ベースのブラウザ操作が必要な場合は、代わりに
  [`@playwright/mcp`](https://github.com/microsoft/playwright-mcp) を登録する方法もあります。
