# Threads Affiliate AI — AI社員によるアフィリエイト運営チーム

Threads上の会話を調査し、消費者の悩み・購買意図を発見して楽天/A8の商品をマッチング、
オリジナル投稿を作成し、**人間の承認後に**投稿、成果を分析して翌日の戦略を自動改善する
自律型システムです。単なる投稿BOTではなく「売れる市場を探し、自分で改善するAI社員チーム」を目指します。

> あなたの毎日の作業は「スマホで投稿候補を確認して承認する」だけ。

## 特徴
- **悩み→需要→商品** の順で提案(商品ありきにしない)
- **コピー禁止 / 虚偽体験談禁止**: 元投稿は構造分析のみ、生成は完全オリジナル、類似度チェック付き
- **安全第一**: CAPTCHA/2FA/アクセス制限の回避は一切しない。判断不能は人間承認キューへ
- **キー無しでも動く**: 楽天/Threads/OpenAI のキーが無くても end-to-end でモック稼働
- **KPIは1投稿あたり利益**: Revenue/Post, CTR, CVR, カテゴリ/Hook/時間別分析

## セットアップ

```bash
cd threads-affiliate-ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 必要に応じてAPIキーを設定(無くても動く)
```

## 使い方

### 1. パイプラインを1回実行(投稿候補を生成)
```bash
python -m app.run_once "旅行便利グッズ"
```
市場調査 → キーワード発見 → 購買意図TOP5 → 楽天商品検索 → スコアリング →
各商品3案 → コンプライアンス → 承認待ちに保存(※投稿はしない)。

### 2. ダッシュボード起動(スマホで承認)
```bash
python -m app.main
# → http://localhost:8000
```
承認/修正/却下/後で投稿 のボタンで操作。承認したものだけが投稿されます。

### 3. (開発用)成果データを擬似生成して分析を確認
```bash
python -m app.services.simulate
```

### テスト
```bash
pytest -q
```

## アーキテクチャ / エージェント仕様
- 全体設計: [`architecture.md`](architecture.md)
- AI社員の役割/入出力/禁止事項: [`AGENTS.md`](AGENTS.md)
- 進捗: [`TODO.md`](TODO.md)

## 安全と法令順守
- `AUTO_PUBLISH=false`(初期は完全自動投稿を禁止、人間承認必須)
- アフィリエイト投稿には必ず `#PR` 表記とアフィリエイトURLを付与
- A8.net の提携申請・SNS利用条件・規約同意・2FA・CAPTCHA・金銭契約・法的判断は
  自動化せず **Human Approval Queue** へ送られます
- APIキーはソースに書かず `.env` で管理

## PHASE
1. (現在) 楽天のみ・承認フロー・投稿・基本分析
2. A8.net 追加
3. 成果分析強化 / Weekly Report
4. Keyword自動進化 / Winning Pattern / Reverse Research
5. 条件付き AUTO_PUBLISH(初期OFF)
