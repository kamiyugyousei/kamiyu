# 無料で24時間稼働（Oracle Cloud Always Free）

PCを閉じても**毎朝8時に自動投稿**できる、完全無料の24時間サーバーを作ります。
Oracle Cloud の「Always Free（ずっと無料）」枠を使います。

> クレジットカードの登録は必要ですが、Always Free枠だけを使えば**課金されません**。
> （有料に切り替えない限り請求は発生しません）

所要時間：初回30〜40分。難しく感じたら、各ステップの画面を私に見せてください。一緒に進めます。

---

## 全体の流れ
1. Oracleアカウントを作る
2. 無料の仮想サーバー（VM）を1台作る
3. サーバーに接続する
4. インストールコマンドを1行貼る（自動で全部入る）
5. Oracle側でポートを開ける
6. スマホでダッシュボードにアクセス

---

## ステップ1：Oracleアカウント作成
1. https://www.oracle.com/jp/cloud/free/ →「無料で始める」
2. メール・国（日本）・電話番号・**クレジットカード**を登録
   （本人確認用。Always Freeなら課金されません）
3. ホーム地域（リージョン）は **Japan Central (Osaka)** か **Japan East (Tokyo)** を選択

---

## ステップ2：無料サーバー（VM）を作る
1. Oracleコンソール左上メニュー →「コンピュート」→「インスタンス」→「**インスタンスの作成**」
2. 名前：`threads-ai`（何でもOK）
3. **イメージとシェイプ**：
   - イメージ →「イメージの変更」→ **Canonical Ubuntu 22.04** を選ぶ
   - シェイプ →「シェイプの変更」→「Ampere」→ **VM.Standard.A1.Flex**
     （**Always Free 対象**。OCPU=1、メモリ=6GB 程度でOK）
     - ※「Always Free-eligible（無料枠対象）」の表示があるものを選ぶ
     - Ampereが満杯で作れない時は「AMD」→ **VM.Standard.E2.1.Micro**（無料枠）でもOK
4. **SSHキー**（サーバーに入るための鍵）：
   - 「**自分のキーの生成**」を選ぶ →「**秘密キーの保存**」「公開キーの保存」を**両方ダウンロード**
   - ⚠️ 秘密キー（`ssh-key-xxxx.key`）は大切に保管。これでサーバーに入ります
5. 「作成」を押す → 1〜2分で起動。**パブリックIPアドレス**が表示されるのでメモ
   （例：`140.83.xx.xx`）

---

## ステップ3：サーバーに接続する

### Mac の場合（ターミナル）
```bash
chmod 600 ~/Downloads/ssh-key-xxxx.key
ssh -i ~/Downloads/ssh-key-xxxx.key ubuntu@（サーバーのIP）
```
初回は「Are you sure...?」と出たら `yes`。

### Windows の場合（PowerShell）
```powershell
ssh -i C:\Users\あなた\Downloads\ssh-key-xxxx.key ubuntu@（サーバーのIP）
```
※ ユーザー名は Ubuntu の場合 **ubuntu** です。

接続できると `ubuntu@threads-ai:~$` のような表示になります。

---

## ステップ4：インストール（1行で全自動）
接続した画面（サーバーの中）で、次の1行をコピペして実行：

```bash
curl -fsSL https://raw.githubusercontent.com/kamiyugyousei/kamiyu/claude/threads-affiliate-ai-system-15vu5d/threads-affiliate-ai/deploy/install.sh | bash
```

途中で以下を聞かれるので入力：
- 楽天 アプリケーションID
- 楽天 アフィリエイトID
- ダッシュボードのユーザー名（例：admin）
- ダッシュボードのパスワード（**必ず設定**。あなただけが知るもの）

数分待つと「完了しました 🎉」と、アクセスURLが表示されます。

> Dockerを入れた直後は権限反映のため、もし `permission denied` が出たら
> 一度 `exit` で抜けて再度SSH接続 → 同じコマンドをもう一度実行してください。

---

## ステップ5：Oracle側でポートを開ける（重要）
これをしないと外部から画面が開けません。

1. Oracleコンソール →「ネットワーキング」→「仮想クラウド・ネットワーク（VCN）」
2. 使っているVCN →「セキュリティ・リスト」→ デフォルトのものを開く
3. 「**イングレス・ルールの追加**」：
   - ソースCIDR：`0.0.0.0/0`
   - IPプロトコル：**TCP**
   - 宛先ポート範囲：**8000**
   - 「追加」

---

## ステップ6：アクセスする
スマホやPCのブラウザで：
```
http://（サーバーのIP）:8000
```
→ ユーザー名・パスワードを入れるとダッシュボードが開きます。
スマホのホーム画面に追加しておくと毎日ワンタップ。

---

## これで自動運転が始まります 🎉
- **毎朝7:00**：その日の投稿候補を自動生成
- **毎朝8:00〜22:00**：あなたが承認した投稿を60分間隔で自動投稿
- **23:00**：成果を分析／**0:00**：翌日戦略を更新

あなたの毎日の作業は「**スマホで候補を見て承認する**」だけ。
承認しておけば、PCを閉じていてもサーバーが8時から投稿します。

---

## よく使うコマンド（SSH接続して実行）
```bash
cd ~/kamiyu/threads-affiliate-ai
sudo docker compose logs -f       # 動作ログを見る（Ctrl+Cで戻る）
sudo docker compose restart       # 再起動
sudo docker compose down          # 停止
sudo docker compose up -d --build # 更新して起動
nano .env                         # 設定（キー等）を編集
```

## 最新版に更新したいとき
```bash
cd ~/kamiyu && git pull origin claude/threads-affiliate-ai-system-15vu5d
cd threads-affiliate-ai && sudo docker compose up -d --build
```

## Threadsへ実際に投稿したくなったら
`nano .env` で以下を追記して保存 →`sudo docker compose restart`：
```
THREADS_ACCESS_TOKEN=（Meta開発者サイトで発行）
THREADS_USER_ID=（同上）
```

---

## トラブル時
| 症状 | 対処 |
|---|---|
| 画面が開けない | ステップ5のポート開放（Oracle側）を確認。IPが正しいか確認 |
| permission denied (docker) | 一度 `exit` して再SSH接続し、インストールを再実行 |
| 商品が「モック」表示 | `.env` の楽天キーを確認 → `sudo docker compose restart` |
| ログを見たい | `sudo docker compose logs -f` |
| サーバー再起動後も自動で動く？ | はい（Docker自動起動＋restart設定済み） |
