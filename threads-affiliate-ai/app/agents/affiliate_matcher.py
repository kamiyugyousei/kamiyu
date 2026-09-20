"""AI社員08 — Affiliate Product Score / Matcher.

各商品を100点満点で採点(spec section 13):
  Trend Fit 25 / Purchase Intent 20 / Product Relevance 20 /
  Review・Trust 10 / Price Attractiveness 10 / Affiliate Economics 10 / Seasonality 5
70点未満は原則不採用。
"""
from __future__ import annotations

import datetime as dt
import json
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.config import settings
from app.models import Product
from app.schemas import ProductCandidate

_SEASON_MAP = {
    12: ["冬", "クリスマス", "年末", "防寒"], 1: ["冬", "新生活"], 2: ["冬", "花粉"],
    3: ["新生活", "花粉", "春"], 4: ["新生活", "春"], 5: ["母の日", "アウトドア"],
    6: ["梅雨", "父の日"], 7: ["夏", "旅行", "夏休み"], 8: ["夏", "旅行", "アウトドア"],
    9: ["秋", "防災"], 10: ["秋", "アウトドア"], 11: ["冬", "ギフト"],
}


class AffiliateMatcher(BaseAgent):
    name = "affiliate_matcher"

    def score_and_store(
        self,
        db: Session,
        candidates: List[Tuple[ProductCandidate, float, str, str]],
        run_id: str,
    ) -> List[Product]:
        stored: List[Product] = []
        for pc, intent, problem, keyword in candidates:
            score, breakdown = self._score(pc, intent, problem, keyword)
            product = Product(
                provider=pc.provider,
                external_id=pc.external_id,
                name=pc.name,
                price=pc.price,
                description=pc.description,
                review_average=pc.review_average,
                review_count=pc.review_count,
                image_url=pc.image_url,
                shop_name=pc.shop_name,
                product_url=pc.product_url,
                affiliate_url=pc.affiliate_url,
                genre=pc.genre,
                postage_flag=pc.postage_flag,
                keyword=keyword,
                affiliate_score=score,
                score_breakdown=json.dumps(breakdown, ensure_ascii=False),
            )
            db.add(product)
            db.flush()
            stored.append(product)

        passing = [p for p in stored if p.affiliate_score >= settings.min_affiliate_score]
        self.log(
            db,
            "score",
            f"{len(stored)}商品を採点、{len(passing)}商品が{settings.min_affiliate_score}点以上",
            run_id=run_id,
        )
        return stored

    def _score(
        self, pc: ProductCandidate, intent: float, problem: str, keyword: str
    ) -> Tuple[float, Dict[str, float]]:
        b: Dict[str, float] = {}

        # Trend Fit (25) — keyword/problem terms appearing in product name
        name = pc.name
        terms = [t for t in (keyword.split() + problem.split()) if t]
        hits = sum(1 for t in terms if t and t in name)
        b["trend_fit"] = round(min(25.0, 8.0 + hits * 8.0), 2)

        # Purchase Intent (20) — from upstream 0-100 scaled
        b["purchase_intent"] = round(min(20.0, intent / 100.0 * 20.0), 2)

        # Product Relevance (20) — problem keyword in name/description
        rel_hits = sum(1 for t in terms if t and (t in name or t in pc.description))
        b["relevance"] = round(min(20.0, 6.0 + rel_hits * 5.0), 2)

        # Review / Trust (10)
        review = (pc.review_average / 5.0) * 6.0
        review += min(4.0, pc.review_count / 200.0 * 4.0)
        b["review_trust"] = round(min(10.0, review), 2)

        # Price Attractiveness (10) — sweet spot 1000-5000 yen
        price = pc.price
        if 1000 <= price <= 5000:
            price_score = 10.0
        elif price < 1000:
            price_score = 6.0
        elif price <= 10000:
            price_score = 7.0
        else:
            price_score = 3.0
        b["price"] = round(price_score, 2)

        # Affiliate Economics (10) — proxy: higher price -> higher reward, capped
        b["economics"] = round(min(10.0, 4.0 + price / 3000.0), 2)

        # Seasonality (5)
        month = dt.date.today().month
        season_terms = _SEASON_MAP.get(month, [])
        seasonal = any(s in name or s in keyword or s in problem for s in season_terms)
        b["seasonality"] = 5.0 if seasonal else 2.0

        total = round(sum(b.values()), 2)
        return min(100.0, total), b
