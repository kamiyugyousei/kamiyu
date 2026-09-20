# Architecture — Threads Affiliate AI 社員チーム

## 目的
Threads 上の会話を調査し、消費者の悩み・購買意図を発見して楽天/A8 の商品をマッチング、
オリジナル投稿を作成し、人間の承認後に投稿、成果を分析して翌日の戦略を自動改善する
「AI社員によるアフィリエイト運営会社」。単純な投稿BOTではない。

## 全体像 (PDCA ループ)

```
  06:00 Daily Research (Chrome Market Researcher)
        └ Threadsの話題・伸びてる投稿を調査 (robots/ToS尊重, CAPTCHA回避禁止)
  07:00 Keyword Discovery
        └ 投稿から Problem/Purchase/Emotion/Comparison/Season キーワード抽出 → DB保存
  08:00 Purchase Intent + Product Matching
        └ 悩み→需要→商品 の順で楽天検索(公式API優先) → Affiliate Score(100点)
  09:00 Content Generation
        └ Copywriter が各商品3案 → Compliance(90点) → Approval Queue
   日中  承認された投稿を MIN_POST_INTERVAL で分散投稿 (AUTO_PUBLISH=false なら承認待ち)
  23:00 Daily Analysis (Growth Manager)
        └ カテゴリ/Hook/価格帯/商品/ASP/時間 別に成果分析
  00:00 Strategy Update
        └ 翌日の Research予算・カテゴリ配分・投稿構成を再計算 (探索枠20%以上維持)
```

## レイヤー構成

| レイヤー | 役割 | 主要ファイル |
|---|---|---|
| Config | .env読み込み・全パラメータ | `app/config.py` |
| Database | SQLAlchemy engine/session | `app/database/` |
| Models | ORMモデル (30章のテーブル) | `app/models/` |
| Schemas | Pydantic I/O | `app/schemas/` |
| Integrations | 外部連携。**キー無しでもモックで動く** | `app/integrations/` |
| Agents | AI社員(各役割1クラス) | `app/agents/` |
| Services | パイプライン統合・監査ログ | `app/services/` |
| Scheduler | APScheduler 日次ジョブ | `app/scheduler/` |
| Dashboard | FastAPI + スマホUI + 承認API | `app/dashboard/` |

## AI社員 (Agents)

| # | Agent | 入力 | 出力 |
|---|---|---|---|
| 01 | Chief Manager | 前日成果 | 本日の DailyStrategy(投稿構成/カテゴリ配分/時間) |
| 02 | Chrome Researcher | seed keywords | 調査済み投稿(トレンド/悩み) |
| 03 | Keyword Discovery | 調査投稿 | 分類済み新キーワード → DB |
| 04 | Viral Analyst | 伸びた投稿 | Hookパターン(コピー禁止・構造のみ) |
| 05 | Purchase Intent | 投稿/悩み | purchase_intent_score(0-100) |
| 06 | Product Hunter | 高意図テーマ | 商品候補(楽天優先) |
| 07 | Rakuten Agent | キーワード | 5-10商品(公式API優先) |
| 08 | Affiliate Matcher | 商品+トレンド | Affiliate Score(100点), 70未満は不採用 |
| 09 | Copywriter | 商品+Hook | 投稿3案(A共感/B解決/C発見)。虚偽体験談禁止 |
| 10 | Compliance | 投稿 | compliance_score, 90未満は不投稿 |
| 11 | Conversation | トレンド | 会話喚起投稿(PHASE後半で強化) |
| 12 | Experiment | - | 新Hook/新構造テスト(A/B) |
| 13 | Growth Manager | 成果DB | 分析 + 翌日戦略 |

## 設計原則
- **悩み→需要→商品** の順（商品ありきにしない）
- **コピー禁止**: 元投稿は市場需要/構造分析のみ。生成は完全オリジナル。Semantic類似度チェック。
- **虚偽体験談禁止**: 未使用商品に「使ってみた」を書かない。事実ベース表現(レビュー多数等)。
- **安全**: CAPTCHA/2FA/アクセス制限回避禁止。規約違反スクレイピング禁止。判断不能はHuman Approval Queueへ。
- **KPIは投稿数でなく1投稿あたり利益** (Revenue Per Post, CTR, CVR, Revenue/1000imp...)。
- **探索枠20%以上維持**: 1カテゴリ100%集中禁止。

## PHASE ロードマップ
- **PHASE 1 (現在)**: 楽天のみ。Research→Keyword→Intent→楽天→投稿3案→Compliance→Dashboard→人間承認→(承認後)Threads投稿。
- **PHASE 2**: A8.net 追加。
- **PHASE 3**: 成果分析(Growth Manager 完全稼働)。
- **PHASE 4**: Keyword自動進化 / Winning Pattern / Reverse Research。
- **PHASE 5**: 条件付き AUTO_PUBLISH(初期OFF)。
