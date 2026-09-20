"""Daily content-generation pipeline (PHASE 1).

Chrome Research → Keyword Discovery → Viral Analysis → Purchase Intent →
Product Hunt (Rakuten) → Affiliate Scoring → Copywriting (3 variants) →
Compliance → Approval Queue (candidates saved as `pending`).

Nothing is published here; AUTO_PUBLISH defaults to false, so a human approves
candidates via the dashboard first.
"""
from __future__ import annotations

import datetime as dt
import json
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.agents import (
    AffiliateMatcher,
    ChiefManager,
    ChromeResearcher,
    ComplianceOfficer,
    ConversationAgent,
    Copywriter,
    ExperimentAgent,
    KeywordDiscovery,
    ProductHunter,
    PurchaseIntent,
    ViralAnalyst,
)
from app.agents.base import PipelineContext
from app.config import settings
from app.models import PostCandidate, Product
from app.services import audit
from app.services.similarity import max_similarity


def _existing_bodies(db: Session, limit: int = 500) -> List[str]:
    rows = (
        db.query(PostCandidate.body)
        .order_by(PostCandidate.created_at.desc())
        .limit(limit)
        .all()
    )
    return [r[0] for r in rows]


def run_daily_pipeline(
    db: Session,
    seed_keywords: Optional[List[str]] = None,
    strategy_date: Optional[str] = None,
) -> dict:
    run_id = uuid.uuid4().hex[:12]
    strategy_date = strategy_date or dt.date.today().isoformat()
    seeds = seed_keywords or settings.seed_keywords[:6]

    ctx = PipelineContext(db=db, run_id=run_id, strategy_date=strategy_date)
    audit.log(db, "pipeline", "start", f"seeds={seeds}", run_id=run_id)

    # 01 Chief Manager: today's plan
    chief = ChiefManager()
    strategy = chief.plan_day(db, strategy_date, run_id)
    ctx.strategy = strategy

    # 02 Chrome Research
    researcher = ChromeResearcher()
    findings = researcher.research(db, seeds, run_id, per_keyword=5)

    # 03 Keyword Discovery
    KeywordDiscovery().discover(db, findings, run_id)

    # 04 Viral Analysis (hook tagging, structure only)
    findings = ViralAnalyst().analyze(db, findings, run_id)

    # 05 Purchase Intent — top problems
    intent = PurchaseIntent()
    problems = intent.rank_problems(db, findings, run_id, top_n=5)

    # 06/07 Product Hunt (Rakuten)
    hunter = ProductHunter()
    product_candidates = hunter.hunt(db, problems, run_id, hits_per_problem=10)

    # 08 Affiliate scoring
    matcher = AffiliateMatcher()
    scored_products = matcher.score_and_store(db, product_candidates, run_id)

    # pick top affiliate products above threshold, dedupe by name
    passing = sorted(
        [p for p in scored_products if p.affiliate_score >= settings.min_affiliate_score],
        key=lambda p: p.affiliate_score,
        reverse=True,
    )
    top_products = _dedupe_products(passing)[: strategy.affiliate_posts]

    copywriter = Copywriter()
    compliance = ComplianceOfficer()
    existing = _existing_bodies(db)

    created: List[PostCandidate] = []

    # --- Affiliate candidates: 3 variants each, pick best compliant/original ---
    problem_by_kw = {kw: (prob, f.hook_type) for prob, s, f in problems for kw in [f.keyword]}
    for product in top_products:
        prob, hook = problem_by_kw.get(product.keyword, ("", ""))
        variants = copywriter.write_affiliate_variants(db, product, prob, hook, run_id)
        chosen = _choose_variant(variants, compliance, product, existing)
        if not chosen:
            continue
        variant, comp_result, sim = chosen
        cand = PostCandidate(
            post_type="affiliate",
            variant=variant.variant,
            body=variant.body,
            hook_type=variant.hook_type,
            product_id=product.id,
            keyword=product.keyword,
            category=product.keyword.split()[0] if product.keyword else "",
            affiliate_url=product.affiliate_url,
            ai_score=product.affiliate_score,
            compliance_score=comp_result.score,
            similarity_score=sim,
            reference_trend=prob,
            reference_url="",
            status="pending",
            strategy_date=strategy_date,
        )
        db.add(cand)
        db.flush()
        existing.append(variant.body)
        created.append(cand)

    # --- Value posts ---
    value_topics = _value_topics(problems, seeds)
    for i in range(strategy.value_posts):
        topic = value_topics[i % len(value_topics)]
        v = copywriter.write_value_post(db, topic, run_id)
        created.append(_simple_candidate(db, "value", v, topic, strategy_date, compliance))

    # --- Conversation posts ---
    conv = ConversationAgent()
    for i in range(strategy.conversation_posts):
        topic = value_topics[i % len(value_topics)]
        v = conv.make(db, topic, run_id)
        created.append(_simple_candidate(db, "conversation", v, topic, strategy_date, compliance))

    # --- Experiment posts ---
    exp = ExperimentAgent()
    for i in range(strategy.experiment_posts):
        topic = value_topics[i % len(value_topics)]
        v = exp.make(db, topic, run_id)
        created.append(_simple_candidate(db, "experiment", v, topic, strategy_date, compliance))

    # assign staggered scheduled times from strategy
    _assign_times(created, strategy)

    db.commit()
    summary = {
        "run_id": run_id,
        "strategy_date": strategy_date,
        "candidates": len(created),
        "affiliate": sum(1 for c in created if c.post_type == "affiliate"),
        "value": sum(1 for c in created if c.post_type == "value"),
        "conversation": sum(1 for c in created if c.post_type == "conversation"),
        "experiment": sum(1 for c in created if c.post_type == "experiment"),
        "products_scored": len(scored_products),
        "problems": [p for p, _, _ in problems],
    }
    audit.log(db, "pipeline", "done", json.dumps(summary, ensure_ascii=False), run_id=run_id)
    db.commit()
    return summary


