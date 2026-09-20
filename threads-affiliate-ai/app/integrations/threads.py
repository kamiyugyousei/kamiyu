"""Threads (Meta) publishing + read integration.

Publishing uses the official Threads Graph API (two-step: create container,
then publish). When THREADS_ACCESS_TOKEN / THREADS_USER_ID are absent we return
a mock post id so the approval->publish flow can be exercised safely.

We never bypass login, CAPTCHA, or access restrictions.
"""
from __future__ import annotations

import time
import uuid
from typing import Optional

import httpx

from app.config import settings

_GRAPH = "https://graph.threads.net/v1.0"


def publish_post(text: str) -> dict:
    """Publish a text post to Threads. Returns {'id', 'mock', 'permalink'}."""
    if not settings.threads_publish_enabled:
        return {
            "id": f"mock_{uuid.uuid4().hex[:12]}",
            "mock": True,
            "permalink": "",
        }

    uid = settings.threads_user_id
    token = settings.threads_access_token
    try:
        # 1) create media container
        create = httpx.post(
            f"{_GRAPH}/{uid}/threads",
            data={"media_type": "TEXT", "text": text, "access_token": token},
            timeout=30.0,
        )
        create.raise_for_status()
        creation_id = create.json()["id"]

        # small delay recommended by Threads API before publish
        time.sleep(2)

        # 2) publish
        pub = httpx.post(
            f"{_GRAPH}/{uid}/threads_publish",
            data={"creation_id": creation_id, "access_token": token},
            timeout=30.0,
        )
        pub.raise_for_status()
        post_id = pub.json()["id"]
        return {"id": post_id, "mock": False, "permalink": ""}
    except Exception as exc:  # pragma: no cover - network dependent
        return {"id": "", "mock": False, "error": str(exc)}


def fetch_insights(threads_post_id: str) -> Optional[dict]:
    """Fetch impressions/likes/replies for a published post (best effort)."""
    if not settings.threads_publish_enabled or threads_post_id.startswith("mock_"):
        return None
    try:
        resp = httpx.get(
            f"{_GRAPH}/{threads_post_id}/insights",
            params={
                "metric": "views,likes,replies,reposts,quotes",
                "access_token": settings.threads_access_token,
            },
            timeout=20.0,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:  # pragma: no cover
        return None
