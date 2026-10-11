---
name: expedia-club-lounge-hotels
description: エクスペディア（Expedia MCP の search_hotels）で指定都市のホテルを検索し、クラブラウンジ（エグゼクティブラウンジ）があるホテルだけを選んで日本語で一覧にする。「〇〇のクラブラウンジのあるホテル」「ラウンジ付きホテルをエクスペディアで」などの依頼で使う。
---

# エクスペディアでクラブラウンジのあるホテルを探す

## 前提
- Expedia の `search_hotels` には「クラブラウンジ」フィルタが**無い**。検索結果を取得し、ラウンジ有無は自分の知識（ブランド・ホテル個別の情報）で判定する。
- `star_ratings` / `property_themes` フィルタは無視されることがある。結果を自分で 4.5〜5 つ星中心に絞る。

## 手順
1. ツール読込: `ToolSearch` で `select:mcp__Expedia__search_hotels`。
2. 日付: ユーザー指定がなければ「今日+30日」から3泊。大人2名（デフォルト）。
3. 検索（`limit: 20`、`offset: 0` と `offset: 20` の2回、必要なら `property_themes: ["LUXURY_PROPERTY"]` でもう1回）。
   - `destination` は `"Jakarta, Indonesia"` のように英語「City, Country」。
   - **注意**: `user_location` や改行入り `query_text` を渡すと `Unknown error` になることがある。エラー時は `destination` / `check_in_date` / `check_out_date` / `limit` / `offset` の最小構成で再試行する。
4. 重複を除き、下記の判定基準でクラブラウンジのあるホテルを抽出。
5. 結果を表で出す（下記フォーマット）。

## クラブラウンジ判定の目安（ブランド別）
| 判定 | ブランド / ラウンジ名 |
|---|---|
| ほぼ確実にあり | Grand Hyatt / Hyatt Regency（Grand Club / Regency Club）、InterContinental（Club InterContinental）、Langham（Langham Club）、Shangri-La（Horizon Club）、Fairmont（Fairmont Gold）、Pullman（Executive Lounge）、Westin / Sheraton（Club Lounge）、JW Marriott・Ritz-Carlton（Club Lounge、本館のみ）、Meliá / Gran Meliá（The Level）、Pan Pacific（Pacific Club）、Conrad / Hilton / DoubleTree の大型店（Executive Lounge）、Crowne Plaza（Club Lounge） |
| ほぼ無し | Four Seasons、Mandarin Oriental、Raffles、Aman、Alila、Tribute Portfolio・Autograph などのブティック系、サービスアパートメント（Fraser・Oakwood・Residences 等）、Holiday Inn Express |
| 要確認 | Kempinski、Mulia、Unbound Collection、Mövenpick、ローカル系5つ星 |

- 判定に自信がないホテルは「要確認」と明記し、断定しない。
- 「ほぼ確実」でも改装・閉鎖で変わり得るため、最後に「ラウンジ付き客室（クラブルーム）で予約するとアクセス可。予約前にホテル公式で確認を」と添える。

## 出力フォーマット
| ホテル | ラウンジ名 | 評価（クチコミ数） | 1泊目安 | リンク |
|---|---|---|---|---|

- 価格は Expedia の標準料金（通貨はレスポンスの `currency`、通常 USD）で、検索日程を明記。クラブルームは表示価格より高い点も注記。
- リンクはレスポンスの `url` をそのまま使う。
- 末尾に「Expedia の検索結果に出なかったが、その都市でクラブラウンジがある有名ホテル」を数件補足してよい（Expedia 未確認と明記）。

## 参考: ジャカルタ（2026-10 検索時）
Expedia の結果に出たラウンジ付き: Grand Hyatt Jakarta（Grand Club）、The Langham Jakarta（Langham Club）、InterContinental Jakarta Pondok Indah（Club InterContinental）、Pullman Jakarta Central Park（Executive Lounge）、Gran Meliá Jakarta（The Level）、Pan Pacific Jakarta（Pacific Club）、DoubleTree by Hilton Jakarta Diponegoro（Executive Lounge）。
結果外の候補: Shangri-La Jakarta、Fairmont Jakarta、JW Marriott Jakarta、The Ritz-Carlton Jakarta（Mega Kuningan / Pacific Place）、The Westin Jakarta、Sheraton Grand Jakarta Gandaria City、Pullman Jakarta Indonesia Thamrin。
