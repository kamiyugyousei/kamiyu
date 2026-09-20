"""ORM models — the tables listed in the spec (section 29).

keywords, trends, posts_researched, products, affiliate_links,
affiliate_programs, post_candidates, published_posts, post_performance,
conversions, winning_patterns, daily_strategy, approval_queue, agent_logs.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now() -> dt.datetime:
    return dt.datetime.utcnow()


# --------------------------------------------------------------------------- #
# Keywords
# --------------------------------------------------------------------------- #
class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    keyword: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(64), default="uncategorized")
    # problem / purchase / emotion / comparison / season / seed
    ktype: Mapped[str] = mapped_column(String(32), default="seed")
    first_seen: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    last_seen: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    search_count: Mapped[int] = mapped_column(Integer, default=0)
    posts_found: Mapped[int] = mapped_column(Integer, default=0)
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)
    purchase_intent_score: Mapped[float] = mapped_column(Float, default=0.0)
    affiliate_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    revenue_generated: Mapped[float] = mapped_column(Float, default=0.0)
    # exploring / active / winner / declining / paused
    status: Mapped[str] = mapped_column(String(16), default="exploring", index=True)


# --------------------------------------------------------------------------- #
# Trends (aggregated topics observed on Threads)
# --------------------------------------------------------------------------- #
class Trend(Base):
    __tablename__ = "trends"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(64), default="uncategorized")
    momentum: Mapped[float] = mapped_column(Float, default=0.0)  # relative growth
    sample_url: Mapped[str] = mapped_column(String(512), default="")
    observed_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


# --------------------------------------------------------------------------- #
# Researched posts (analysed for structure, NEVER copied)
# --------------------------------------------------------------------------- #
class ResearchedPost(Base):
    __tablename__ = "posts_researched"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32), default="threads")
    url: Mapped[str] = mapped_column(String(512), default="")
    summary: Mapped[str] = mapped_column(Text, default="")  # our summary, not raw copy
    keyword: Mapped[str] = mapped_column(String(255), default="")
    likes: Mapped[int] = mapped_column(Integer, default=0)
    replies: Mapped[int] = mapped_column(Integer, default=0)
    reposts: Mapped[int] = mapped_column(Integer, default=0)
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)
    purchase_intent_score: Mapped[float] = mapped_column(Float, default=0.0)
    hook_type: Mapped[str] = mapped_column(String(64), default="")
    detected_problem: Mapped[str] = mapped_column(Text, default="")
    researched_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


# --------------------------------------------------------------------------- #
# Products
# --------------------------------------------------------------------------- #
class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), default="rakuten")
    external_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    name: Mapped[str] = mapped_column(String(512), default="")
    price: Mapped[float] = mapped_column(Float, default=0.0)
    description: Mapped[str] = mapped_column(Text, default="")
    review_average: Mapped[float] = mapped_column(Float, default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    image_url: Mapped[str] = mapped_column(String(1024), default="")
    shop_name: Mapped[str] = mapped_column(String(255), default="")
    product_url: Mapped[str] = mapped_column(String(1024), default="")
    affiliate_url: Mapped[str] = mapped_column(String(1024), default="")
    genre: Mapped[str] = mapped_column(String(128), default="")
    postage_flag: Mapped[int] = mapped_column(Integer, default=0)  # 0=送料込/未定,1=別
    keyword: Mapped[str] = mapped_column(String(255), default="", index=True)
    affiliate_score: Mapped[float] = mapped_column(Float, default=0.0)
    score_breakdown: Mapped[str] = mapped_column(Text, default="{}")  # JSON
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


# --------------------------------------------------------------------------- #
# Affiliate programs & links
# --------------------------------------------------------------------------- #
class AffiliateProgram(Base):
    __tablename__ = "affiliate_programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32))  # rakuten / a8 / amazon...
    name: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(32), default="active")  # active/pending
    sns_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


class AffiliateLink(Base):
    __tablename__ = "affiliate_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), default="rakuten")
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"))
    url: Mapped[str] = mapped_column(String(1024), default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


# --------------------------------------------------------------------------- #
# Post candidates (before approval)
# --------------------------------------------------------------------------- #
class PostCandidate(Base):
    __tablename__ = "post_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    # affiliate / value / conversation / experiment
    post_type: Mapped[str] = mapped_column(String(16), default="affiliate", index=True)
    variant: Mapped[str] = mapped_column(String(8), default="A")  # A/B/C
    body: Mapped[str] = mapped_column(Text, default="")
    hook_type: Mapped[str] = mapped_column(String(64), default="")
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"))
    keyword: Mapped[str] = mapped_column(String(255), default="")
    category: Mapped[str] = mapped_column(String(64), default="")
    affiliate_url: Mapped[str] = mapped_column(String(1024), default="")
    ai_score: Mapped[float] = mapped_column(Float, default=0.0)
    compliance_score: Mapped[float] = mapped_column(Float, default=0.0)
    similarity_score: Mapped[float] = mapped_column(Float, default=0.0)
    reference_trend: Mapped[str] = mapped_column(String(512), default="")
    reference_url: Mapped[str] = mapped_column(String(512), default="")
    scheduled_time: Mapped[Optional[dt.datetime]] = mapped_column(DateTime)
    # pending / approved / rejected / edited / postponed / published
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    strategy_date: Mapped[str] = mapped_column(String(16), default="", index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    product: Mapped[Optional["Product"]] = relationship()


# --------------------------------------------------------------------------- #
# Published posts + performance + conversions
# --------------------------------------------------------------------------- #
class PublishedPost(Base):
    __tablename__ = "published_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("post_candidates.id"))
    threads_post_id: Mapped[str] = mapped_column(String(128), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    post_type: Mapped[str] = mapped_column(String(16), default="affiliate")
    category: Mapped[str] = mapped_column(String(64), default="")
    hook_type: Mapped[str] = mapped_column(String(64), default="")
    affiliate_url: Mapped[str] = mapped_column(String(1024), default="")
    published_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


class PostPerformance(Base):
    __tablename__ = "post_performance"

    id: Mapped[int] = mapped_column(primary_key=True)
    published_post_id: Mapped[int] = mapped_column(ForeignKey("published_posts.id"))
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    replies: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    followers_gained: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    recorded_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


class Conversion(Base):
    __tablename__ = "conversions"

    id: Mapped[int] = mapped_column(primary_key=True)
    published_post_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("published_posts.id")
    )
    provider: Mapped[str] = mapped_column(String(32), default="rakuten")
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"))
    reward: Mapped[float] = mapped_column(Float, default=0.0)
    occurred_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


# --------------------------------------------------------------------------- #
# Winning patterns
# --------------------------------------------------------------------------- #
class WinningPattern(Base):
    __tablename__ = "winning_patterns"

    id: Mapped[int] = mapped_column(primary_key=True)
    keyword: Mapped[str] = mapped_column(String(255), default="")
    problem: Mapped[str] = mapped_column(Text, default="")
    product_category: Mapped[str] = mapped_column(String(128), default="")
    hook_type: Mapped[str] = mapped_column(String(64), default="")
    price_range: Mapped[str] = mapped_column(String(64), default="")
    posting_time: Mapped[str] = mapped_column(String(16), default="")
    ctr: Mapped[float] = mapped_column(Float, default=0.0)
    cvr: Mapped[float] = mapped_column(Float, default=0.0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


# --------------------------------------------------------------------------- #
# Daily strategy (Chief Manager output)
# --------------------------------------------------------------------------- #
class DailyStrategy(Base):
    __tablename__ = "daily_strategy"

    id: Mapped[int] = mapped_column(primary_key=True)
    strategy_date: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    affiliate_posts: Mapped[int] = mapped_column(Integer, default=4)
    value_posts: Mapped[int] = mapped_column(Integer, default=3)
    conversation_posts: Mapped[int] = mapped_column(Integer, default=2)
    experiment_posts: Mapped[int] = mapped_column(Integer, default=1)
    focus_categories: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    category_budget: Mapped[str] = mapped_column(Text, default="{}")  # JSON dict
    posting_times: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of HH:MM
    rationale: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


# --------------------------------------------------------------------------- #
# Approval queue (human-in-the-loop / blocked automation)
# --------------------------------------------------------------------------- #
class ApprovalQueueItem(Base):
    __tablename__ = "approval_queue"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), default="post")  # post / a8_action ...
    ref_id: Mapped[Optional[int]] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[str] = mapped_column(Text, default="{}")  # JSON
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


# --------------------------------------------------------------------------- #
# Agent audit log
# --------------------------------------------------------------------------- #
class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(128), default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    level: Mapped[str] = mapped_column(String(16), default="info")  # info/warn/error
    degraded: Mapped[bool] = mapped_column(Boolean, default=False)
    run_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


__all__ = [
    "Keyword",
    "Trend",
    "ResearchedPost",
    "Product",
    "AffiliateProgram",
    "AffiliateLink",
    "PostCandidate",
    "PublishedPost",
    "PostPerformance",
    "Conversion",
    "WinningPattern",
    "DailyStrategy",
    "ApprovalQueueItem",
    "AgentLog",
]
