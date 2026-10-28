# kamiyu

## MEO順位チェッカー (`meo_rank.py`)

Google Places API (New) の Text Search で、指定した地点・キーワードで店舗が何位に出るかを格子状に測り、CSV とヒートマップ (HTML) を出力します。Python 標準ライブラリのみで動きます。

```bash
export GOOGLE_PLACES_API_KEY=xxxx

# 1) 対象店舗の place_id を調べる（店名などを取得するため有料SKU。無料枠内で数回だけ）
python3 meo_rank.py find "店名 渋谷"

# 2) 5×5地点・500m間隔で順位を測る（IDのみ取得 = IDs Only SKU）
python3 meo_rank.py rank "渋谷 美容室" --lat 35.658 --lng 139.7016 \
  --target ChIJ自店 --label 自店 --target ChIJ競合 --label 競合A
# → meo_rank.csv / meo_rank.html
```

- 順位チェックは `places.id` だけを取得するため、IDs Only SKU（無料枠の上限なし）で動きます。利用前に公式の料金表で最新の条件を確認してください。
- 1地点につき最大3リクエスト（20件×3ページ = 60位まで）。61位以下は「圏外」になります。
- 順位は API の並び順に基づく**目安**です。実際の Google マップの表示は、検索する人の位置や履歴で変わります。
- 予算アラートと API の割り当て上限を設定しておくと安心です。
