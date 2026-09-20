"""AI社員07 — Rakuten Agent.

楽天公式APIを優先して商品を取得(最低5、可能なら10)。取得情報を Product として保存。
APPLICATION_ID未設定時は integration がモックへフォールバック(degraded)。
"""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.config import settings
from app.integrations import rakuten
from app.schemas import ProductCandidate


class RakutenAgent(BaseAgent):
    name = "rakuten_agent"

    def search(
        self, db: Session, keyword: str, run_id: str, hits: int = 10
    ) -> List[ProductCandidate]:
        products = rakuten.search_products(keyword, hits=hits)
        degraded = not settings.rakuten_enabled
        self.log(
            db,
            "search",
            f"'{keyword}' で{len(products)}商品を取得"
            + ("（APIキー未設定のためモック）" if degraded else ""),
            degraded=degraded,
            run_id=run_id,
        )
        return products
