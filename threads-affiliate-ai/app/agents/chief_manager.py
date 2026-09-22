"""AI社員01 — Chief AI Manager.

前日成果を見て本日の投稿計画(DailyStrategy)を決定。探索枠は常に20%以上維持し、
1カテゴリへの100%集中を禁止する。
"""
from __future__ import annotations

import datetime as dt
import json
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.config import settings
from app.models import DailyStrategy, Keyword, PostPerformance, PublishedPost


class ChiefManager(BaseAgent):
    name = "chief_manager"

    def plan_day(self, db: Session, strategy_date: str, run_id: str) -> DailyStrategy:
        existing = (
            db.query(DailyStrategy)
            .filter(DailyStrategy.strategy_date == strategy_date)
            .one_or_none()
        )
        if existing:
            self.log(db, "plan_day", f"既存戦略を再利用: {strategy_date}", run_id=run_id)
            return existing

        composition = self._composition(db)
        focus, budget = self._category_budget(db)
        times = self._posting_times(composition_total=sum(composition.values()))

        strategy = DailyStrategy(
            strategy_date=strategy_date,
            affiliate_posts=composition["affiliate"],
            value_posts=composition["value"],
            conversation_posts=composition["conversation"],
            experiment_posts=composition["experiment"],
            focus_categories=json.dumps(focus, ensure_ascii=False),
            category_budget=json.dumps(budget, ensure_ascii=False),
            posting_times=json.dumps(times, ensure_ascii=False),
            rationale=self._rationale(composition, focus),
        )
        db.add(strategy)
        db.flush()
        self.log(
            db,
            "plan_day",
            f"本日戦略: {composition} focus={focus}",
            run_id=run_id,
        )
        return strategy

    # --- composition based on yesterday's revenue-per-post ---
    def _composition(self, db: Session) -> Dict[str, int]:
        target = settings.target_posts_per_day
        comp = {
            "affiliate": settings.affiliate_posts_per_day,
            "value": settings.value_posts_per_day,
            "conversation": settings.conversation_posts_per_day,
            "experiment": settings.experiment_posts_per_day,
        }
        # Adjust affiliate share by yesterday's affiliate revenue-per-post signal.
        y_rev = self._yesterday_affiliate_rpp(db)
        if y_rev is not None:
            if y_rev >= 1000 and comp["affiliate"] < settings.max_affiliate_posts_per_day:
                comp["affiliate"] += 1
                comp["value"] = max(1, comp["value"] - 1)
            elif y_rev < 200 and comp["affiliate"] > 2:
                comp["affiliate"] -= 1
                comp["value"] += 1
        comp["affiliate"] = min(comp["affiliate"], settings.max_affiliate_posts_per_day)

        # normalise to target total, keeping at least 1 experiment (exploration)
        comp["experiment"] = max(1, comp["experiment"])
        total = sum(comp.values())
        if total != target:
            comp["value"] += target - total
            comp["value"] = max(0, comp["value"])
        return comp

    def _yesterday_affiliate_rpp(self, db: Session) -> float | None:
        y = (dt.date.today() - dt.timedelta(days=1))
        start = dt.datetime.combine(y, dt.time.min)
        end = dt.datetime.combine(y, dt.time.max)
        rows = (
            db.query(func.sum(PostPerformance.revenue), func.count(PostPerformance.id))
            .join(PublishedPost, PublishedPost.id == PostPerformance.published_post_id)
            .filter(PublishedPost.post_type == "affiliate")
            .filter(PublishedPost.published_at >= start)
            .filter(PublishedPost.published_at <= end)
            .one()
        )
        total_rev, count = rows[0] or 0.0, rows[1] or 0
        if count == 0:
            return None
        return total_rev / count

    # --- category budget with >=20% exploration reserve ---
    def _category_budget(self, db: Session) -> tuple[List[str], Dict[str, float]]:
        # winners by revenue
        winners = (
            db.query(Keyword.category, func.sum(Keyword.revenue_generated))
            .group_by(Keyword.category)
            .order_by(func.sum(Keyword.revenue_generated).desc())
            .limit(4)
            .all()
        )
        focus = [c for c, rev in winners if rev and rev > 0]
        if not focus:
            focus = ["旅行", "収納", "美容"]  # default starting focus

        reserve = max(settings.min_exploration_ratio, 0.20)
        exploit = 1.0 - reserve
        budget: Dict[str, float] = {}
        if focus:
            per = exploit / len(focus)
            for c in focus:
                budget[c] = round(per, 3)
        budget["_exploration"] = round(reserve, 3)
        return focus, budget

    def _posting_times(self, composition_total: int) -> List[str]:
        # spread across the day within the posting window (first_post_hour..last_post_hour)
        first = settings.first_post_hour
        last = max(first + 1, settings.last_post_hour)
        start = dt.datetime.combine(dt.date.today(), dt.time(hour=first))
        end = dt.datetime.combine(dt.date.today(), dt.time(hour=last))

        if composition_total <= 1:
            return [start.strftime("%H:%M")]

        # even spacing across the window, but never tighter than MIN_POST_INTERVAL
        window_min = (end - start).total_seconds() / 60
        spacing = max(
            settings.min_post_interval_minutes,
            window_min / (composition_total - 1) if composition_total > 1 else window_min,
        )
        times: List[str] = []
        cur = start
        for _ in range(composition_total):
            times.append(cur.strftime("%H:%M"))
            cur += dt.timedelta(minutes=spacing)
            if cur > end:
                cur = end
        return times

    def _rationale(self, comp: Dict[str, int], focus: List[str]) -> str:
        return (
            f"投稿構成 affiliate={comp['affiliate']} value={comp['value']} "
            f"conversation={comp['conversation']} experiment={comp['experiment']}。"
            f"注力カテゴリ={focus}。探索枠は{int(settings.min_exploration_ratio*100)}%以上維持。"
        )
