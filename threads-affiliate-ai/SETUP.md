# セットアップ手順書（初心者向け）

このシステムを **あなたのパソコン** で動かすための手順です。
クラウド開発環境からは楽天APIへの通信が制限されているため、実際の運用は
インターネットに自由につながる環境（あなたのPC / VPS等）で行います。

---

## 0. 必要なもの
- パソコン（Mac または Windows）
- Python 3.11 以上（無ければ https://www.python.org/downloads/ からインストール）
- 楽天の2つのキー（取得済み）
  - アプリケーションID（`RAKUTEN_APPLICATION_ID`）
  - アフィリエイトID（`RAKUTEN_AFFILIATE_ID`）

---

## 1. プロジェクトを取得する

### GitHubから取る場合（推奨）
```bash
git clone https://github.com/kamiyugyousei/kamiyu.git
cd kamiyu/threads-affiliate-ai
git checkout claude/threads-affiliate-ai-system-15vu5d
```

---

## 2. Python環境をつくる

**Mac / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 3. .env を作ってキーを入れる

```bash
cp .env.example .env    # Windowsは copy .env.example .env
```

`.env` をメモ帳等で開き、次の2行を自分の値に書き換えて保存：

```
RAKUTEN_APPLICATION_ID=（あなたのアプリケーションIDを貼る）
RAKUTEN_AFFILIATE_ID=（あなたのアフィリエイトIDを貼る）
```

> ⚠️ キーの実物は絶対にGitHub等へ公開しないでください（`.env` は自動で除外されます）。

> `AUTO_PUBLISH=false` のままにしておけば、承認しない限り絶対に投稿されません。

---

## 4. 動作確認（本物の楽天商品が出るか）

```bash
python -m app.run_once "旅行便利グッズ"
```

- ログに「**モック**」の文字が **出なければ成功**＝本物の楽天につながっています。
- 商品名が実在の商品名になっていればOK。

---

## 5. ダッシュボードを開いて承認する（スマホ可）

```bash
python -m app.main
```

ブラウザで **http://localhost:8000** を開く（同じWi-Fiのスマホからは
`http://（PCのIPアドレス）:8000`）。承認/修正/却下ボタンで操作します。

---

## 6. Threadsに実際に投稿したくなったら（後で）

`.env` に Threads のトークンを追加：
```
THREADS_ACCESS_TOKEN=（Meta開発者サイトで発行）
THREADS_USER_ID=（同上）
```
入れなくても「承認フローの練習」まではできます（ニセ投稿IDになるだけ）。

---

## 7. OpenAIで文章を賢くしたい場合（任意）
`.env` に `OPENAI_API_KEY=` を入れると、投稿文の生成がAIになります。
無くてもテンプレートで動きます。

---

## よくあるつまずき
| 症状 | 対処 |
|---|---|
| `python` が見つからない | `python3` で試す / Pythonを再インストール |
| ログに「モック」が出続ける | `.env` のキーの綴り・前後の空白を確認、保存し直す |
| 403 / タイムアウト | 会社/学校の制限ネットワークだと楽天に繋がらないことがある。家のWi-Fi等で試す |
| ポート8000が使用中 | `.env` の `DASHBOARD_PORT` を 8001 等に変更 |

---

## 24時間自動で回したい場合（発展）
- 常時起動のサーバー（VPS / Render / Railway 等）に置くと、スケジューラ
  （朝リサーチ→商品検索→投稿候補作成→夜分析）が毎日自動で回ります。
- `docker compose up -d` でも起動できます（Dockerがある場合）。
- ただし投稿はあなたの承認が前提（`AUTO_PUBLISH=false`）なので、
  スマホでダッシュボードを開いて承認する運用になります。
