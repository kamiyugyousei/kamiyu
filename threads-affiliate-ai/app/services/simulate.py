"""Dev-only: synthesize performance + conversions for published posts, so the
Growth Manager / dashboard analytics can be exercised without live Threads data.

    python -m app.services.simulate
"""
from __future__ import annotations

import hashlib
import random

from sqlalchemy.orm import Session

from app.database import init_db, session_scope
from app.models import Conversion, PostCandidate, PostPerformance, PublishedPost


def simulate(db: Session) -> dict:
    published = db.query(PublishedPost).all()
    created = 0
    for post in published:
        seed = int(hashlib.md5(str(post.id).encode()).hexdigest(), 16)
        rnd = random.Random(seed)
        impressions = rnd.randint(500, 8000)
        clicks = int(impressions * rnd.uniform(0.01, 0.06))
        conversions = int(clicks * rnd.uniform(0.0, 0.05)) if post.post_type == "affiliate" else 0
        revenue = conversions * rnd.uniform(300, 2500)
        db.add(
            PostPerformance(
                published_post_id=post.id,
                impressions=impressions,
                clicks=clicks,
                replies=rnd.randint(0, 20),
                likes=rnd.randint(0, 300),
                followers_gained=rnd.randint(0, 15),
                conversions=conversions,
                revenue=round(revenue, 2),
            )
        )
        cand = db.get(PostCandidate, post.candidate_id) if post.candidate_id else None
        for _ in range(conversions):
            db.add(
                Conversion(
                    published_post_id=post.id,
                    provider="rakuten",
                    product_id=cand.product_id if cand else None,
                    reward=round(revenue / max(conversions, 1), 2),
                )
            )
        created += 1
    db.commit()
    return {"posts_simulated": created}


def main() -> None:
    init_db()
    with session_scope() as db:
        print(simulate(db))


if __name__ == "__main__":
    main()
