"""Scheduled jobs (spec section 24). Times come from config (.env)."""
from __future__ import annotations

import datetime as dt

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.agents import ChiefManager, GrowthManager
from app.config import settings
from app.database import session_scope
from app.services import publisher
from app.services.pipeline import run_daily_pipeline


def _hm(value: str) -> tuple[int, int]:
    h, m = value.split(":")
    return int(h), int(m)


def job_daily_pipeline() -> None:
    with session_scope() as db:
        run_daily_pipeline(db)


def job_publish_due() -> None:
    with session_scope() as db:
        publisher.publish_due(db)


def job_daily_analysis() -> None:
    with session_scope() as db:
        GrowthManager().analyze_day(db, dt.date.today(), run_id="scheduler")


def job_strategy_update() -> None:
    with session_scope() as db:
        tomorrow = (dt.date.today() + dt.timedelta(days=1)).isoformat()
        ChiefManager().plan_day(db, tomorrow, run_id="scheduler")


def build_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone="Asia/Tokyo")

    # 06:00-09:00 combined into one pipeline run (research→...→content) at content time
    ch, cm = _hm(settings.cron_content_generation)
    sched.add_job(job_daily_pipeline, CronTrigger(hour=ch, minute=cm), id="daily_pipeline")

    # publish approved posts every N minutes (staggering handled inside publish_due)
    sched.add_job(
        job_publish_due,
        CronTrigger(minute=f"*/{max(settings.min_post_interval_minutes, 5)}"),
        id="publish_due",
    )

    ah, am = _hm(settings.cron_daily_analysis)
    sched.add_job(job_daily_analysis, CronTrigger(hour=ah, minute=am), id="daily_analysis")

    sh, sm = _hm(settings.cron_strategy_update)
    sched.add_job(job_strategy_update, CronTrigger(hour=sh, minute=sm), id="strategy_update")

    return sched
