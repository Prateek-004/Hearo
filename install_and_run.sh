#!/usr/bin/env bash
echo ""
echo " ============================================"
echo "  Hearo v1.0 — Smart Offline Music Player"
echo " ============================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo " [ERROR] python3 not found. Please install Python 3.8+"
    exit 1
fi

echo " [1/2] Installing dependencies..."
python3 -m pip install -r requirements.txt --quiet

echo " [2/2] Launching Hearo..."
echo ""
python3 hearo.py
