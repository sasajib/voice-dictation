#!/bin/bash
# Terminal Integration for Voice Dictation
# Activates voice dictation and types the result into the terminal

set -e

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PATH="$SCRIPT_DIR/venv"
DICTATE_SCRIPT="$SCRIPT_DIR/dictate.py"
MODEL="${VOICE_MODEL:-base.en}"  # Can be overridden with env var

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run: cd $SCRIPT_DIR && ./install.sh"
    exit 1
fi

# Check if dictate script exists
if [ ! -f "$DICTATE_SCRIPT" ]; then
    echo "❌ Dictation script not found: $DICTATE_SCRIPT"
    exit 1
fi

# Function to show notification (if notify-send is available)
notify() {
    if command -v notify-send &> /dev/null; then
        notify-send "🎤 Voice Dictation" "$1"
    fi
}

# Function to type text into focused window
type_text() {
    local text="$1"

    if [ -z "$text" ]; then
        echo "No text to type"
        return 1
    fi

    # Check if xdotool is available
    if command -v xdotool &> /dev/null; then
        # Type the text into the currently focused window
        xdotool type "$text"
        echo "✓ Typed into window: $text"
    else
        # Fallback: just print (user can copy-paste)
        echo "⚠️  xdotool not found, printing instead:"
        echo "$text"
    fi
}

# Main function
main() {
    # Show notification that we're listening
    notify "Listening... Speak now"

    # Activate virtual environment and run dictation
    source "$VENV_PATH/bin/activate"

    # Run dictation and capture output
    # We use --no-realtime for more accurate final transcription
    TEXT=$(python3 "$DICTATE_SCRIPT" --model "$MODEL" 2>&1 | grep "📝 Transcribed:" | sed 's/📝 Transcribed: //')

    if [ -n "$TEXT" ]; then
        # Type or print the text
        type_text "$TEXT"
        notify "✓ Transcribed: $TEXT"
    else
        echo "⚠️  No speech detected or transcription failed"
        notify "No speech detected"
        exit 1
    fi
}

# Show usage if --help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    cat << EOF
Voice Terminal - Type via voice dictation

Usage:
  $0                    # Run voice dictation and type result
  $0 --help            # Show this help

Environment Variables:
  VOICE_MODEL          # Whisper model (tiny.en, base.en, small.en, medium.en)
                       # Default: base.en

Examples:
  # Basic usage
  $0

  # Use faster (less accurate) model
  VOICE_MODEL=tiny.en $0

  # Use more accurate (slower) model
  VOICE_MODEL=small.en $0

Keyboard Shortcut:
  1. Open KDE System Settings
  2. Go to Shortcuts → Custom Shortcuts
  3. Click "Edit" → "New" → "Global Shortcut" → "Command/URL"
  4. Name: "Voice Dictation"
  5. Trigger: Set to Ctrl+Alt+V (or your preference)
  6. Action: Command/URL: $SCRIPT_DIR/voice-terminal.sh

EOF
    exit 0
fi

# Run main function
main "$@"
