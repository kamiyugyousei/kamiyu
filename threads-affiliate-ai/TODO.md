# TODO — Threads Affiliate AI

## PHASE 1 (MVP: 楽天のみ / AUTO_PUBLISH=false)
- [x] プロジェクト構成 / docs (architecture, AGENTS, .env.example)
- [x] Config (pydantic-settings)
- [x] Database engine/session + 全テーブルモデル
- [x] Integrations: threads / rakuten / a8(枠) / browser (キー無しでもモック稼働)
- [x] Agents: chief_manager / chrome_researcher / keyword_discovery / viral_analyst /
      purchase_intent / product_hunter / rakuten_agent / affiliate_matcher /
      copywriter / compliance / conversation / experiment / growth_manager
- [x] Services: pipeline (日次生成) + audit log + similarity
- [x] Dashboard: スマホ対応トップ + 承認カード + 承認/修正/却下/後で API
- [x] Scheduler (APScheduler)
- [x] Tests (pytest) + 手動実行スクリプト
- [x] 「旅行便利グッズ」初回テスト実行

## PHASE 2
- [ ] A8.net agent 本実装 (提携済み案件/SNS条件/広告リンク)。判断不能はHuman Queue。

## PHASE 3
- [ ] Growth Manager 成果分析の可視化強化 / Weekly Report

## PHASE 4
- [ ] Keyword自動進化 (status遷移 exploring→active→winner→declining)
- [ ] Winning Pattern DB 蓄積・活用
- [ ] Reverse Research (Revenue→Research フィードバック)

## PHASE 5
- [ ] 条件付き AUTO_PUBLISH (勝ちパターンのみ、初期OFF維持)

## 運用メモ
- 実行: `python -m app.main`  → ダッシュボード http://localhost:8000
- 1回だけ生成: `python -m app.run_once "旅行便利グッズ"`
- テスト: `pytest -q`
