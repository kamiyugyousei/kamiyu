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

  # 3) ある地点での上位店舗 (競合) を一覧する (評価・口コミ数を含むため Enterprise SKU)
  python3 meo_rank.py top "渋谷 美容室" --lat 35.658 --lng 139.7016 --limit 10

  # 4) 複数の rank 結果 (キーワード違い・店舗違い) を1枚のレポートにまとめる
  python3 meo_rank.py report --title "〇〇事務所 MEO順位" \
      --card "kw1.csv:ChIJxxxx:「西宮 行政書士」" --card "kw2.csv:ChIJxxxx:「行政書士」" \
      --out report

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
        "places.id,places.displayName,places.formattedAddress,places.location",
    )
    places = data.get("places", [])
    if not places:
        print("見つかりませんでした")
    for p in places:
        name = p.get("displayName", {}).get("text", "")
        loc = p.get("location", {})
        print(f"{p['id']}\t{name}\t{loc.get('latitude')},{loc.get('longitude')}\t{p.get('formattedAddress', '')}")


def location_bias(lat, lng, radius):
    return {"circle": {"center": {"latitude": lat, "longitude": lng}, "radius": radius}}


def top(args):
    # rating / userRatingCount を含むため Enterprise SKU (無料枠は少なめ)。1回だけ呼ぶ
    data = search_text(
        {"textQuery": args.keyword, "languageCode": args.lang, "pageSize": args.limit,
         "locationBias": location_bias(args.lat, args.lng, args.radius)},
        "places.id,places.displayName,places.rating,places.userRatingCount",
    )
    for i, p in enumerate(data.get("places", []), 1):
        name = p.get("displayName", {}).get("text", "")
        print(f"{i}\t{p['id']}\t{name}\t{p.get('rating', '-')}\t{p.get('userRatingCount', 0)}")


