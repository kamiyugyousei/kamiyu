# kamiyu

Obsidian Vault 兼 GitHub リポジトリです。Obsidian Git プラグインで自動的にコミット・プッシュ・プルし、複数端末で同期します。

## フォルダ構成

| フォルダ | 用途 |
|---|---|
| `00_Inbox/` | 新規ノートの作成先。未整理のメモ置き場 |
| `10_Notes/` | 整理済みのノート |
| `20_Daily/` | デイリーノート（`YYYY-MM-DD.md`） |
| `90_Templates/` | テンプレート（`Daily`, `Note`） |
| `99_Attachments/` | 画像・PDF などの添付ファイル |
| `.obsidian/` | 共有する Obsidian 設定 |

## セットアップ

### PC（Windows / Mac）

1. Git をインストール（Windows は [Git for Windows](https://git-scm.com/download/win)）
2. リポジトリをクローン
   ```bash
   git clone https://github.com/kamiyugyousei/kamiyu.git
   ```
   認証は GitHub Desktop か `gh auth login`、または Personal Access Token を使います。
3. Obsidian で「フォルダを保管庫として開く」→ クローンした `kamiyu` フォルダを選択
4. 設定 → コミュニティプラグイン → 制限モードをオフ → 「閲覧」で **Git**（作者: Vinzent）をインストールして有効化
   - 設定（10分ごとの自動コミット・プッシュ、起動時のプル）はリポジトリに含まれているので、そのまま反映されます

### スマホ（iOS / Android）

Obsidian Git はモバイルでも動きますが、動作が重い場合があります。

1. Obsidian で空の保管庫を作成
2. コミュニティプラグインの **Git** をインストール
3. 設定で GitHub ユーザー名と Personal Access Token（`repo` 権限、Fine-grained なら Contents: Read and write）を入力
4. コマンドパレット →「Git: Clone an existing remote repo」→ `https://github.com/kamiyugyousei/kamiyu.git`

## 同期の注意

- 同じノートを複数端末で同時に編集するとコンフリクトが起きることがあります。編集前にプル（自動）されるのを待ってから書き始めると安全です。
- `workspace.json` など端末固有のファイルは `.gitignore` で同期対象外にしています。
- プラグイン本体（`main.js` 等）は各端末でインストールし、設定（`data.json`）だけ共有します。
