#!/bin/bash
# Install Voice Dictation Daemon
# Sets up dependencies, auto-start, and provides hotkey instructions

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DESKTOP_FILE="$SCRIPT_DIR/voice-dictation.desktop"
AUTOSTART_DIR="$HOME/.config/autostart"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Voice Dictation Daemon Installer${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running from correct directory
if [ ! -f "$SCRIPT_DIR/voice-daemon.py" ]; then
    echo -e "${RED}ERROR: voice-daemon.py not found!${NC}"
    echo "Please run this script from the voice dictation directory."
    exit 1
fi

# Step 1: Install system dependencies
echo -e "${YELLOW}Step 1: Installing system dependencies...${NC}"
echo ""

# Check package manager
if command -v pacman &> /dev/null; then
    echo "Detected Arch-based system (pacman)"

    # Install ydotool for text injection (works on X11 and Wayland)
    if ! command -v ydotool &> /dev/null; then
        echo "Installing ydotool..."
        sudo pacman -S --noconfirm ydotool
    else
        echo "ydotool already installed"
    fi

    # Ensure xdotool is installed as fallback
    if ! command -v xdotool &> /dev/null; then
        echo "Installing xdotool (fallback)..."
        sudo pacman -S --noconfirm xdotool
    else
        echo "xdotool already installed"
    fi

elif command -v apt &> /dev/null; then
    echo "Detected Debian-based system (apt)"
    sudo apt update
    sudo apt install -y ydotool xdotool
else
    echo -e "${YELLOW}Unknown package manager. Please install manually:${NC}"
    echo "  - ydotool (for Wayland support)"
    echo "  - xdotool (for X11)"
fi

echo ""

# Step 2: Enable ydotool service
echo -e "${YELLOW}Step 2: Enabling ydotool service...${NC}"

if systemctl is-active --quiet ydotool 2>/dev/null; then
    echo "ydotool service already running"
else
    echo "Starting and enabling ydotool service..."
    sudo systemctl enable ydotool 2>/dev/null || true
    sudo systemctl start ydotool 2>/dev/null || true

    # Check if it started
    if systemctl is-active --quiet ydotool 2>/dev/null; then
        echo -e "${GREEN}ydotool service started successfully${NC}"
    else
        echo -e "${YELLOW}Note: ydotool service may need manual setup${NC}"
        echo "  Try: sudo systemctl enable --now ydotool"
        echo "  Or run ydotoold manually: sudo ydotoold &"
    fi
fi

echo ""

# Step 3: Install Python dependencies
echo -e "${YELLOW}Step 3: Installing Python dependencies...${NC}"

cd "$SCRIPT_DIR"

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Install PyQt6
if ! python3 -c "import PyQt6" 2>/dev/null; then
    echo "Installing PyQt6..."
    pip install PyQt6
else
    echo "PyQt6 already installed"
fi

echo ""

# Step 4: Generate assets if needed
echo -e "${YELLOW}Step 4: Generating assets...${NC}"

if [ ! -f "$SCRIPT_DIR/sounds/start.wav" ] || [ ! -f "$SCRIPT_DIR/icons/mic-idle.svg" ]; then
    python3 generate-assets.py
else
    echo "Assets already generated"
fi

echo ""

# Step 5: Make scripts executable
echo -e "${YELLOW}Step 5: Setting permissions...${NC}"

chmod +x "$SCRIPT_DIR/voice-daemon.py"
chmod +x "$SCRIPT_DIR/voice-toggle.sh"
chmod +x "$SCRIPT_DIR/start-voice-daemon.sh"
chmod +x "$SCRIPT_DIR/generate-assets.py"

echo "Scripts made executable"
echo ""

# Step 6: Setup auto-start
echo -e "${YELLOW}Step 6: Setting up auto-start...${NC}"

mkdir -p "$AUTOSTART_DIR"

if [ -f "$AUTOSTART_DIR/voice-dictation.desktop" ]; then
    echo "Auto-start entry already exists"
else
    cp "$DESKTOP_FILE" "$AUTOSTART_DIR/"
    echo -e "${GREEN}Auto-start entry created${NC}"
fi

echo ""

# Step 7: Test daemon
echo -e "${YELLOW}Step 7: Testing daemon...${NC}"

# Kill any existing daemon
if [ -f /tmp/voice-daemon.pid ]; then
    OLD_PID=$(cat /tmp/voice-daemon.pid)
    kill "$OLD_PID" 2>/dev/null || true
    rm -f /tmp/voice-daemon.pid
fi

echo "Starting daemon for test..."
cd "$SCRIPT_DIR"
source venv/bin/activate
python3 voice-daemon.py &
DAEMON_PID=$!

sleep 3

if kill -0 $DAEMON_PID 2>/dev/null; then
    echo -e "${GREEN}Daemon started successfully! (PID: $DAEMON_PID)${NC}"
    echo ""
    echo "You should see a microphone icon in your system tray."
    echo ""
else
    echo -e "${RED}Daemon failed to start. Check /tmp/voice-daemon.log${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo ""
echo "1. ${YELLOW}Set up the global hotkey (Super+F12):${NC}"
echo ""
echo "   For KDE Plasma:"
echo "   - Open System Settings"
echo "   - Go to: Shortcuts → Custom Shortcuts"
echo "   - Click: Edit → New → Global Shortcut → Command/URL"
echo "   - Name: Voice Dictation Toggle"
echo "   - Trigger: Press Super+F12"
echo "   - Action: $SCRIPT_DIR/voice-toggle.sh"
echo "   - Click Apply"
echo ""
echo "2. ${YELLOW}Usage:${NC}"
echo "   - Press Super+F12 to toggle listening"
echo "   - Speak naturally, text will type into focused window"
echo "   - Press Super+F12 again to stop"
echo ""
echo "3. ${YELLOW}Manual controls:${NC}"
echo "   - Left-click tray icon to toggle"
echo "   - Right-click tray icon for menu"
echo "   - Stop daemon: kill \$(cat /tmp/voice-daemon.pid)"
echo ""
echo "4. ${YELLOW}Logs:${NC}"
echo "   - /tmp/voice-daemon.log"
echo ""
echo -e "${GREEN}Enjoy voice dictation anywhere!${NC}"
