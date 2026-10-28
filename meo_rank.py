#!/usr/bin/env python3
"""MEO順位チェッカー (Google Places API (New) Text Search)

使い方:
  export GOOGLE_PLACES_API_KEY=...

  # 1) 対象店舗の place_id を調べる (有料SKU・無料枠内で数回だけ)
  python3 meo_rank.py find "店名 地名"

  # 2) 格子状の地点で順位を測る (IDs Only = 無料枠上限なし)
  python3 meo_rank.py rank "渋谷 美容室" --lat 35.658 --lng 139.7016 \
      --grid 5 --spacing 500 --target ChIJxxxx --target ChIJyyyy

  出力: <out>.csv と <out>.html (ヒートマップ)

依存ライブラリなし (Python 3.8+ 標準ライブラリのみ)。
"""
import argparse
import csv
import html
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request

ENDPOINT = "https://places.googleapis.com/v1/places:searchText"
MAX_PAGES = 3  # Text Search は 20件 x 3ページ = 最大60件


def api_key():
    key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not key:
        sys.exit("環境変数 GOOGLE_PLACES_API_KEY を設定してください")
    return key


def search_text(body, field_mask):
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key(),
            "X-Goog-FieldMask": field_mask,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        sys.exit(f"APIエラー {e.code}: {e.read().decode(errors='replace')}")


def find(query, lang):
    # displayName 等を含むため Pro SKU (無料枠内で数回だけ使う想定)
    data = search_text(
        {"textQuery": query, "languageCode": lang, "pageSize": 5},
        "places.id,places.displayName,places.formattedAddress",
    )
    places = data.get("places", [])
    if not places:
        print("見つかりませんでした")
    for p in places:
        name = p.get("displayName", {}).get("text", "")
        print(f"{p['id']}\t{name}\t{p.get('formattedAddress', '')}")


def ranked_ids(keyword, lat, lng, radius, lang):
    """指定地点で検索したときの place_id を順位順に返す (IDs Only SKU)。"""
    body = {
        "textQuery": keyword,
        "languageCode": lang,
        "pageSize": 20,
        "locationBias": {
            "circle": {"center": {"latitude": lat, "longitude": lng}, "radius": radius}
        },
    }
    ids = []
    for _ in range(MAX_PAGES):
        data = search_text(body, "places.id,nextPageToken")
        ids += [p["id"] for p in data.get("places", [])]
        token = data.get("nextPageToken")
        if not token:
            break
        body["pageToken"] = token
        time.sleep(1)
    return ids


def grid_points(lat, lng, size, spacing_m):
    """中心から size x size の格子点 (spacing_m メートル間隔) を返す。"""
    half = (size - 1) / 2
    dlat = spacing_m / 111_320
    dlng = spacing_m / (111_320 * math.cos(math.radians(lat)))
    for row in range(size):
        for col in range(size):
            yield row, col, lat + (half - row) * dlat, lng + (col - half) * dlng


