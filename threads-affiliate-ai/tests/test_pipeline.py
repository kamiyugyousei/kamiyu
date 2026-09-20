"""End-to-end pipeline test (mock mode: no external keys)."""
from app.models import PostCandidate, Product, PublishedPost
from app.services import publisher
from app.services.pipeline import run_daily_pipeline
from app.services.simulate import simulate
from app.agents import GrowthManager
import datetime as dt


def test_full_pipeline_generates_candidates(db):
    summary = run_daily_pipeline(db, seed_keywords=["旅行便利グッズ"])
    assert summary["candidates"] > 0
    assert summary["affiliate"] >= 1

    cands = db.query(PostCandidate).all()
    assert len(cands) == summary["candidates"]
    # every candidate is pending (nothing auto-published)
    assert all(c.status == "pending" for c in cands)

    # affiliate candidates must carry PR label + affiliate url
    aff = [c for c in cands if c.post_type == "affiliate"]
    assert aff, "expected affiliate candidates"
    for c in aff:
        assert c.affiliate_url
        assert "PR" in c.body or "広告" in c.body

    # products were scored and stored
    assert db.query(Product).count() > 0


def test_approve_and_publish_flow(db):
    run_daily_pipeline(db, seed_keywords=["旅行便利グッズ"])
    cand = db.query(PostCandidate).filter(PostCandidate.post_type == "affiliate").first()
    assert cand is not None

    # nothing published before approval
    assert db.query(PublishedPost).count() == 0

    cand.status = "approved"
    db.commit()

    results = publisher.publish_due(db, force=True)
    assert len(results) >= 1
    assert db.query(PublishedPost).count() >= 1
    # threads mock id
    assert results[0]["mock"] is True


def test_analytics_after_simulation(db):
    run_daily_pipeline(db, seed_keywords=["旅行便利グッズ"])
    for c in db.query(PostCandidate).all():
        c.status = "approved"
    db.commit()
    publisher.publish_due(db, force=True)
    simulate(db)

    report = GrowthManager().analyze_day(db, dt.date.today(), run_id="test")
    assert report.posts_published >= 1
    assert report.revenue >= 0
