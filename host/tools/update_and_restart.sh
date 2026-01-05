#!/bin/bash

REPO_DIR="/home/zachariah/2026"
SERVICE_NAME="rover-host.service"

cd "$REPO_DIR"

git fetch origin

LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[Updater] New commit detected. Pulling..."
    git pull --rebase
    echo "[Updater] Restarting service..."
    systemctl restart "$SERVICE_NAME"
else
    echo "[Updater] No changes."
fi