def _dedupe_products(products: List[Product]) -> List[Product]:
    seen, out = set(), []
    for p in products:
        key = p.name[:24]
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def _choose_variant(variants, compliance, product, existing):
    """Return (variant, compliance_result, similarity) for the best variant that
    passes compliance and originality; None if all fail."""
    best = None
    for v in variants:
        sim = max_similarity(v.body, existing)
        comp = compliance.check(
            v.body, is_affiliate=True, affiliate_url=product.affiliate_url, price=product.price
        )
        ok = comp.passed and sim <= settings.copy_similarity_threshold
        rank = (ok, comp.score, -sim)
        if best is None or rank > best[0]:
            best = (rank, v, comp, sim)
    if best is None:
        return None
    _, v, comp, sim = best
    if not comp.passed or sim > settings.copy_similarity_threshold:
        # still surface the best one for human review, marked by low scores
        return (v, comp, sim)
    return (v, comp, sim)


def _simple_candidate(db, post_type, variant, topic, strategy_date, compliance):
    comp = compliance.check(variant.body, is_affiliate=False)
    cand = PostCandidate(
        post_type=post_type,
        variant=variant.variant,
        body=variant.body,
        hook_type=variant.hook_type,
        keyword=topic,
        category=topic.split()[0] if topic else "",
        ai_score=0.0,
        compliance_score=comp.score,
        similarity_score=0.0,
        reference_trend=topic,
        status="pending",
        strategy_date=strategy_date,
    )
    db.add(cand)
    db.flush()
    return cand


def _value_topics(problems, seeds) -> List[str]:
    topics = [f.keyword for _, _, f in problems if f.keyword]
    topics += seeds
    # fallbacks
    topics += ["旅行の持ち物", "収納のコツ", "時短テクニック"]
    return list(dict.fromkeys(topics))


def _assign_times(candidates, strategy) -> None:
    try:
        times = json.loads(strategy.posting_times)
    except Exception:
        times = []
    today = dt.date.today()
    for i, cand in enumerate(candidates):
        if i < len(times):
            hh, mm = times[i].split(":")
            cand.scheduled_time = dt.datetime.combine(
                today, dt.time(hour=int(hh), minute=int(mm))
            )
