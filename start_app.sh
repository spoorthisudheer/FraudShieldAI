#!/usr/bin/env bash
# FraudShieldAI - Start Service Script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Stop existing app instance if running
pkill -f "python.*app.py" 2>/dev/null || true

echo "Starting FraudShieldAI on IBM LinuxONE (s390x)..."
nohup "$DIR/.venv/bin/python" "$DIR/app.py" > "$DIR/app.log" 2>&1 &
APP_PID=$!
sleep 2

if ps -p $APP_PID > /dev/null; then
    echo "FraudShieldAI is running! PID: $APP_PID"
    echo "Local URL : http://127.0.0.1:5000"
    echo "Logs      : $DIR/app.log"
else
    echo "Error: Failed to start FraudShieldAI. Check $DIR/app.log"
    cat "$DIR/app.log"
    exit 1
fi
