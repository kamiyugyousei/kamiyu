"""AI社員13 — Growth Manager.

日次で成果を分析(カテゴリ/Hook/価格帯/商品/ASP/投稿時間別)し、
Winning Pattern の保存、翌日戦略への反映、Reverse Research の種出しを行う。
KPIは投稿数でなく「1投稿あたり利益」。1カテゴリ100%集中禁止・探索枠20%維持。
"""
from __future__ import annotations

import datetime as dt
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models import (
    Conversion,
    Keyword,
    PostPerformance,
    Product,
    PublishedPost,
    WinningPattern,
)
from app.schemas import DailyReport


class GrowthManager(BaseAgent):
    name = "growth_manager"

    def analyze_day(self, db: Session, day: dt.date, run_id: str) -> DailyReport:
        start = dt.datetime.combine(day, dt.time.min)
        end = dt.datetime.combine(day, dt.time.max)

        posts = (
            db.query(PublishedPost)
            .filter(PublishedPost.published_at >= start)
            .filter(PublishedPost.published_at <= end)
            .all()
        )
        perf_by_post = self._perf_map(db, [p.id for p in posts])

        total_rev = sum(perf_by_post.get(p.id, _z()).revenue for p in posts)
        total_clicks = sum(perf_by_post.get(p.id, _z()).clicks for p in posts)
        total_conv = sum(perf_by_post.get(p.id, _z()).conversions for p in posts)
        affiliate_posts = [p for p in posts if p.post_type == "affiliate"]

        by_cat = self._aggregate(posts, perf_by_post, key="category")
        by_hook = self._aggregate(posts, perf_by_post, key="hook_type")

        best_cat = self._best(by_cat)
        best_hook = self._best(by_hook)
        best_product = self._best_product(db, start, end)

        # persist winning pattern for the best category/hook if it earned money
        if best_cat and by_cat[best_cat]["revenue"] > 0:
            self._save_winning_pattern(db, best_cat, best_hook, by_cat[best_cat])

        # feed revenue back to keyword scores (Reverse Research seed)
        self._update_keyword_revenue(db, start, end)

        report = DailyReport(
            date=day.isoformat(),
            posts_published=len(posts),
            affiliate_posts=len(affiliate_posts),
            revenue=round(total_rev, 2),
            revenue_yesterday=self._revenue_on(db, day - dt.timedelta(days=1)),
            revenue_month=self._revenue_month(db, day),
            clicks=total_clicks,
            conversions=total_conv,
            best_category=best_cat or "-",
            best_product=best_product or "-",
            best_hook=best_hook or "-",
            tomorrow_strategy=self._tomorrow(best_cat, by_cat),
        )
        self.log(
            db,
            "analyze_day",
            f"{day}: 投稿{len(posts)} 売上{total_rev:.0f}円 CV{total_conv} "
            f"best_cat={best_cat} best_hook={best_hook}",
            run_id=run_id,
        )
        return report

    # --- helpers ---
    def _perf_map(self, db: Session, post_ids: List[int]) -> Dict[int, PostPerformance]:
        if not post_ids:
            return {}
        rows = (
            db.query(PostPerformance)
            .filter(PostPerformance.published_post_id.in_(post_ids))
            .all()
        )
        out: Dict[int, PostPerformance] = {}
        for r in rows:
            # keep latest per post
            cur = out.get(r.published_post_id)
            if not cur or r.recorded_at > cur.recorded_at:
                out[r.published_post_id] = r
        return out

    def _aggregate(self, posts, perf_map, key: str) -> Dict[str, Dict[str, float]]:
        agg: Dict[str, Dict[str, float]] = {}
        for p in posts:
            k = getattr(p, key) or "-"
            perf = perf_map.get(p.id, _z())
            a = agg.setdefault(k, {"posts": 0, "revenue": 0.0, "clicks": 0, "impressions": 0, "conversions": 0})
            a["posts"] += 1
            a["revenue"] += perf.revenue
            a["clicks"] += perf.clicks
            a["impressions"] += perf.impressions
            a["conversions"] += perf.conversions
        for k, a in agg.items():
            a["revenue_per_post"] = a["revenue"] / a["posts"] if a["posts"] else 0.0
            a["ctr"] = (a["clicks"] / a["impressions"]) if a["impressions"] else 0.0
            a["cvr"] = (a["conversions"] / a["clicks"]) if a["clicks"] else 0.0
        return agg

    def _best(self, agg: Dict[str, Dict[str, float]]) -> str:
        if not agg:
            return ""
        return max(agg.items(), key=lambda kv: kv[1]["revenue"])[0]

    def _best_product(self, db: Session, start, end) -> str:
        row = (
            db.query(Product.name, func.sum(Conversion.reward))
            .join(Conversion, Conversion.product_id == Product.id)
            .filter(Conversion.occurred_at >= start)
            .filter(Conversion.occurred_at <= end)
            .group_by(Product.name)
            .order_by(func.sum(Conversion.reward).desc())
            .first()
        )
        return row[0] if row else ""

    def _save_winning_pattern(self, db, category, hook, stats) -> None:
        db.add(
            WinningPattern(
                keyword=category,
                product_category=category,
                hook_type=hook or "",
                ctr=stats.get("ctr", 0.0),
                cvr=stats.get("cvr", 0.0),
                revenue=stats.get("revenue", 0.0),
            )
        )

    def _update_keyword_revenue(self, db, start, end) -> None:
        rows = (
            db.query(PublishedPost.category, func.sum(PostPerformance.revenue))
            .join(PostPerformance, PostPerformance.published_post_id == PublishedPost.id)
            .filter(PublishedPost.published_at >= start)
            .filter(PublishedPost.published_at <= end)
            .group_by(PublishedPost.category)
            .all()
        )
        for category, rev in rows:
            if not rev:
                continue
            for kw in db.query(Keyword).filter(Keyword.category == category).all():
                kw.revenue_generated += float(rev) / 10.0
                if kw.revenue_generated > 0 and kw.status in ("exploring", "declining"):
                    kw.status = "active"
                if kw.revenue_generated > 3000:
                    kw.status = "winner"

    def _revenue_on(self, db, day: dt.date) -> float:
        start = dt.datetime.combine(day, dt.time.min)
        end = dt.datetime.combine(day, dt.time.max)
        val = (
            db.query(func.sum(PostPerformance.revenue))
            .filter(PostPerformance.recorded_at >= start)
            .filter(PostPerformance.recorded_at <= end)
            .scalar()
        )
        return round(val or 0.0, 2)

    def _revenue_month(self, db, day: dt.date) -> float:
        start = dt.datetime.combine(day.replace(day=1), dt.time.min)
        val = (
            db.query(func.sum(PostPerformance.revenue))
            .filter(PostPerformance.recorded_at >= start)
            .scalar()
        )
        return round(val or 0.0, 2)

    def _tomorrow(self, best_cat: str, by_cat) -> str:
        if not best_cat:
            return "データ不足のため探索を継続(全カテゴリ均等 + 実験1件)。"
        return (
            f"「{best_cat}」のResearch予算を増やす(ただし探索枠20%は維持し、"
            "1カテゴリ集中は避ける)。"
        )


class _z:
    revenue = 0.0
    clicks = 0
    impressions = 0
    conversions = 0
    recorded_at = dt.datetime.min
