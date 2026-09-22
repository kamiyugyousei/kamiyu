"""Entrypoint: launch the dashboard + background scheduler.

    python -m app.main
"""
from __future__ import annotations

import os

import uvicorn

from app.config import settings
from app.database import init_db
from app.dashboard.app import app
from app.scheduler.jobs import build_scheduler

_scheduler = None


@app.on_event("startup")
def _start_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        _scheduler = build_scheduler()
        _scheduler.start()
    if settings.generate_on_startup:
        _maybe_generate_today()


def _maybe_generate_today() -> None:
    """If there are no candidates for today yet, generate them in the background
    so a double-click launch leaves you with posts ready to approve."""
    import datetime as dt
    import threading

    def _run() -> None:
        from app.database import session_scope
        from app.models import PostCandidate
        from app.services.pipeline import run_daily_pipeline

        today = dt.date.today().isoformat()
        try:
            with session_scope() as db:
                exists = (
                    db.query(PostCandidate)
                    .filter(PostCandidate.strategy_date == today)
                    .first()
                )
                if exists:
                    return
                run_daily_pipeline(db)
        except Exception:
            # never crash startup because of generation
            pass

    threading.Thread(target=_run, daemon=True).start()


@app.on_event("shutdown")
def _stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def main() -> None:
    init_db()
    # Hosting platforms (Render, Railway, Fly, Heroku...) inject the port via $PORT.
    port = int(os.environ.get("PORT", settings.dashboard_port))
    uvicorn.run(
        "app.main:app",
        host=settings.dashboard_host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
