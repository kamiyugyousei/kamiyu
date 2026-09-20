"""AI社員05 — Purchase Intent Agent.

投稿/悩みが購買につながるかを 0-100 で判定。「楽しかった」より
「充電口が足りず困った」のような具体的な悩みを高く評価する。
悩み→需要→商品 の順を担保するための入口。
"""
from __future__ import annotations

from typing import List, Tuple

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models import Keyword
from app.schemas import ResearchFinding

PROBLEM_SIGNALS = [
    "困った", "足りない", "できない", "面倒", "収納", "かさばる", "重い",
    "乾かない", "眠れない", "時間がない", "疲れる", "暑い", "寒い", "充電",
]
PURCHASE_SIGNALS = [
    "買って", "おすすめ", "欲しい", "便利", "コスパ", "リピート", "セール",
    "クーポン", "安い", "楽天",
]
NEGATIVE_SIGNALS = ["楽しかった", "きれいだった", "最高の思い出", "行ってきた"]


class PurchaseIntent(BaseAgent):
    name = "purchase_intent"

    def score_text(self, text: str) -> float:
        score = 30.0
        score += 8.0 * sum(1 for s in PROBLEM_SIGNALS if s in text)
        score += 6.0 * sum(1 for s in PURCHASE_SIGNALS if s in text)
        score -= 10.0 * sum(1 for s in NEGATIVE_SIGNALS if s in text)
        return float(max(0.0, min(100.0, score)))

    def rank_problems(
        self, db: Session, findings: List[ResearchFinding], run_id: str, top_n: int = 5
    ) -> List[Tuple[str, float, ResearchFinding]]:
        scored: List[Tuple[str, float, ResearchFinding]] = []
        for f in findings:
            text = f"{f.summary} {f.detected_problem}"
            s = self.score_text(text)
            f_intent = s
            scored.append((f.detected_problem or f.keyword, f_intent, f))
            # write intent back onto keyword
            kw = db.query(Keyword).filter(Keyword.keyword == f.keyword).one_or_none()
            if kw:
                kw.purchase_intent_score = max(kw.purchase_intent_score, s)

        # dedupe by problem, keep highest intent
        best: dict[str, Tuple[str, float, ResearchFinding]] = {}
        for problem, s, f in scored:
            key = problem or f.keyword
            if key not in best or s > best[key][1]:
                best[key] = (problem, s, f)
        top = sorted(best.values(), key=lambda x: x[1], reverse=True)[:top_n]
        self.log(
            db,
            "rank_problems",
            "購買意図TOP: "
            + "; ".join(f"{p}({s:.0f})" for p, s, _ in top),
            run_id=run_id,
        )
        return top
