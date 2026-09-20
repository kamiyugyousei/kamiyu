"""AI社員03 — Keyword Discovery.

調査投稿から新しい検索語を抽出・分類し、キーワードを自動拡張(30→50→100→200)。
成果ゼロのキーワードは永久検索せず status で優先度を下げる。
"""
from __future__ import annotations

import re
from typing import Dict, List

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models import Keyword, ResearchedPost
from app.schemas import ResearchFinding

# classification lexicons (spec section 6)
LEXICON: Dict[str, List[str]] = {
    "problem": [
        "面倒", "時間がない", "収納できない", "荷物が多い", "乾かない", "眠れない",
        "片付かない", "暑い", "寒い", "疲れる", "重い", "かさばる", "充電",
    ],
    "purchase": [
        "買ってよかった", "おすすめ", "便利", "欲しい", "楽天", "セール",
        "クーポン", "安い", "コスパ", "リピート",
    ],
    "emotion": [
        "知らなかった", "もっと早く知りたかった", "天才", "地味に便利",
        "本当に助かる", "こればかり",
    ],
    "comparison": [
        "Amazon", "楽天", "無印", "ニトリ", "ダイソー", "比較", "どっち", "おすすめ",
    ],
    "season": [
        "夏", "冬", "梅雨", "旅行", "夏休み", "新生活", "クリスマス", "年末",
        "母の日", "父の日",
    ],
}

_WORD_RE = re.compile(r"[぀-ヿ一-鿿A-Za-z]{2,}")


class KeywordDiscovery(BaseAgent):
    name = "keyword_discovery"

    def discover(
        self, db: Session, findings: List[ResearchFinding], run_id: str
    ) -> List[str]:
        discovered: List[str] = []
        for f in findings:
            text = f"{f.summary} {f.detected_problem}"
            for token in self._candidate_terms(text, f.keyword):
                ktype, category = self._classify(token, f.keyword)
                if self._upsert(db, token, ktype, category):
                    discovered.append(token)

        self._demote_dead_keywords(db)
        self.log(
            db,
            "discover",
            f"新規キーワード{len(set(discovered))}語を発見・分類",
            run_id=run_id,
        )
        return list(dict.fromkeys(discovered))

    def _candidate_terms(self, text: str, base_kw: str) -> List[str]:
        terms = set()
        # derived problem+category compound terms (悩みベースの新検索語)
        for group in LEXICON.values():
            for hint in group:
                if hint in text:
                    terms.add(hint)
                    terms.add(f"{base_kw} {hint}")
        # also add notable standalone words
        for m in _WORD_RE.findall(text):
            if len(m) >= 3 and m not in base_kw:
                terms.add(m)
        return [t.strip() for t in terms if 2 <= len(t) <= 40]

    def _classify(self, term: str, base_kw: str) -> tuple[str, str]:
        for ktype, group in LEXICON.items():
            if any(h in term for h in group):
                return ktype, self._category_of(base_kw)
        return "purchase", self._category_of(base_kw)

    def _category_of(self, base_kw: str) -> str:
        return base_kw.split()[0] if base_kw else "uncategorized"

    def _upsert(self, db: Session, term: str, ktype: str, category: str) -> bool:
        existing = db.query(Keyword).filter(Keyword.keyword == term).one_or_none()
        from app.agents.base import today_str  # local import to avoid cycle

        import datetime as dt

        if existing:
            existing.last_seen = dt.datetime.utcnow()
            existing.posts_found += 1
            return False
        db.add(
            Keyword(
                keyword=term,
                category=category,
                ktype=ktype,
                status="exploring",
                posts_found=1,
            )
        )
        db.flush()
        return True

    def _demote_dead_keywords(self, db: Session) -> None:
        """探索済みだが成果ゼロのキーワードを declining に。"""
        stale = (
            db.query(Keyword)
            .filter(Keyword.status == "exploring")
            .filter(Keyword.search_count >= 5)
            .filter(Keyword.revenue_generated <= 0)
            .filter(Keyword.affiliate_match_score <= 0)
            .all()
        )
        for k in stale:
            k.status = "declining"
