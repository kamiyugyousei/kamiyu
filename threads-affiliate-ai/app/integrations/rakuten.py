"""Rakuten Ichiba Product Search API client (official API preferred).

Docs: https://webservice.rakuten.co.jp/api/ichibaitemsearch/
Falls back to deterministic mock products when RAKUTEN_APPLICATION_ID is unset,
so PHASE 1 runs end-to-end without credentials.
"""
from __future__ import annotations

import hashlib
from typing import List

import httpx

from app.config import settings
from app.schemas import ProductCandidate

_API = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"


def _affiliate_wrap(url: str, affiliate_id: str) -> str:
    """When Rakuten returns affiliateUrl directly we use it. This helper is a
    fallback for building a hml.rakuten.co.jp affiliate URL from affiliate_id."""
    if not affiliate_id:
        return url
    return f"https://hb.afl.rakuten.co.jp/hgc/{affiliate_id}/?pc={url}"


def search_products(keyword: str, hits: int = 10) -> List[ProductCandidate]:
    """Return up to `hits` products for a keyword. Real API when configured."""
    if not settings.rakuten_enabled:
        return _mock_products(keyword, hits)

    params = {
        "applicationId": settings.rakuten_application_id,
        "keyword": keyword,
        "hits": min(max(hits, 1), 30),
        "sort": "-reviewCount",
        "format": "json",
    }
    if settings.rakuten_affiliate_id:
        params["affiliateId"] = settings.rakuten_affiliate_id

    try:
        resp = httpx.get(_API, params=params, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        # network / quota error -> degrade to mock
        return _mock_products(keyword, hits)

    out: List[ProductCandidate] = []
    for entry in data.get("Items", []):
        it = entry.get("Item", entry)
        images = it.get("mediumImageUrls") or []
        image_url = ""
        if images:
            image_url = images[0].get("imageUrl", "") if isinstance(images[0], dict) else str(images[0])
        affiliate_url = it.get("affiliateUrl") or _affiliate_wrap(
            it.get("itemUrl", ""), settings.rakuten_affiliate_id
        )
        out.append(
            ProductCandidate(
                provider="rakuten",
                external_id=str(it.get("itemCode", "")),
                name=it.get("itemName", ""),
                price=float(it.get("itemPrice", 0) or 0),
                description=(it.get("itemCaption", "") or "")[:2000],
                review_average=float(it.get("reviewAverage", 0) or 0),
                review_count=int(it.get("reviewCount", 0) or 0),
                image_url=image_url,
                shop_name=it.get("shopName", ""),
                product_url=it.get("itemUrl", ""),
                affiliate_url=affiliate_url,
                genre=str(it.get("genreId", "")),
                postage_flag=int(it.get("postageFlag", 0) or 0),
                keyword=keyword,
            )
        )
    return out or _mock_products(keyword, hits)


def _mock_products(keyword: str, hits: int) -> List[ProductCandidate]:
    """Deterministic, clearly-fake products for local runs (provider=rakuten-mock)."""
    hits = min(max(hits, 5), 10)
    out: List[ProductCandidate] = []
    base_names = [
        f"{keyword} 便利アイテム 人気モデル",
        f"{keyword}用 コンパクト収納ケース",
        f"{keyword} 高評価 定番グッズ",
        f"{keyword} 軽量 携帯タイプ",
        f"{keyword} まとめ買いセット",
        f"{keyword} 折りたたみ式 多機能",
        f"{keyword} 大容量 タイプ",
        f"{keyword} プレゼントにも 人気",
        f"{keyword} 省スペース設計",
        f"{keyword} 時短 お助けグッズ",
    ]
    for i in range(hits):
        seed = int(hashlib.md5(f"{keyword}-{i}".encode()).hexdigest(), 16)
        price = 980 + (seed % 40) * 100
        review_count = 20 + (seed % 900)
        review_avg = round(3.6 + (seed % 14) / 10.0, 1)  # 3.6 - 4.9
        code = f"mockshop:{seed % 100000}"
        out.append(
            ProductCandidate(
                provider="rakuten-mock",
                external_id=code,
                name=base_names[i % len(base_names)],
                price=float(price),
                description=(
                    f"{keyword}に関する悩みを持つ人に選ばれている商品。"
                    "レビューでは『コンパクト』『使いやすい』との声が多い。（モックデータ）"
                ),
                review_average=review_avg,
                review_count=review_count,
                image_url="https://placehold.jp/300x300.png?text=" + keyword,
                shop_name=f"モックショップ{seed % 50}",
                product_url=f"https://item.rakuten.co.jp/{code}/",
                affiliate_url=f"https://hb.afl.rakuten.co.jp/hgc/mock/?pc=https://item.rakuten.co.jp/{code}/",
                genre=str(100000 + (seed % 900)),
                postage_flag=seed % 2,
                keyword=keyword,
            )
        )
    return out
