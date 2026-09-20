"""AI社員11 — Conversation Agent.

会話を生む投稿を作成し、返信から新しい悩み/需要/キーワードを発見する土台。
PHASE 1 では投稿生成のみ(返信収集は browser/threads read で PHASE 後半に拡張)。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.copywriter import Copywriter
from app.schemas import CopyVariant


class ConversationAgent(BaseAgent):
    name = "conversation_agent"

    def __init__(self) -> None:
        self.copywriter = Copywriter()

    def make(self, db: Session, topic: str, run_id: str) -> CopyVariant:
        variant = self.copywriter.write_conversation_post(db, topic, run_id)
        self.log(db, "make", f"会話投稿: {topic}", run_id=run_id)
        return variant
