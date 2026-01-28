#!/bin/bash

REPO_DIR="/home/kali/2026"
SERVICE="rover1.service"

cd "$REPO_DIR" || exit 1

# Fetch remote info
git fetch origin main

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[AutoUpdate] Update found. Pulling..."
    git pull origin main
    echo "[AutoUpdate] Restarting $SERVICE..."
    systemctl restart $SERVICE
else
    echo "[AutoUpdate] No update available."
fi
