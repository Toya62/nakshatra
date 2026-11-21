#!/usr/bin/env bash
# Nakshatra - Background 9router Startup Helper

PORT="${ROUTER_PORT:-20128}"

# Check if already listening
if lsof -i :"$PORT" >/dev/null 2>&1; then
    echo "✅ 9router is already running on port $PORT."
    exit 0
fi

# Locate 9router binary
ROUTER_BIN=""
if command -v 9router >/dev/null 2>&1; then
    ROUTER_BIN=$(command -v 9router)
elif [ -f "$HOME/.nvm/versions/node/v22.23.1/bin/9router" ]; then
    ROUTER_BIN="$HOME/.nvm/versions/node/v22.23.1/bin/9router"
fi

if [ -z "$ROUTER_BIN" ]; then
    echo "❌ 9router binary not found. Install via npm: npm install -g 9router"
    exit 1
fi

echo "🚀 Starting 9router in background on port $PORT..."
nohup "$ROUTER_BIN" --skip-update -n -p "$PORT" >/dev/null 2>&1 &

sleep 2

if lsof -i :"$PORT" >/dev/null 2>&1; then
    echo "✅ 9router successfully started on port $PORT (PID: $!)."
    exit 0
else
    echo "❌ Failed to start 9router on port $PORT."
    exit 1
fi
