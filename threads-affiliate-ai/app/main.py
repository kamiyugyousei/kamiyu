"""Entrypoint: launch the dashboard + background scheduler.

    python -m app.main
"""
from __future__ import annotations

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


@app.on_event("shutdown")
def _stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def main() -> None:
    init_db()
    uvicorn.run(
        "app.main:app",
        host=settings.dashboard_host,
        port=settings.dashboard_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
