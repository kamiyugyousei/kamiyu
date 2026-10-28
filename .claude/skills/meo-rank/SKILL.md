---
name: meo-rank
description: Google Places API (New) で店舗のMEO順位（Googleマップで何位に出るか）を、指定地点の周りに格子状に置いた複数地点で測り、ヒートマップとCSV、競合一覧、まとめ画像を作る。「MEO順位を測って」「〇〇駅 美容室で何位？」「この店のMEOを調べて」「競合のマップ順位」「ヒートマップを作って」などの依頼で使う。
---

# MEO順位チェック

スクリプト: `.claude/skills/meo-rank/scripts/meo_rank.py`（Python 標準ライブラリのみ）。以下 `S=.claude/skills/meo-rank/scripts/meo_rank.py` とする。

## 前提

- 環境変数 `GOOGLE_PLACES_API_KEY` が必要。未設定なら、Google Cloud で Places API (New) を有効にしてAPIキーを作り、環境変数に設定するよう案内する。キーをチャットに貼らせない。もし貼られたら、ファイルやGitに書かず、使い終わったら再生成するよう勧める。
- 出力は `results/` に置く（`.gitignore` 済み）。顧客や他店のデータはコミットしない。

## 料金区分（コストを抑える）

| コマンド | 取得する項目 | SKU | 使い方 |
|---|---|---|---|
| `rank` | `places.id` だけ | Text Search Essentials (IDs Only)：無料枠の上限なし | 何地点でも回してよい |
| `find` | 店名・住所 | Pro（月 5,000 件まで無料） | 対象店ごとに1回 |
| `top` | 評価・口コミ数も含む | Enterprise（月 1,000 件まで無料） | キーワードごとに1回まで |

## 手順

1. **対象店舗の place_id を調べる**
   `python3 $S find "店名 地名"`
   出力は「place_id、名前、緯度,経度、住所」の順。同じ名前の店が複数出たら、住所で見分ける。
2. **中心座標を決める**
   - 店舗を測るときは、`find` で出た店舗の緯度経度を中心にする。
   - 「〇〇駅で」と言われたら駅を中心にする。駅の座標は `find "〇〇駅"` で取れる。
3. **キーワードを決める**
   ユーザーの指定がなければ、「地名＋業種」「最寄り駅名＋業種」「業種だけ」の3つを提案して測る。
4. **格子の設定を決める**
   - 店に歩いて来る業種（美容室・飲食店など）：`--grid 5 --spacing 500 --radius 500`
   - 広い範囲から客が来る業種（士業・クリニックなど）：`--spacing 1000 --radius 1000`
5. **順位を測る**（キーワードごとに1回）
   `python3 $S rank "キーワード" --lat .. --lng .. --target ID --label 名前 [--target ..] --out results/xxx`
   - `--target` は何件付けても API の呼び出し回数は変わらない。
   - 25地点の場合、1キーワードあたり最大75回呼び出す。
6. **競合を確認する**（必要なとき）
   `python3 $S top "キーワード" --lat .. --lng .. --radius ..`
7. **1枚の画像にまとめる**
   `python3 $S report --title "..." --subtitle "中心・間隔・計測日" --card "results/a.csv:ID:「キーワードA」" ... --out results/xxx_report`
   HTML を Playwright で PNG にする。幅は HTML の body 幅に合わせ、`fullPage:true` で撮る。PNG はユーザーに送る。
   ```bash
   node -e "const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1500,height:600}});await p.goto('file://'+require('path').resolve('results/xxx_report.html'),{waitUntil:'networkidle'});await p.screenshot({path:'results/xxx_report.png',fullPage:true});await b.close()})()"
   ```

## 結果の伝え方

- キーワードごとに、**TOP3に入った地点数**（一番重要）、平均順位、中心地点での順位を表にする。
- 強い方角・弱い方角を、具体的な地名で説明する。上が北。
- `results` 列が60未満の地点の「圏外」は、順位が低いのではない。Google が返した候補が少なく、その中に入らなかったという意味なので、そう説明する。
- 競合の評価と口コミ数を並べて、改善の余地を示す。
- 必ず添えること：API の並び順に基づく**目安**であり、実際のマップ表示は検索する人の位置や履歴で変わる。
- 改善策として**店名にキーワードを足すことは勧めない**（Google のガイドライン違反）。

## X（SNS）投稿用の画像を作るとき

他店のデータを使う場合は、店名を「A店」などにし、エリアも「関西のある駅前」のように伏せる。口コミ件数と評価は「100件以上」「★4点台後半」のように幅で書く（件数と評価の組み合わせで店が特定できるため）。サイズは 1080×1350 で作る。