def ranked_ids(keyword, lat, lng, radius, lang):
    """指定地点で検索したときの place_id を順位順に返す (IDs Only SKU)。"""
    body = {
        "textQuery": keyword,
        "languageCode": lang,
        "pageSize": 20,
        "locationBias": location_bias(lat, lng, radius),
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


def report(args):
    """複数の rank CSV を横並びのカードにして1枚の HTML にまとめる。"""
    cards = []
    short_lists = False
    for spec in args.card:
        try:
            path, pid, label = spec.split(":", 2)
        except ValueError:
            sys.exit(f"--card は CSV:place_id:見出し の形式で指定してください: {spec}")
        with open(path, encoding="utf-8-sig") as f:
            rows = [r for r in csv.DictReader(f) if r["place_id"] == pid]
        if not rows:
            sys.exit(f"{path} に {pid} の行がありません")
        size = max(int(r["row"]) for r in rows) + 1
        rows.sort(key=lambda r: (int(r["row"]), int(r["col"])))
        ranks = [int(r["rank"]) if r["rank"] else None for r in rows]
        short_lists |= any(r["rank"] == "" and int(r["results"]) < 60 for r in rows)
        found = [r for r in ranks if r]
        center = (size // 2) * size + size // 2
        cells = "".join(
            f'<div class="c {color_class(r)}{" ctr" if i == center else ""}">{r or "圏外"}</div>'
            for i, r in enumerate(ranks))
        avg = f"{sum(found) / len(found):.1f}" if found else "-"
        cards.append(
            f'<div class="card"><h2>{html.escape(label)}</h2>'
            f'<div class="grid" style="grid-template-columns:repeat({size},66px)">{cells}</div>'
            f'<div class="stat"><div><small>TOP3</small><b>{sum(1 for r in found if r <= 3)}<i>/{len(ranks)}</i></b></div>'
            f'<div><small>平均</small><b>{avg}<i>位</i></b></div>'
            f'<div><small>圏外</small><b>{ranks.count(None)}<i>地点</i></b></div></div></div>')

    cols = min(len(cards), 3)
    note = ("<p class=\"note\">※ 一部の地点は検索候補が60件未満でした。その地点の「圏外」は順位が低いのではなく、候補に含まれなかったという意味です</p>"
            if short_lists else "")
    page = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@500;700;900&display=block" rel="stylesheet">
<title>{html.escape(args.title)}</title>
<style>
:root{{--ink:#16213a;--sub:#5b6478;--g:#2e7d32;--y:#f2a900;--o:#ef6c00;--r:#c62828;--n:#9aa1ad}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{cols * 476 + 96}px;background:#f6f8fc;font-family:"Noto Sans JP","IPAGothic",sans-serif;color:var(--ink);padding:40px 48px}}
h1{{font-size:44px;font-weight:900}} .lead{{font-size:22px;color:var(--sub);margin-top:8px}}
.cards{{display:grid;grid-template-columns:repeat({cols},1fr);gap:24px;margin-top:26px}}
.card{{background:#fff;border-radius:24px;padding:24px;box-shadow:0 4px 18px rgba(22,33,58,.07)}}
h2{{font-size:28px;font-weight:900;text-align:center}}
.grid{{display:grid;gap:10px;justify-content:center;margin:18px 0}}
.c{{width:66px;height:66px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:900;font-size:26px}}
.c.n{{font-size:16px}} .c.ctr{{outline:4px solid var(--ink);outline-offset:3px}}
.g{{background:var(--g)}}.y{{background:var(--y)}}.o{{background:var(--o)}}.r{{background:var(--r)}}.n{{background:var(--n)}}
.stat{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}
.stat div{{background:#f3f5fa;border-radius:14px;padding:8px;text-align:center}}
.stat small{{display:block;font-size:17px;color:var(--sub);font-weight:700}} .stat b{{font-size:32px;font-weight:900}} .stat i{{font-style:normal;font-size:17px;color:var(--sub)}}
.legend{{display:flex;gap:22px;justify-content:center;margin-top:20px;font-size:19px;font-weight:700;color:var(--sub)}}
.legend span::before{{content:"";display:inline-block;width:16px;height:16px;border-radius:50%;margin-right:6px;vertical-align:-2px;background:var(--c)}}
.note{{margin-top:12px;font-size:17px;color:var(--sub);text-align:center}}
</style></head><body>
<h1>{html.escape(args.title)}</h1>
<p class="lead">{html.escape(args.subtitle)}</p>
<div class="cards">{''.join(cards)}</div>
<div class="legend"><span style="--c:var(--g)">1〜3位</span><span style="--c:var(--y)">4〜10位</span><span style="--c:var(--o)">11〜20位</span><span style="--c:var(--r)">21位〜</span><span style="--c:var(--n)">圏外</span></div>
{note}
</body></html>"""
    with open(f"{args.out}.html", "w", encoding="utf-8") as f:
        f.write(page)
    print(f"保存しました: {args.out}.html")


def color_class(r):
    if r is None:
        return "n"
    return "g" if r <= 3 else "y" if r <= 10 else "o" if r <= 20 else "r"


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

    t = sub.add_parser("top", help="指定地点での上位店舗 (競合) を一覧する")
    t.add_argument("keyword")
    t.add_argument("--lat", type=float, required=True)
    t.add_argument("--lng", type=float, required=True)
    t.add_argument("--radius", type=float, default=500)
    t.add_argument("--limit", type=int, default=10, help="件数 (最大20)")
    t.add_argument("--lang", default="ja")

    rp = sub.add_parser("report", help="複数の rank 結果を1枚の HTML にまとめる")
    rp.add_argument("--title", required=True)
    rp.add_argument("--subtitle", default="")
    rp.add_argument("--card", action="append", required=True,
                    help="CSV:place_id:見出し (複数可。3枚ごとに折り返し)")
    rp.add_argument("--out", default="report")

    args = p.parse_args()
    if args.cmd == "find":
        find(args.query, args.lang)
    elif args.cmd == "top":
        top(args)
    elif args.cmd == "report":
        report(args)
    else:
        if args.label and len(args.label) != len(args.target):
            sys.exit("--label は --target と同じ数だけ指定してください")
        rank(args)


if __name__ == "__main__":
    main()
