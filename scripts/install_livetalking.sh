#!/usr/bin/env bash
# ติดตั้ง LiveTalking ไว้ภายนอก repo นี้ แล้วตั้ง virtualenv แยก
# ใช้: bash scripts/install_livetalking.sh [install_dir]
set -euo pipefail

INSTALL_DIR="${1:-$HOME/apps/LiveTalking}"

if [ ! -d "$INSTALL_DIR" ]; then
  echo "[1/3] clone LiveTalking → $INSTALL_DIR"
  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone https://github.com/lipku/LiveTalking "$INSTALL_DIR"
else
  echo "[1/3] อัปเดต LiveTalking ที่มีอยู่"
  git -C "$INSTALL_DIR" pull --ff-only
fi

echo "[2/3] สร้าง venv + ติดตั้ง requirements"
cd "$INSTALL_DIR"
if [ ! -d .venv ]; then
  python3.10 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[3/3] เสร็จ — ขั้นต่อไป:"
echo "  cd $INSTALL_DIR && source .venv/bin/activate"
echo "  # เลือกตามเครื่อง"
echo "  python app.py --model wav2lip   --transport virtualcam"
echo "  python app.py --model musetalk --transport virtualcam"
echo ""
echo "  # หรือ RTMP push ให้ OBS ingest"
echo "  python app.py --model musetalk --transport rtmp \\"
echo "         --push_url rtmp://127.0.0.1/live/stream"