def rank(args):
    targets = args.target
    rows = []
    points = list(grid_points(args.lat, args.lng, args.grid, args.spacing))
    for i, (row, col, lat, lng) in enumerate(points, 1):
        ids = ranked_ids(args.keyword, lat, lng, args.radius, args.lang)
        for t in targets:
            pos = ids.index(t) + 1 if t in ids else None
            rows.append({"row": row, "col": col, "lat": round(lat, 6), "lng": round(lng, 6),
                         "place_id": t, "rank": pos, "results": len(ids)})
        print(f"[{i}/{len(points)}] ({lat:.5f},{lng:.5f}) "
              + " ".join(f"{t[:10]}…={r['rank'] or '圏外'}" for t, r in zip(targets, rows[-len(targets):])),
              file=sys.stderr)

    with open(f"{args.out}.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    write_heatmap(f"{args.out}.html", args, rows)
    print(f"保存しました: {args.out}.csv / {args.out}.html")


def cell_color(r):
    if r is None:
        return "#9e9e9e"
    if r <= 3:
        return "#2e7d32"
    if r <= 10:
        return "#f9a825"
    if r <= 20:
        return "#ef6c00"
    return "#c62828"


def write_heatmap(path, args, rows):
    sections = []
    for t, label in zip(args.target, args.label or args.target):
        cells = {(r["row"], r["col"]): r for r in rows if r["place_id"] == t}
        ranks = [r["rank"] for r in cells.values()]
        found = [r for r in ranks if r]
        avg = f"{sum(found) / len(found):.1f}" if found else "-"
        top3 = sum(1 for r in found if r <= 3)
        trs = []
        for row in range(args.grid):
            tds = []
            for col in range(args.grid):
                c = cells[(row, col)]
                tds.append(f'<td style="background:{cell_color(c["rank"])}" '
                           f'title="{c["lat"]},{c["lng"]}">{c["rank"] or "圏外"}</td>')
            trs.append("<tr>" + "".join(tds) + "</tr>")
        sections.append(
            f"<section><h2>{html.escape(label)}</h2>"
            f"<p>平均順位 {avg} ／ TOP3 {top3}/{len(ranks)} 地点 ／ 圏外 {ranks.count(None)} 地点</p>"
            f"<table>{''.join(trs)}</table></section>")

    page = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MEO順位 {html.escape(args.keyword)}</title>
<style>
body{{font-family:system-ui,sans-serif;margin:16px;background:#fff;color:#222}}
table{{border-collapse:collapse}}
td{{width:48px;height:48px;text-align:center;color:#fff;font-weight:bold;border:2px solid #fff;border-radius:50%}}
.legend span{{display:inline-block;padding:2px 8px;margin-right:4px;color:#fff;border-radius:4px}}
</style></head><body>
<h1>「{html.escape(args.keyword)}」MEO順位</h1>
<p>中心 {args.lat},{args.lng} ／ {args.grid}×{args.grid} 地点・{args.spacing}m 間隔 ／ 上が北</p>
<p class="legend"><span style="background:#2e7d32">1-3</span><span style="background:#f9a825">4-10</span>
<span style="background:#ef6c00">11-20</span><span style="background:#c62828">21-60</span>
<span style="background:#9e9e9e">圏外</span></p>
{''.join(sections)}
<p><small>Places API の検索結果順に基づく目安です。実際のGoogleマップ表示とは異なる場合があります。</small></p>
</body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)


def main():
    p = argparse.ArgumentParser(description="Google Places API で MEO 順位を測る")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("find", help="店名から place_id を調べる")
    f.add_argument("query")
    f.add_argument("--lang", default="ja")

    r = sub.add_parser("rank", help="格子状の地点で順位を測る")
    r.add_argument("keyword", help='検索キーワード (例: "渋谷 美容室")')
    r.add_argument("--lat", type=float, required=True, help="中心の緯度")
    r.add_argument("--lng", type=float, required=True, help="中心の経度")
    r.add_argument("--target", action="append", required=True, help="対象の place_id (複数可)")
    r.add_argument("--label", action="append", help="--target と同順の表示名 (任意)")
    r.add_argument("--grid", type=int, default=5, help="格子のサイズ N (N×N 地点, 既定 5)")
    r.add_argument("--spacing", type=float, default=500, help="格子の間隔 m (既定 500)")
    r.add_argument("--radius", type=float, default=500, help="locationBias の半径 m (既定 500)")
    r.add_argument("--lang", default="ja")
    r.add_argument("--out", default="meo_rank", help="出力ファイル名 (拡張子なし)")

    args = p.parse_args()
    if args.cmd == "find":
        find(args.query, args.lang)
    else:
        if args.label and len(args.label) != len(args.target):
            sys.exit("--label は --target と同じ数だけ指定してください")
        rank(args)


if __name__ == "__main__":
    main()
