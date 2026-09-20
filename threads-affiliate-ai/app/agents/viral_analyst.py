"""AI社員04 — Viral Research Agent.

伸びた投稿を「なぜ伸びたか」で構造分析し Hook パターンを分類する。
本文はコピーしない — 構造だけを抽出する。
"""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.schemas import ResearchFinding

HOOK_PATTERNS = [
    ("知らないと損型", ["知らな", "損", "情報"]),
    ("失敗談型", ["失敗", "後悔", "困った", "足りな", "できな"]),
    ("もっと早く知りたかった型", ["もっと早く", "早く知り"]),
    ("比較型", ["比較", "どっち", "vs", "より"]),
    ("ランキング型", ["ランキング", "best", "トップ", "選"]),
    ("悩み解決型", ["解決", "悩み", "対策", "改善"]),
    ("意外性型", ["まさか", "意外", "実は", "天才"]),
    ("質問型", ["？", "?", "ありますか", "どこ"]),
    ("共感型", ["わかる", "あるある", "共感", "同じ"]),
    ("季節型", ["夏", "冬", "梅雨", "旅行", "年末", "新生活"]),
    ("ギフト型", ["ギフト", "プレゼント", "贈"]),
    ("レビュー型", ["レビュー", "使ってみ", "口コミ", "評価"]),
]


class ViralAnalyst(BaseAgent):
    name = "viral_analyst"

    def classify_hook(self, text: str) -> str:
        for label, keys in HOOK_PATTERNS:
            if any(k in text for k in keys):
                return label
        return "悩み解決型"

    def analyze(
        self, db: Session, findings: List[ResearchFinding], run_id: str
    ) -> List[ResearchFinding]:
        # rank by engagement, tag hook types (structure only, no copying)
        ranked = sorted(
            findings,
            key=lambda f: f.likes + f.replies * 3 + f.reposts * 2,
            reverse=True,
        )
        for f in ranked:
            f.hook_type = self.classify_hook(f.summary + " " + f.detected_problem)
        top = ranked[: min(10, len(ranked))]
        self.log(
            db,
            "analyze",
            f"上位{len(top)}投稿のHookパターンを分類 "
            + ", ".join(sorted({f.hook_type for f in top})),
            run_id=run_id,
        )
        return ranked
