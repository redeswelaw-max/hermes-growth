#!/bin/bash
# Start Postiz Lite in background, then Hermes gateway in foreground.
set -e

echo "[start] PATH=$PATH"
echo "[start] which python: $(which python || echo 'NOT FOUND')"
echo "[start] python version: $(python --version 2>&1 || echo 'NO PYTHON')"

# Start Postiz Lite (logs go to stdout so Railway captures them)
echo "[postiz-lite] Starting on port 5000..."
python /opt/hermes/postiz-lite/main.py &
POSTIZ_PID=$!
echo "[postiz-lite] PID $POSTIZ_PID"

# Give Postiz Lite a moment to start
sleep 3

# Check if Postiz Lite started successfully
if ! kill -0 $POSTIZ_PID 2>/dev/null; then
    echo "[postiz-lite] FAILED to start."
    exit 1
fi

echo "[postiz-lite] Running on localhost:5000"

# Start Hermes gateway in foreground (this is the main process)
echo "[hermes] Starting gateway..."
exec hermes gateway
