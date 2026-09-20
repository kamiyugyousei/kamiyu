"""Browser-based Threads market research (Playwright).

Design constraints (hard rules):
  - Respect robots.txt and Threads' Terms of Service.
  - NEVER bypass CAPTCHA, login walls, or access restrictions.
  - Prefer official APIs where they fit; the browser is only for
    human-like public market exploration.

If BROWSER_ENABLED is false or Playwright/Chromium is unavailable, we return
deterministic mock findings so the pipeline still runs. Real scraping logic is
kept intentionally conservative and public-only.
"""
from __future__ import annotations

import hashlib
from typing import List

from app.config import settings
from app.schemas import ResearchFinding

# Problem/purchase signal lexicon used to synthesise realistic mock findings and
# to score real snippets when browsing is enabled.
_PROBLEM_HINTS = [
    "充電が足りない", "収納できない", "荷物が多い", "乾かない", "眠れない",
    "片付かない", "かさばる", "重い", "時間がない", "面倒", "疲れる",
]
_PURCHASE_HINTS = [
    "買ってよかった", "おすすめ", "便利", "欲しい", "リピート", "コスパ",
]


def research(keyword: str, limit: int = 5) -> List[ResearchFinding]:
    """Return public research findings for a keyword."""
    if settings.browser_enabled:
        try:
            return _research_playwright(keyword, limit)
        except Exception:
            # any failure (no chromium, blocked, timeout) -> mock, stay safe
            return _mock_research(keyword, limit)
    return _mock_research(keyword, limit)


def _research_playwright(keyword: str, limit: int) -> List[ResearchFinding]:  # pragma: no cover
    """Conservative public exploration. Aborts on any login/CAPTCHA wall."""
    from playwright.sync_api import sync_playwright

    findings: List[ResearchFinding] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=settings.browser_headless)
        page = browser.new_page()
        url = f"https://www.threads.net/search?q={keyword}&serp_type=default"
        page.goto(url, timeout=30000)
        content = page.content().lower()
        # Respect access restrictions: if we hit a login/CAPTCHA wall, stop.
        if any(w in content for w in ("log in", "ログイン", "captcha", "認証")):
            browser.close()
            raise RuntimeError("login/CAPTCHA wall — aborting per safety policy")
        # (Public snippet extraction would go here; kept minimal on purpose.)
        browser.close()
    if not findings:
        raise RuntimeError("no public findings extracted")
    return findings[:limit]


def _mock_research(keyword: str, limit: int) -> List[ResearchFinding]:
    out: List[ResearchFinding] = []
    for i in range(limit):
        seed = int(hashlib.md5(f"{keyword}-r{i}".encode()).hexdigest(), 16)
        problem = _PROBLEM_HINTS[seed % len(_PROBLEM_HINTS)]
        purchase = _PURCHASE_HINTS[seed % len(_PURCHASE_HINTS)]
        likes = 50 + seed % 5000
        replies = seed % 400
        reposts = seed % 300
        out.append(
            ResearchFinding(
                source="threads-mock",
                url=f"https://www.threads.net/@mockuser/post/{seed % 999999}",
                summary=(
                    f"「{keyword}」に関する投稿。ユーザーは『{problem}』という悩みに触れ、"
                    f"『{purchase}』と反応。（構造分析用の要約・原文コピーではない）"
                ),
                keyword=keyword,
                likes=likes,
                replies=replies,
                reposts=reposts,
                detected_problem=problem,
                hook_type="",  # filled by viral analyst
            )
        )
    return out
