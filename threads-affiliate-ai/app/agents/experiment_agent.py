"""AI社員12 — Experiment Agent.

毎日1件、新Hook/新カテゴリ/新価格帯/新構造をテストし A/B データとして保存。
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.copywriter import Copywriter
from app.agents.viral_analyst import HOOK_PATTERNS
from app.schemas import CopyVariant


class ExperimentAgent(BaseAgent):
    name = "experiment_agent"

    def __init__(self) -> None:
        self.copywriter = Copywriter()

    def make(self, db: Session, topic: str, run_id: str) -> CopyVariant:
        # rotate hook by day-of-year so experiments cover the space over time
        idx = dt.date.today().timetuple().tm_yday % len(HOOK_PATTERNS)
        hook_type = HOOK_PATTERNS[idx][0]
        variant = self.copywriter.write_experiment_post(db, topic, hook_type, run_id)
        self.log(db, "make", f"実験投稿: {topic} hook={hook_type}", run_id=run_id)
        return variant
