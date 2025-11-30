#!/bin/bash
# Toggle Voice Dictation Daemon
# Use this script with KDE Global Shortcuts (Super+F12)

PID_FILE="/tmp/voice-daemon.pid"
TOGGLE_FILE="/tmp/voice-daemon-toggle"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if daemon is running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")

    # Verify process is actually running
    if kill -0 "$PID" 2>/dev/null; then
        # Send toggle signal
        kill -USR1 "$PID"
        exit 0
    fi
fi

# Daemon not running - try toggle file method (in case of permission issues)
if [ -f "$PID_FILE" ]; then
    touch "$TOGGLE_FILE"
    exit 0
fi

# Daemon not running - start it
echo "Daemon not running. Starting..."
notify-send "Voice Dictation" "Starting daemon..." 2>/dev/null || true

# Activate venv and start daemon
cd "$SCRIPT_DIR"
source venv/bin/activate
nohup python3 voice-daemon.py > /tmp/voice-daemon.log 2>&1 &

# Wait a moment for startup
sleep 2

# Check if started successfully
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        notify-send "Voice Dictation" "Daemon started! Press Super+F12 again to toggle." 2>/dev/null || true
        exit 0
    fi
fi

# Failed to start
notify-send "Voice Dictation" "Failed to start daemon. Check /tmp/voice-daemon.log" 2>/dev/null || true
exit 1
