"""Shared agent scaffolding."""
from __future__ import annotations

import dataclasses
import datetime as dt
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.services import audit


@dataclasses.dataclass
class PipelineContext:
    """Carried through the daily pipeline; agents read/write shared state here."""

    db: Session
    run_id: str
    strategy_date: str
    strategy: Any = None  # DailyStrategy ORM row
    findings: List[Any] = dataclasses.field(default_factory=list)
    keywords: List[str] = dataclasses.field(default_factory=list)
    intents: Dict[str, float] = dataclasses.field(default_factory=dict)
    products: List[Any] = dataclasses.field(default_factory=list)
    candidates: List[Any] = dataclasses.field(default_factory=list)
    notes: List[str] = dataclasses.field(default_factory=list)


class BaseAgent:
    name: str = "agent"

    def log(
        self,
        db: Session,
        action: str,
        detail: str = "",
        level: str = "info",
        degraded: bool = False,
        run_id: str = "",
    ) -> None:
        audit.log(
            db,
            agent=self.name,
            action=action,
            detail=detail,
            level=level,
            degraded=degraded,
            run_id=run_id,
        )


def today_str() -> str:
    return dt.date.today().isoformat()
