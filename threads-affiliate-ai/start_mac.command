#!/bin/bash
# Mac用ワンクリック起動。Finderでダブルクリックするだけ。
# 初回は自動でPython環境を用意します。
cd "$(dirname "$0")" || exit 1

echo "=== Threads Affiliate AI を起動します ==="

# Python確認
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python3 が見つかりません。https://www.python.org/downloads/ からインストールしてください。"
  read -r -p "Enterで閉じる"
  exit 1
fi

# 仮想環境を初回だけ作成
if [ ! -d ".venv" ]; then
  echo "初回セットアップ中（数分かかります）..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

# .env が無ければ見本からコピー
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "⚠️ .env を作りました。楽天のキーを .env に入れてから使うと本番接続になります。"
fi

# ブラウザを開く（数秒後）
( sleep 4 && open "http://localhost:8000" ) &

echo "ダッシュボード: http://localhost:8000  （このウィンドウを閉じると停止します）"
python -m app.main
