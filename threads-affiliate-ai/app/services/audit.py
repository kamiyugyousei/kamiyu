"""Audit logging — records everything each AI employee does (spec section 45)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AgentLog


def log(
    db: Session,
    agent: str,
    action: str,
    detail: str = "",
    level: str = "info",
    degraded: bool = False,
    run_id: str = "",
) -> AgentLog:
    entry = AgentLog(
        agent=agent,
        action=action,
        detail=detail,
        level=level,
        degraded=degraded,
        run_id=run_id,
    )
    db.add(entry)
    db.flush()
    return entry
