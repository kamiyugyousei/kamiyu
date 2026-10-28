# kamiyu

## MEO順位チェック（Claude Code スキル `meo-rank`）

Google Places API (New) で、指定した地点の周りに格子状の地点を置き、各地点で店舗が何位に出るかを測ります。結果はヒートマップ・CSV・まとめ画像で出力します。

### Claude Code で使う
環境変数 `GOOGLE_PLACES_API_KEY` を設定して、こう頼むだけで動きます。
> 「〇〇事務所のMEO順位を測って」
> 「西宮北口 美容室で上位10店のヒートマップを作って」

手順や料金区分は `.claude/skills/meo-rank/SKILL.md` に書いてあります。

### コマンドで直接使う
```bash
S=.claude/skills/meo-rank/scripts/meo_rank.py
python3 $S find "店名 地名"                                   # place_id と座標
python3 $S rank "西宮 行政書士" --lat 34.7585 --lng 135.3591 \
  --spacing 1000 --radius 1000 --target ChIJ... --label 自店 --out results/kw1
python3 $S top "西宮 行政書士" --lat 34.7585 --lng 135.3591     # 競合の一覧
python3 $S report --title "MEO順位" --card "results/kw1.csv:ChIJ...:「西宮 行政書士」" --out results/report
```

- `rank` は `places.id` だけを取得するので、無料枠の上限がない区分（IDs Only）で動きます。最新の料金表で確認してください。
- 順位は API の並び順に基づく**目安**です。実際の Google マップの表示は、検索する人の位置や履歴で変わります。
- 出力は `results/` に置きます（Git の管理対象外）。
