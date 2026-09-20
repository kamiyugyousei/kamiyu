"""AI社員02 — Chrome Market Researcher.

Threadsで「今ユーザーが何を話しているか」を探索。固定語検索で終わらせず、
active/winner キーワードや seed から幅広く調査する。robots/ToS尊重、
CAPTCHA/ログイン制限回避は禁止(browser integration が保証)。
"""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.config import settings
from app.integrations import browser
from app.models import Keyword, ResearchedPost, Trend
from app.schemas import ResearchFinding


class ChromeResearcher(BaseAgent):
    name = "chrome_researcher"

    def research(
        self, db: Session, seed_keywords: List[str], run_id: str, per_keyword: int = 5
    ) -> List[ResearchFinding]:
        # combine explicit seeds with active DB keywords (avoid dead ones)
        active = [
            k.keyword
            for k in db.query(Keyword)
            .filter(Keyword.status.in_(["exploring", "active", "winner"]))
            .order_by(Keyword.revenue_generated.desc())
            .limit(15)
            .all()
        ]
        query_keywords = list(dict.fromkeys(seed_keywords + active))[:20]

        all_findings: List[ResearchFinding] = []
        degraded = not settings.browser_enabled
        for kw in query_keywords:
            findings = browser.research(kw, limit=per_keyword)
            all_findings.extend(findings)
            self._persist(db, kw, findings)

        self.log(
            db,
            "research",
            f"{len(query_keywords)}キーワードを調査、{len(all_findings)}件の投稿を分析"
            + ("（browser無効のためモック）" if degraded else ""),
            degraded=degraded,
            run_id=run_id,
        )
        return all_findings

    def _persist(self, db: Session, keyword: str, findings: List[ResearchFinding]) -> None:
        kw = db.query(Keyword).filter(Keyword.keyword == keyword).one_or_none()
        if kw:
            kw.search_count += 1
            kw.posts_found += len(findings)
        for f in findings:
            eng = f.likes + f.replies * 3 + f.reposts * 2
            db.add(
                ResearchedPost(
                    source=f.source,
                    url=f.url,
                    summary=f.summary,
                    keyword=f.keyword,
                    likes=f.likes,
                    replies=f.replies,
                    reposts=f.reposts,
                    engagement_score=float(eng),
                    detected_problem=f.detected_problem,
                )
            )
        # register a trend row for the keyword
        if findings:
            momentum = sum(x.likes for x in findings) / max(len(findings), 1)
            db.add(
                Trend(
                    topic=keyword,
                    category=(kw.category if kw else "uncategorized"),
                    momentum=float(momentum),
                    sample_url=findings[0].url,
                )
            )
        db.flush()
