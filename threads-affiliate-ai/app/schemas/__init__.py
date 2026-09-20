"""Pydantic schemas for API I/O and internal agent data transfer."""
from __future__ import annotations

import datetime as dt
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ProductOut(BaseModel):
    id: int
    provider: str
    name: str
    price: float
    review_average: float
    review_count: int
    image_url: str
    shop_name: str
    product_url: str
    affiliate_url: str
    genre: str
    affiliate_score: float

    model_config = ConfigDict(from_attributes=True)


class CandidateOut(BaseModel):
    id: int
    post_type: str
    variant: str
    body: str
    hook_type: str
    keyword: str
    category: str
    affiliate_url: str
    ai_score: float
    compliance_score: float
    similarity_score: float
    reference_trend: str
    reference_url: str
    scheduled_time: Optional[dt.datetime]
    status: str
    product: Optional[ProductOut] = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalAction(BaseModel):
    action: str  # approve / reject / postpone / edit
    body: Optional[str] = None  # for edit
    scheduled_time: Optional[dt.datetime] = None


class DailyReport(BaseModel):
    date: str
    posts_published: int
    affiliate_posts: int
    revenue: float
    revenue_yesterday: float
    revenue_month: float
    clicks: int
    conversions: int
    best_category: str
    best_product: str
    best_hook: str
    tomorrow_strategy: str


# --- Internal (agent pipeline) ---
class ResearchFinding(BaseModel):
    source: str = "threads"
    url: str = ""
    summary: str = ""
    keyword: str = ""
    likes: int = 0
    replies: int = 0
    reposts: int = 0
    detected_problem: str = ""
    hook_type: str = ""


class ProductCandidate(BaseModel):
    provider: str = "rakuten"
    external_id: str = ""
    name: str = ""
    price: float = 0.0
    description: str = ""
    review_average: float = 0.0
    review_count: int = 0
    image_url: str = ""
    shop_name: str = ""
    product_url: str = ""
    affiliate_url: str = ""
    genre: str = ""
    postage_flag: int = 0
    keyword: str = ""


class CopyVariant(BaseModel):
    variant: str
    body: str
    hook_type: str


class ComplianceResult(BaseModel):
    score: float
    passed: bool
    issues: List[str] = []
