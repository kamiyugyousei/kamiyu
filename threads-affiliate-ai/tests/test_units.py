"""Unit tests for scoring, similarity, compliance, integrations."""
from app.agents.affiliate_matcher import AffiliateMatcher
from app.agents.compliance import ComplianceOfficer
from app.agents.copywriter import PR_LABEL
from app.agents.purchase_intent import PurchaseIntent
from app.integrations import rakuten
from app.schemas import ProductCandidate
from app.services.similarity import similarity


def test_rakuten_mock_returns_products():
    products = rakuten.search_products("旅行 充電", hits=10)
    assert 5 <= len(products) <= 10
    assert all(p.affiliate_url for p in products)
    assert all(p.name for p in products)


def test_similarity_detects_copy():
    a = "旅行中に充電が足りなくて困った話"
    assert similarity(a, a) > 0.99
    assert similarity(a, "全く関係のない料理レシピの投稿") < 0.4


def test_purchase_intent_prefers_problem():
    pi = PurchaseIntent()
    problem = pi.score_text("旅行中ホテルで充電口が足りなくて困った、便利なものが欲しい")
    fun = pi.score_text("京都旅行楽しかった、最高の思い出")
    assert problem > fun


def test_affiliate_score_range():
    matcher = AffiliateMatcher()
    pc = ProductCandidate(
        name="旅行 充電 USB充電器 コンパクト",
        price=2980,
        review_average=4.6,
        review_count=500,
        description="旅行の充電の悩みに。コンパクト。",
        keyword="旅行 充電",
    )
    score, breakdown = matcher._score(pc, intent=88.0, problem="充電", keyword="旅行 充電")
    assert 0 <= score <= 100
    assert abs(sum(breakdown.values()) - score) < 0.01
    assert score >= 50  # relevant product should score decently


def test_compliance_flags_missing_pr():
    officer = ComplianceOfficer()
    bad = officer.check("この商品便利です https://x", is_affiliate=True, affiliate_url="https://x")
    assert not bad.passed
    good = officer.check(
        f"充電の悩みに候補。¥2980 https://x\n{PR_LABEL}",
        is_affiliate=True,
        affiliate_url="https://x",
        price=2980,
    )
    assert good.passed


def test_posting_window_starts_at_8am():
    from app.agents.chief_manager import ChiefManager
    from app.config import settings

    times = ChiefManager()._posting_times(10)
    assert times[0] == f"{settings.first_post_hour:02d}:00"  # 毎朝8時から
    assert len(times) == 10
    # last post no later than the configured window end
    assert int(times[-1].split(":")[0]) <= settings.last_post_hour


def test_compliance_flags_fake_experience():
    officer = ComplianceOfficer()
    res = officer.check(
        f"私も愛用しています！最高です ¥1000 https://x\n{PR_LABEL}",
        is_affiliate=True,
        affiliate_url="https://x",
        price=1000,
    )
    assert any("体験談" in i for i in res.issues)
