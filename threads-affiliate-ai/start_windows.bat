@echo off
REM Windows用ワンクリック起動。ダブルクリックするだけ。
REM 初回は自動でPython環境を用意します。
cd /d "%~dp0"

echo === Threads Affiliate AI を起動します ===

where python >nul 2>nul
if errorlevel 1 (
  echo Python が見つかりません。https://www.python.org/downloads/ からインストールしてください。
  echo インストール時に "Add Python to PATH" に必ずチェックを入れてください。
  pause
  exit /b 1
)

if not exist ".venv" (
  echo 初回セットアップ中（数分かかります）...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt

if not exist ".env" (
  copy .env.example .env >nul
  echo .env を作りました。楽天のキーを .env に入れてから使うと本番接続になります。
)

start "" http://localhost:8000
echo ダッシュボード: http://localhost:8000  （このウィンドウを閉じると停止します）
python -m app.main
pause
