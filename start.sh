#!/bin/bash
# Start Postiz Lite in background with log capture, then Hermes gateway.
set -e

# Start Postiz Lite
echo "[postiz-lite] Starting on port 5000..."
python /opt/hermes/postiz-lite/main.py > /data/postiz-lite.log 2>&1 &
POSTIZ_PID=$!
echo "[postiz-lite] PID $POSTIZ_PID"

# Give Postiz Lite a moment to start
sleep 2

# Check if Postiz Lite started successfully
if ! kill -0 $POSTIZ_PID 2>/dev/null; then
    echo "[postiz-lite] FAILED to start. Logs:"
    cat /data/postiz-lite.log || true
    exit 1
fi

echo "[postiz-lite] Running. Logs: /data/postiz-lite.log"

# Start Hermes gateway in foreground (this is the main process)
echo "[hermes] Starting gateway..."
exec hermes gateway
