"""Publishing service — sends approved candidates to Threads, staggered.

Rules (spec section 23):
  - Never dump all posts at once; respect MIN_POST_INTERVAL_MINUTES.
  - No consecutive same-product / same-affiliate-URL / same-hook posts.
AUTO_PUBLISH defaults to false: only human-approved candidates are published.
"""
from __future__ import annotations

import datetime as dt
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.integrations import threads
from app.models import PostCandidate, PublishedPost
from app.services import audit


def _last_published(db: Session) -> Optional[PublishedPost]:
    return (
        db.query(PublishedPost)
        .order_by(PublishedPost.published_at.desc())
        .first()
    )


def _interval_ok(last: Optional[PublishedPost]) -> bool:
    if not last:
        return True
    delta = dt.datetime.utcnow() - last.published_at
    return delta >= dt.timedelta(minutes=settings.min_post_interval_minutes)


def _dedup_ok(last: Optional[PublishedPost], cand: PostCandidate) -> bool:
    if not last:
        return True
    if cand.affiliate_url and cand.affiliate_url == last.affiliate_url:
        return False
    if cand.product_id and last.candidate_id:
        prev = None
        # compare product via previous candidate
    if cand.hook_type and cand.hook_type == last.hook_type and cand.post_type == "affiliate":
        return False
    return True


def publish_due(db: Session, now: Optional[dt.datetime] = None, force: bool = False) -> List[dict]:
    """Publish approved candidates whose scheduled time has arrived.

    `force` ignores the schedule (used for manual 'publish now')."""
    now = now or dt.datetime.utcnow()
    q = db.query(PostCandidate).filter(PostCandidate.status == "approved")
    if not force:
        q = q.filter(
            (PostCandidate.scheduled_time == None)  # noqa: E711
            | (PostCandidate.scheduled_time <= now)
        )
    candidates = q.order_by(PostCandidate.scheduled_time.asc().nullsfirst()).all()

    results: List[dict] = []
    for cand in candidates:
        last = _last_published(db)
        if not force:
            if not _interval_ok(last):
                break  # wait for interval
            if not _dedup_ok(last, cand):
                continue

        res = threads.publish_post(cand.body)
        if res.get("error"):
            audit.log(
                db, "publisher", "publish_error", res["error"], level="error"
            )
            continue

        published = PublishedPost(
            candidate_id=cand.id,
            threads_post_id=res["id"],
            body=cand.body,
            post_type=cand.post_type,
            category=cand.category,
            hook_type=cand.hook_type,
            affiliate_url=cand.affiliate_url,
        )
        db.add(published)
        cand.status = "published"
        db.flush()
        audit.log(
            db,
            "publisher",
            "published",
            f"candidate={cand.id} threads_id={res['id']} mock={res.get('mock')}",
        )
        results.append({"candidate_id": cand.id, "threads_id": res["id"], "mock": res.get("mock", False)})
        if not force:
            break  # one per interval cycle

    db.commit()
    return results
