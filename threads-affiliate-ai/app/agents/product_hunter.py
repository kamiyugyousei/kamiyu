"""AI社員06 — Product Hunter.

高購買意図テーマについて商品を探索。楽天優先→(PHASE2)A8→将来他ASP。
Rakuten Agent を呼び出し、悩みキーワードから商品候補を集める。
"""
from __future__ import annotations

from typing import List, Tuple

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.rakuten_agent import RakutenAgent
from app.schemas import ProductCandidate, ResearchFinding


class ProductHunter(BaseAgent):
    name = "product_hunter"

    def __init__(self) -> None:
        self.rakuten = RakutenAgent()

    def hunt(
        self,
        db: Session,
        problems: List[Tuple[str, float, ResearchFinding]],
        run_id: str,
        hits_per_problem: int = 10,
    ) -> List[Tuple[ProductCandidate, float, str, str]]:
        """Return list of (product, purchase_intent, problem, keyword)."""
        results: List[Tuple[ProductCandidate, float, str, str]] = []
        for problem, intent, finding in problems:
            # search query: prefer specific problem term over generic keyword
            query = self._query_for(problem, finding.keyword)
            products = self.rakuten.search(db, query, run_id, hits=hits_per_problem)
            for p in products:
                results.append((p, intent, problem, finding.keyword))
        self.log(
            db,
            "hunt",
            f"{len(problems)}件の悩みから{len(results)}商品候補を収集",
            run_id=run_id,
        )
        return results

    def _query_for(self, problem: str, keyword: str) -> str:
        problem = (problem or "").strip()
        keyword = (keyword or "").strip()
        if problem and problem not in keyword:
            # 悩み由来の商品検索語 (例: "旅行 充電")
            base = keyword.split()[0] if keyword else ""
            return f"{base} {problem}".strip()
        return keyword or problem
