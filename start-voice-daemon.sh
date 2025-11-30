#!/bin/bash
# Start Voice Dictation Daemon
# This script is used by the .desktop autostart entry

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="/tmp/voice-daemon.log"

cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Start daemon
exec python3 voice-daemon.py >> "$LOG_FILE" 2>&1
