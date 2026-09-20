"""A8.net integration (PHASE 2 scaffold).

A8.net has no general public product API. Real operation therefore uses a
browser/MCP flow against the member console. That flow must STOP and route to
the Human Approval Queue whenever it hits any of:
  CAPTCHA, 2FA, terms consent, partnership application, financial contract,
  unknown SNS posting conditions, or unknown program conditions.
We never bypass these.

In PHASE 1 this module only exposes helpers that raise HumanApprovalRequired,
so nothing runs automatically yet.
"""
from __future__ import annotations

from typing import List

from app.schemas import ProductCandidate


class HumanApprovalRequired(Exception):
    """Raised when an A8 action needs a human decision (never auto-bypassed)."""

    def __init__(self, reason: str, payload: dict | None = None):
        super().__init__(reason)
        self.reason = reason
        self.payload = payload or {}


BLOCKING_CONDITIONS = {
    "captcha",
    "2fa",
    "terms_consent",
    "partnership_application",
    "financial_contract",
    "unknown_sns_conditions",
    "unknown_program_conditions",
}


def search_products(keyword: str, hits: int = 5) -> List[ProductCandidate]:
    """PHASE 2. Currently blocked pending partnership/console access."""
    raise HumanApprovalRequired(
        reason="A8.net requires member-console access; partnership & SNS posting "
        "conditions must be confirmed by a human before use.",
        payload={"keyword": keyword, "condition": "unknown_program_conditions"},
    )
