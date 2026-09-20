# AGENTS.md — AI社員仕様 (for Codex / Claude Code)

各 Agent は `app/agents/*.py` に 1 クラスで実装。共通契約:
`run(ctx: PipelineContext) -> AgentResult` を持ち、AuditLog に開始/終了/主要判断を記録する。

失敗時共通ポリシー:
- 外部APIエラー → リトライ(指数バックオフ)後、モックにフォールバックし `degraded=True` で継続。
- 判断不能(規約同意/提携申請/2FA/CAPTCHA/金銭契約/法的判断/権限付与) → **停止して Human Approval Queue** へ。回避しない。

---

## 01. Chief AI Manager (`chief_manager.py`)
- **目的**: 全社員の統括。前日成果を見て本日の投稿計画(DailyStrategy)を決定。
- **Input**: 前日の post_performance / daily_strategy、設定値。
- **Output**: DailyStrategy(投稿構成 affiliate/value/conversation/experiment、注力カテゴリ配分、投稿時間割)。
- **権限**: 各 Agent へタスク配分。DBへ DailyStrategy 書込。
- **禁止**: 探索枠20%未満への圧縮、1カテゴリ100%集中。
- **Failure**: 前日データ無し → 初期推奨構成(4/3/2/1)で開始。

## 02. Chrome Market Researcher (`chrome_researcher.py`)
- **目的**: Threadsで「今ユーザーが何を話しているか」を発見。固定語検索で終わらない。
- **Input**: seed/active keywords。
- **Output**: posts_researched(本文要約・エンゲージ指標・URL)。
- **権限**: browser integration (Playwright) 経由。robots/ToS尊重。
- **禁止**: CAPTCHA回避 / ログイン制限回避 / 規約違反スクレイピング。公式APIが適する処理はAPI優先。
- **Failure**: browser無効/失敗 → モック調査データで継続 (degraded)。

## 03. Keyword Discovery (`keyword_discovery.py`)
- **目的**: 調査投稿から新検索語を抽出・分類し自動拡張(30→50→100→200)。
- **Input**: posts_researched。
- **Output**: keywords(category, scores, status=exploring)。
- **禁止**: 成果ゼロ語の永久検索。status で優先度自動調整。

## 04. Viral Analyst (`viral_analyst.py`)
- **目的**: 伸びた投稿を「なぜ伸びたか」で構造分析。Hook/Problem/Emotion/Story/Benefit/Curiosity/CTA/Discussion。
- **Output**: Hook パターン分類(知らないと損型/失敗談型/比較型...)。
- **禁止**: 本文コピー、特徴的文章の流用。構造のみ抽出。

## 05. Purchase Intent (`purchase_intent.py`)
- **目的**: 投稿/悩みが購買につながるか判定。
- **Output**: purchase_intent_score(0-100)。「楽しかった」より「充電口足りず困った」を高評価。

## 06. Product Hunter (`product_hunter.py`)
- **目的**: 高購買意図テーマの商品探索。楽天優先→A8→(将来 Amazon/もしも/バリュコマ/Yahoo)。
- **Output**: products 候補。

## 07. Rakuten Agent (`rakuten_agent.py`)
- **目的**: 楽天公式API優先で商品取得(名前/価格/説明/レビュー/件数/画像/ショップ/URL/アフィリURL/ジャンル/送料)。最低5、可能なら10。
- **Failure**: APPLICATION_ID 未設定 → モック商品で継続 (degraded)。

## 08. Affiliate Matcher (`affiliate_matcher.py`)
- **目的**: 商品を100点満点で採点。TrendFit25/PurchaseIntent20/Relevance20/Review10/Price10/Economics10/Season5。
- **Output**: affiliate_score。**70未満は原則不採用**。

## 09. Threads Copywriter (`copywriter.py`)
- **目的**: 各商品最低3案(A共感/B問題解決/C発見)。
- **禁止**: 未使用商品の虚偽体験談。事実ベース(レビュー多数/こういう悩みの人に候補)で表現。
- **構造**: HOOK→Problem→Empathy→Solution→Product→Benefit→CTA→PR表記→Affiliate Link。毎回同構造にしない。
- **チェック**: 既存投稿との Semantic 類似度 > COPY_SIMILARITY_THRESHOLD は破棄・再生成。

## 10. Compliance Officer (`compliance.py`)
- **目的**: 投稿前全チェック(PR表記/アフィリ表示/虚偽/価格/商品情報/体験捏造/コピー/誇大/ASP規約/SNS条件/URL/NG商品)。
- **Output**: compliance_score。**90未満は不投稿**。

## 11. Conversation Agent (`conversation_agent.py`)
- **目的**: 会話喚起投稿を生成。返信から新しい悩み/需要/キーワードを発見。

## 12. Experiment Agent (`experiment_agent.py`)
- **目的**: 毎日1件、新Hook/新カテゴリ/新価格帯/新構造をテスト。A/Bデータ保存。

## 13. Growth Manager (`growth_manager.py`)
- **目的**: 日次分析(カテゴリ/Hook/価格帯/商品/ASP/時間別)→ 翌日戦略・Winning Pattern・Reverse Research。
- **禁止**: 1カテゴリ100%集中。探索枠20%以上維持。
