"""Run the daily pipeline once and print the result (spec section 46).

    python -m app.run_once "旅行便利グッズ"
"""
from __future__ import annotations

import json
import sys

from app.database import init_db, session_scope
from app.services.pipeline import run_daily_pipeline


def main() -> None:
    init_db()
    seeds = sys.argv[1:] or ["旅行便利グッズ"]
    with session_scope() as db:
        summary = run_daily_pipeline(db, seed_keywords=seeds)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(
        "\n→ ダッシュボードで承認してください: "
        "python -m app.main → http://localhost:8000"
    )


if __name__ == "__main__":
    main()
