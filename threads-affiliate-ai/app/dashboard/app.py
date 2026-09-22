"""FastAPI app: dashboard top screen + approval API (spec sections 21,34,35,36)."""
from __future__ import annotations

import datetime as dt
import os
import secrets
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.orm import Session

from app.agents import GrowthManager
from app.config import settings
from app.database import get_db, init_db
from app.models import ApprovalQueueItem, PostCandidate, Product, PublishedPost
from app.services import publisher

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app = FastAPI(title="Threads Affiliate AI - 承認ダッシュボード")


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """HTTP Basic auth for public deployments. Active only when a password is set.
    /healthz is always open so hosting health checks keep working."""

    async def dispatch(self, request: Request, call_next):
        pwd = settings.dashboard_password
        if not pwd or request.url.path == "/healthz":
            return await call_next(request)

        header = request.headers.get("Authorization", "")
        if header.startswith("Basic "):
            import base64

            try:
                decoded = base64.b64decode(header[6:]).decode("utf-8")
                user, _, passwd = decoded.partition(":")
                if secrets.compare_digest(user, settings.dashboard_user) and secrets.compare_digest(
                    passwd, pwd
                ):
                    return await call_next(request)
            except Exception:
                pass
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Threads Affiliate AI"'},
            content="Unauthorized",
        )


app.add_middleware(BasicAuthMiddleware)


@app.on_event("startup")
def _startup() -> None:
    init_db()


def _today() -> dt.date:
    return dt.date.today()


@app.get("/healthz")
def healthz():
    """Health check for hosting platforms."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    report = GrowthManager().analyze_day(db, _today(), run_id="dashboard")
    pending = (
        db.query(PostCandidate)
        .filter(PostCandidate.status == "pending")
        .order_by(PostCandidate.post_type, PostCandidate.scheduled_time)
        .all()
    )
    approved = (
        db.query(PostCandidate)
        .filter(PostCandidate.status.in_(["approved", "postponed"]))
        .order_by(PostCandidate.scheduled_time)
        .all()
    )
    published_today = (
        db.query(PublishedPost)
        .filter(PublishedPost.published_at >= dt.datetime.combine(_today(), dt.time.min))
        .order_by(PublishedPost.published_at.desc())
        .all()
    )
    products = {p.id: p for p in db.query(Product).all()}
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "report": report,
            "pending": pending,
            "approved": approved,
            "published_today": published_today,
            "products": products,
            "settings": settings,
        },
    )


@app.post("/candidate/{cid}/action")
def candidate_action(
    cid: int,
    action: str = Form(...),
    body: Optional[str] = Form(None),
    scheduled_time: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    cand = db.get(PostCandidate, cid)
    if not cand:
        raise HTTPException(404, "candidate not found")

    if action == "approve":
        cand.status = "approved"
    elif action == "reject":
        cand.status = "rejected"
    elif action == "postpone":
        cand.status = "postponed"
        if scheduled_time:
            cand.scheduled_time = dt.datetime.fromisoformat(scheduled_time)
    elif action == "edit":
        if body is not None:
            cand.body = body
        cand.status = "approved"
    else:
        raise HTTPException(400, f"unknown action {action}")

    db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/publish-now/{cid}")
def publish_now(cid: int, db: Session = Depends(get_db)):
    cand = db.get(PostCandidate, cid)
    if not cand:
        raise HTTPException(404, "candidate not found")
    if cand.status != "approved":
        cand.status = "approved"
        db.commit()
    results = publisher.publish_due(db, force=True)
    return JSONResponse({"published": results})


@app.get("/api/report")
def api_report(db: Session = Depends(get_db)):
    report = GrowthManager().analyze_day(db, _today(), run_id="api")
    return report.model_dump()


@app.get("/api/candidates")
def api_candidates(status: str = "pending", db: Session = Depends(get_db)):
    rows = db.query(PostCandidate).filter(PostCandidate.status == status).all()
    return [
        {
            "id": c.id,
            "post_type": c.post_type,
            "variant": c.variant,
            "body": c.body,
            "hook_type": c.hook_type,
            "ai_score": c.ai_score,
            "compliance_score": c.compliance_score,
            "similarity_score": c.similarity_score,
            "affiliate_url": c.affiliate_url,
            "scheduled_time": c.scheduled_time.isoformat() if c.scheduled_time else None,
        }
        for c in rows
    ]


@app.get("/api/approval-queue")
def api_approval_queue(db: Session = Depends(get_db)):
    rows = db.query(ApprovalQueueItem).filter(ApprovalQueueItem.status == "pending").all()
    return [{"id": r.id, "kind": r.kind, "reason": r.reason, "payload": r.payload} for r in rows]
