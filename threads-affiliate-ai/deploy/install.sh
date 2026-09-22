#!/usr/bin/env bash
# =====================================================================
# Threads Affiliate AI - Oracle Cloud (Ubuntu) 自動インストーラー
# 使い方: 新しいUbuntuサーバーに接続して、この1行を実行:
#   curl -fsSL https://raw.githubusercontent.com/kamiyugyousei/kamiyu/claude/threads-affiliate-ai-system-15vu5d/threads-affiliate-ai/deploy/install.sh | bash
# もしくはリポジトリをcloneして bash deploy/install.sh
# =====================================================================
set -euo pipefail

REPO_URL="https://github.com/kamiyugyousei/kamiyu.git"
BRANCH="claude/threads-affiliate-ai-system-15vu5d"
CLONE_DIR="$HOME/kamiyu"
PROJECT_DIR="$CLONE_DIR/threads-affiliate-ai"
PORT="8000"

echo "======================================================"
echo " Threads Affiliate AI セットアップを開始します"
echo "======================================================"

# --- 1. 必要パッケージ (git, docker) ---
if ! command -v git >/dev/null 2>&1; then
  echo "[1/6] git をインストール..."
  sudo apt-get update -y && sudo apt-get install -y git
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[2/6] Docker をインストール..."
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER" || true
fi

# docker compose plugin 確認
if ! docker compose version >/dev/null 2>&1; then
  echo "     docker compose plugin をインストール..."
  sudo apt-get update -y && sudo apt-get install -y docker-compose-plugin || true
fi

# --- 3. リポジトリ取得/更新 ---
if [ -d "$PROJECT_DIR/.git" ] || [ -d "$CLONE_DIR/.git" ]; then
  echo "[3/6] 既存リポジトリを更新..."
  git -C "$CLONE_DIR" fetch origin "$BRANCH"
  git -C "$CLONE_DIR" checkout "$BRANCH"
  git -C "$CLONE_DIR" pull origin "$BRANCH"
else
  echo "[3/6] リポジトリを取得..."
  git clone --branch "$BRANCH" "$REPO_URL" "$CLONE_DIR"
fi

cd "$PROJECT_DIR"

# --- 4. .env 作成 (無ければ対話入力) ---
if [ ! -f ".env" ]; then
  echo "[4/6] APIキーを入力してください (.env を作成します)"
  cp .env.example .env

  read -r -p "  楽天 アプリケーションID (RAKUTEN_APPLICATION_ID): " RAK_APP
  read -r -p "  楽天 アフィリエイトID   (RAKUTEN_AFFILIATE_ID): " RAK_AFF
  read -r -p "  ダッシュボードのユーザー名 (例 admin): " DASH_USER
  read -r -s -p "  ダッシュボードのパスワード (画面に表示されません): " DASH_PASS
  echo ""

  # 値を .env に反映 (| 区切りで特殊文字も安全に)
  sed -i "s|^RAKUTEN_APPLICATION_ID=.*|RAKUTEN_APPLICATION_ID=${RAK_APP}|" .env
  sed -i "s|^RAKUTEN_AFFILIATE_ID=.*|RAKUTEN_AFFILIATE_ID=${RAK_AFF}|" .env
  sed -i "s|^DASHBOARD_USER=.*|DASHBOARD_USER=${DASH_USER:-admin}|" .env
  sed -i "s|^DASHBOARD_PASSWORD=.*|DASHBOARD_PASSWORD=${DASH_PASS}|" .env
  echo "     .env を作成しました。(後で編集: nano $PROJECT_DIR/.env)"
else
  echo "[4/6] 既存の .env を使用します。"
fi

# --- 5. サーバー内ファイアウォールでポート開放 ---
echo "[5/6] ポート $PORT を開放 (サーバー内)..."
if command -v iptables >/dev/null 2>&1; then
  sudo iptables -I INPUT -p tcp --dport "$PORT" -j ACCEPT || true
  if command -v netfilter-persistent >/dev/null 2>&1; then
    sudo netfilter-persistent save || true
  else
    sudo apt-get install -y iptables-persistent >/dev/null 2>&1 || true
    sudo netfilter-persistent save >/dev/null 2>&1 || true
  fi
fi

# --- 6. 起動 (自動再起動つき) ---
echo "[6/6] アプリを起動 (docker compose)..."
sudo docker compose up -d --build

echo ""
echo "======================================================"
echo " 完了しました 🎉"
IP=$(curl -fsSL https://api.ipify.org 2>/dev/null || echo "サーバーのIP")
echo " ダッシュボード: http://${IP}:${PORT}"
echo ""
echo " ※ Oracle Cloud の画面側でも受信ルール(Ingress)で"
echo "    ポート ${PORT} を許可する必要があります(ORACLE_DEPLOY.md 参照)。"
echo " ※ 状態確認:  sudo docker compose logs -f"
echo " ※ 停止:      sudo docker compose down"
echo "======================================================"
