#!/bin/bash
# Claude Code Voice Integration
# Optimized for use within Claude Code terminal sessions

set -e

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PATH="$SCRIPT_DIR/venv"
DICTATE_SCRIPT="$SCRIPT_DIR/dictate.py"
MODEL="${VOICE_MODEL:-base.en}"

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check dependencies
check_deps() {
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${RED}❌ Virtual environment not found!${NC}"
        echo "   Please run: cd $SCRIPT_DIR && ./install.sh"
        exit 1
    fi

    if [ ! -f "$DICTATE_SCRIPT" ]; then
        echo -e "${RED}❌ Dictation script not found: $DICTATE_SCRIPT${NC}"
        exit 1
    fi
}

# Interactive mode - for direct use in Claude Code terminal
interactive_mode() {
    echo -e "${BLUE}🎤 Claude Code Voice Dictation${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Mode: Interactive"
    echo "Model: $MODEL"
    echo ""
    echo -e "${GREEN}Options:${NC}"
    echo "  1) Single dictation (print result)"
    echo "  2) Copy to clipboard"
    echo "  3) Continuous mode (Ctrl+C to stop)"
    echo "  4) Test microphone"
    echo "  q) Quit"
    echo ""
    read -p "Select option [1-4, q]: " -n 1 -r
    echo ""

    source "$VENV_PATH/bin/activate"

    case $REPLY in
        1)
            echo -e "\n${BLUE}🎤 Listening... Speak now${NC}"
            python3 "$DICTATE_SCRIPT" --model "$MODEL"
            ;;
        2)
            echo -e "\n${BLUE}🎤 Listening... (will copy to clipboard)${NC}"
            python3 "$DICTATE_SCRIPT" --model "$MODEL" --clipboard
            echo -e "${GREEN}✓ Text copied! Paste with Ctrl+V${NC}"
            ;;
        3)
            echo -e "\n${BLUE}🎤 Continuous listening mode${NC}"
            python3 "$DICTATE_SCRIPT" --model "$MODEL" --continuous
            ;;
        4)
            python3 "$DICTATE_SCRIPT" --test-mic
            ;;
        q|Q)
            echo "Bye!"
            exit 0
            ;;
        *)
            echo "Invalid option"
            exit 1
            ;;
    esac
}

# Command mode - run specific command
command_mode() {
    local mode="$1"

    source "$VENV_PATH/bin/activate"

    case "$mode" in
        once|single)
            python3 "$DICTATE_SCRIPT" --model "$MODEL"
            ;;
        clipboard|clip)
            python3 "$DICTATE_SCRIPT" --model "$MODEL" --clipboard
            ;;
        continuous|cont)
            python3 "$DICTATE_SCRIPT" --model "$MODEL" --continuous
            ;;
        test)
            python3 "$DICTATE_SCRIPT" --test-mic
            ;;
        *)
            echo "Unknown mode: $mode"
            show_help
            exit 1
            ;;
    esac
}

# Show help
show_help() {
    cat << EOF
${BLUE}Claude Code Voice Dictation${NC}

${GREEN}Usage:${NC}
  $0                      # Interactive mode (menu)
  $0 [MODE]              # Command mode

${GREEN}Modes:${NC}
  once, single           # Single dictation (print to stdout)
  clipboard, clip        # Copy transcription to clipboard
  continuous, cont       # Continuous listening (Ctrl+C to stop)
  test                   # Test microphone

${GREEN}Examples:${NC}
  # Interactive menu
  $0

  # Quick dictation
  $0 once

  # Dictate and copy to clipboard
  $0 clipboard

  # Continuous listening
  $0 continuous

${GREEN}In Claude Code:${NC}
  # Create alias for quick access
  alias voice='$SCRIPT_DIR/claude-code-voice.sh'

  # Then use:
  voice              # Interactive mode
  voice once         # Quick dictation
  voice clip         # Copy to clipboard

${GREEN}Environment Variables:${NC}
  VOICE_MODEL          # Whisper model (tiny.en, base.en, small.en, medium.en)
                       # Default: base.en

EOF
}

# Main
check_deps

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

if [ -z "$1" ]; then
    interactive_mode
else
    command_mode "$1"
fi
