"""AI社員10 — Compliance Officer.

投稿前に全チェック(spec section 20)。MIN_COMPLIANCE_SCORE=90 未満は不投稿。
チェック: PR表記/アフィリ表示/虚偽/価格/商品情報/体験捏造/コピー/誇大/URL/NG商品 等。
"""
from __future__ import annotations

from typing import List

from app.config import settings
from app.schemas import ComplianceResult

# 誇大表現・NGワード(簡易)
EXAGGERATION = ["絶対に", "必ず痩せる", "100%", "誰でも稼げる", "完治", "副作用なし"]
FAKE_EXPERIENCE = ["使ってみた結果", "私も愛用", "毎日使っています", "半年使った"]
NG_CATEGORIES = ["たばこ", "アダルト", "出会い系", "現金化", "情報商材"]


class ComplianceOfficer:
    name = "compliance"

    def check(
        self, body: str, is_affiliate: bool, affiliate_url: str = "", price: float = 0.0
    ) -> ComplianceResult:
        issues: List[str] = []
        score = 100.0

        if is_affiliate:
            if not any(tag in body for tag in ["#PR", "PR表記", "広告", "アフィリエイト"]):
                issues.append("PR/広告表記がありません")
                score -= 40
            if affiliate_url and affiliate_url not in body:
                issues.append("アフィリエイトURLが本文に含まれていません")
                score -= 20
            if price and str(int(price)) not in body and "円" not in body:
                issues.append("価格情報が不足")
                score -= 5

        for w in EXAGGERATION:
            if w in body:
                issues.append(f"誇大表現の疑い: {w}")
                score -= 15
        for w in FAKE_EXPERIENCE:
            if w in body:
                issues.append(f"体験談捏造の疑い: {w}")
                score -= 25
        for w in NG_CATEGORIES:
            if w in body:
                issues.append(f"NGカテゴリの疑い: {w}")
                score -= 50

        if len(body) < 20:
            issues.append("本文が短すぎます")
            score -= 10
        if len(body) > 500:
            issues.append("本文が長すぎます(Threads推奨500字以内)")
            score -= 5

        score = max(0.0, min(100.0, score))
        return ComplianceResult(
            score=score,
            passed=score >= settings.min_compliance_score,
            issues=issues,
        )
