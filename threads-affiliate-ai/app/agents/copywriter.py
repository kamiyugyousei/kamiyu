"""AI社員09 — Threads Copywriter.

各商品について最低3案 (A:共感・体験風 / B:問題解決型 / C:発見・意外性型)。
- 未使用商品の虚偽体験談は書かない。事実ベース表現(レビュー多数/こういう悩みの人に候補)。
- 構造: HOOK→Problem→Empathy→Solution→Product→Benefit→CTA→PR表記→Affiliate Link
  だが毎回同じにしない。
- 生成後、既存投稿との類似度が閾値を超えたら破棄・再生成。
Value / Conversation / Experiment 投稿の生成もここで担当。
"""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.config import settings
from app.integrations import llm
from app.models import Product
from app.schemas import CopyVariant

PR_LABEL = "#PR #アフィリエイト広告"

# fact-based framings (no fake personal experience)
_FACT_FRAMES = [
    "楽天レビューでも件数が多く、同じ悩みの人に候補として挙がっています。",
    "こういう用途で評価されているアイテムです。",
    "レビューでは「使いやすい」という声が目立ちます。",
]


class Copywriter(BaseAgent):
    name = "copywriter"

    # ------------------------------------------------------------------ #
    # Affiliate posts (3 variants)
    # ------------------------------------------------------------------ #
    def write_affiliate_variants(
        self,
        db: Session,
        product: Product,
        problem: str,
        hook_type: str,
        run_id: str,
    ) -> List[CopyVariant]:
        variants = self._llm_variants(product, problem, hook_type)
        if not variants:
            variants = self._template_variants(product, problem, hook_type)
        self.log(
            db,
            "write_affiliate",
            f"商品[{product.name[:20]}]に3案生成 hook={hook_type}",
            run_id=run_id,
        )
        return variants

    def _llm_variants(
        self, product: Product, problem: str, hook_type: str
    ) -> List[CopyVariant]:
        if not settings.llm_enabled:
            return []
        system = (
            "あなたは日本語のThreadsアフィリエイトコピーライターです。"
            "重要: 実際に使っていない商品について『使ってみた』『愛用中』等の"
            "虚偽の体験談を書いてはいけません。事実ベース(レビュー多数/こういう悩みの人向け)"
            "で書いてください。各案の末尾に必ず『" + PR_LABEL + "』とアフィリエイトURLを入れてください。"
        )
        prompt = (
            f"商品名: {product.name}\n価格: {int(product.price)}円\n"
            f"レビュー: 平均{product.review_average} / {product.review_count}件\n"
            f"想定する悩み: {problem}\nHookタイプ: {hook_type}\n"
            f"アフィリエイトURL: {product.affiliate_url}\n\n"
            "3つの投稿案を作成してください。A=共感・状況描写型 / B=問題解決型 / "
            "C=発見・意外性型。各案は120〜400文字。'---'で区切って出力。"
        )
        text = llm.complete(prompt, system=system, temperature=0.9)
        if not text:
            return []
        chunks = [c.strip() for c in text.split("---") if c.strip()]
        out: List[CopyVariant] = []
        for i, chunk in enumerate(chunks[:3]):
            body = self._ensure_disclosure(chunk, product)
            out.append(CopyVariant(variant="ABC"[i], body=body, hook_type=hook_type))
        return out if len(out) == 3 else []

    def _template_variants(
        self, product: Product, problem: str, hook_type: str
    ) -> List[CopyVariant]:
        name = product.name
        price = int(product.price)
        url = product.affiliate_url
        fact = _FACT_FRAMES[product.id % len(_FACT_FRAMES)] if product.id else _FACT_FRAMES[0]
        rev = (
            f"（★{product.review_average}・レビュー{product.review_count}件）"
            if product.review_count
            else ""
        )

        # A: 共感・状況描写型 (体験ではなく "あるある" 状況)
        a = (
            f"「{problem}」って地味にストレスですよね。\n"
            f"同じ悩みの人、けっこう多いみたいです。\n"
            f"そんなときの候補が {name}。{fact}\n"
            f"気になる人はチェックしてみてください👇 {price}円前後 {rev}\n"
            f"{url}\n{PR_LABEL}"
        )
        # B: 問題解決型 (HOOK→Problem→Solution→Benefit→CTA)
        b = (
            f"{problem}を解決したい人へ。\n"
            f"ポイントは「{self._benefit_phrase(name)}」。\n"
            f"{name} は {fact}\n"
            f"→ 迷ったら候補に。{price}円前後 {rev}\n"
            f"{url}\n{PR_LABEL}"
        )
        # C: 発見・意外性型
        c = (
            f"え、これ知らなかった…\n"
            f"{problem}、道具ひとつで変わることがあるらしい。\n"
            f"それが {name}。{fact}\n"
            f"気になった人はどうぞ👇 {price}円前後 {rev}\n"
            f"{url}\n{PR_LABEL}"
        )
        return [
            CopyVariant(variant="A", body=a, hook_type=hook_type or "共感型"),
            CopyVariant(variant="B", body=b, hook_type=hook_type or "悩み解決型"),
            CopyVariant(variant="C", body=c, hook_type=hook_type or "意外性型"),
        ]

    def _benefit_phrase(self, name: str) -> str:
        if any(w in name for w in ["収納", "ケース", "バッグ", "圧縮"]):
            return "かさばりを減らす"
        if any(w in name for w in ["充電", "バッテリー", "電源", "タップ"]):
            return "電源の不安をなくす"
        if any(w in name for w in ["時短", "多機能", "折りたたみ"]):
            return "手間を減らす"
        return "悩みをひとつ減らす"

    def _ensure_disclosure(self, body: str, product: Product) -> str:
        if "PR" not in body and "広告" not in body:
            body += f"\n{PR_LABEL}"
        if product.affiliate_url and product.affiliate_url not in body:
            body += f"\n{product.affiliate_url}"
        return body

    # ------------------------------------------------------------------ #
    # Value / Conversation / Experiment posts (no affiliate link)
    # ------------------------------------------------------------------ #
    def write_value_post(self, db: Session, topic: str, run_id: str) -> CopyVariant:
        body = (
            f"【{topic}のコツ】\n"
            f"・買う前に用途とサイズを決める\n"
            f"・レビュー件数が多いものは失敗が少なめ\n"
            f"・「使う場所」を先に決めると選びやすい\n"
            f"保存しておくと地味に役立ちます📌"
        )
        llm_body = llm.complete(
            f"「{topic}」について、商品宣伝なしで役立つThreads投稿(150文字前後)を書いて。"
            "箇条書き可。絵文字少し。",
        )
        if llm_body:
            body = llm_body
        self.log(db, "write_value", f"Value投稿生成: {topic}", run_id=run_id)
        return CopyVariant(variant="V", body=body, hook_type="ノウハウ型")

    def write_conversation_post(self, db: Session, topic: str, run_id: str) -> CopyVariant:
        body = f"{topic}で「持ってくれば良かった」と思ったもの、ありますか？👀\nコメントで教えてください！"
        llm_body = llm.complete(
            f"「{topic}」について、返信を誘発するThreadsの質問投稿を1つ(80文字前後)。"
        )
        if llm_body:
            body = llm_body
        self.log(db, "write_conversation", f"会話投稿生成: {topic}", run_id=run_id)
        return CopyVariant(variant="Q", body=body, hook_type="質問型")

    def write_experiment_post(
        self, db: Session, topic: str, hook_type: str, run_id: str
    ) -> CopyVariant:
        body = (
            f"[実験] {topic}\n"
            f"今日は新しい切り口で。あなたなら何を重視しますか？"
        )
        self.log(
            db, "write_experiment", f"実験投稿生成: {topic} hook={hook_type}", run_id=run_id
        )
        return CopyVariant(variant="X", body=body, hook_type=hook_type or "実験型")
