# 常時稼働サーバー設置ガイド（24時間自動運転）

このシステムを **24時間動くサーバー** に置く手順です。置いてしまえば、
毎朝のリサーチ→商品検索→投稿候補づくり→夜の分析までを**毎日自動**で回します。
あなたの作業は「スマホでダッシュボードを開いて承認する」だけになります。

> 投稿は必ずあなたの承認が前提です（`AUTO_PUBLISH=false`）。勝手に投稿はしません。

---

## いちばん簡単な方法：Render.com（推奨）

GitHub連携で、画面のボタン中心で設置できます。このリポジトリには設定ファイル
`render.yaml` を入れてあるので、ほぼ自動で構成されます。

### 費用の目安
- **Starterプラン 約 $7/月**（24時間止まらない）＋ **永続ディスク 1GB 約 $0.25/月**
- ※無料プランもありますが「15分アクセスが無いと休眠」「再起動でデータ消滅」のため、
  自動運転や売上データ蓄積には向きません。**まずStarter推奨**。

---

### 手順（15〜20分）

#### 1. Renderアカウントを作る
- https://render.com/ にアクセス →「Get Started」
- **GitHubアカウントでサインアップ**（連携が楽になります）

#### 2. GitHubと接続
- サインアップ時に GitHub 連携を許可
- リポジトリ `kamiyugyousei/kamiyu` へのアクセスを許可

#### 3. Blueprint でデプロイ
- Renderの画面右上 **「New +」→「Blueprint」**
- リポジトリ `kamiyugyousei/kamiyu` を選択
- ブランチは **`claude/threads-affiliate-ai-system-15vu5d`** を選ぶ
- `render.yaml` が自動で読み込まれ、サービス名 `threads-affiliate-ai` が表示されます
- **「Apply」** を押す

#### 4. 秘密情報（キー）を入力
デプロイ時に、次の項目の入力を求められます（`render.yaml` には保存されていません）。
分かるものだけ入れればOK：

| 項目 | 入れる値 | 必須？ |
|---|---|---|
| `RAKUTEN_APPLICATION_ID` | 楽天のアプリケーションID | ✅ 必須 |
| `RAKUTEN_AFFILIATE_ID` | 楽天のアフィリエイトID | ✅ 必須 |
| `DASHBOARD_USER` | ログイン名（例：`admin`） | ✅ 推奨 |
| `DASHBOARD_PASSWORD` | **好きなパスワード**（あなただけが知る） | ✅ 推奨 |
| `OPENAI_API_KEY` | OpenAIのキー | 任意（無くても動く） |
| `THREADS_ACCESS_TOKEN` | Threads投稿用 | 後でOK |
| `THREADS_USER_ID` | Threads投稿用 | 後でOK |

> ⚠️ **`DASHBOARD_PASSWORD` は必ず設定してください。** 公開URLなので、
> 設定しないと他人が承認画面を開けてしまいます。設定すると、開くたびに
> ユーザー名とパスワードを聞かれるようになります。

#### 5. 完成 & アクセス
- 数分でビルドが終わり、`https://threads-affiliate-ai-xxxx.onrender.com` のような
  **あなた専用URL**が発行されます
- スマホでそのURLを開く → パスワードを入れる → ダッシュボードが表示されます
- このURLをスマホのホーム画面に追加しておくと、毎日ワンタップで承認できます

#### 6. 最初の投稿候補を作る（動作確認）
自動リサーチは毎朝9時（日本時間）に走りますが、すぐ試したい場合は
Renderの **「Shell」** タブを開いて次を実行：
```bash
python -m app.run_once "旅行便利グッズ"
```
→ ダッシュボードを再読み込みすると承認待ちが10件出ます。

---

## 自動スケジュール（毎日勝手に動く内容）

`render.yaml` で常時起動しているので、以下が**毎日自動**で回ります（日本時間）：

| 時刻 | 内容 |
|---|---|
| 09:00 | 市場調査→キーワード発見→楽天商品検索→投稿候補づくり |
| 日中 | 承認済みの投稿を60分間隔で分散投稿 |
| 23:00 | その日の成果を分析 |
| 00:00 | 翌日の戦略を自動更新 |

時刻は Render の環境変数（`CRON_CONTENT_GENERATION` など）で変更できます。

---

## 別の選択肢

### Railway.app（Renderと似た手軽さ）
1. https://railway.app/ でGitHubサインアップ
2. New Project → Deploy from GitHub → このリポジトリ
3. Settings → Root Directory を `threads-affiliate-ai` に
4. Variables に上記のキーを追加
5. `Procfile` を自動認識して起動

### VPS / 自宅サーバー（Dockerがある場合）
```bash
git clone https://github.com/kamiyugyousei/kamiyu.git
cd kamiyu/threads-affiliate-ai
cp .env.example .env   # キーを記入
docker compose up -d
```
→ `http://サーバーのIP:8000` で開けます。

---

## 運用のコツ
- **毎日1回**、スマホでダッシュボードを開いて承認するだけ
- 最初の1〜2週間はデータ集めの期間。少しずつ「勝ちカテゴリ・勝ちHook」が
  分析に出てきて、翌日の戦略が自動で寄っていきます
- Threadsトークンを入れるまでは「承認の練習」だけできます（実投稿はされません）
- 本格的に売上が増えてきたら、SQLite → PostgreSQL への移行も可能です（相談ください）

---

## 困ったとき
| 症状 | 対処 |
|---|---|
| ビルド失敗 | Renderのログを確認。Pythonバージョンは `runtime.txt` で3.12指定済み |
| 商品が「モック」のまま | 楽天の2つのキーが正しく入っているか（環境変数）を確認 |
| ダッシュボードが開けない | `DASHBOARD_USER` / `DASHBOARD_PASSWORD` を確認 |
| データが消えた | 無料プランは消えます。Starter＋ディスク（`render.yaml`で設定済み）を使う |
