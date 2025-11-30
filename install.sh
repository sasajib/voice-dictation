#!/bin/bash
# Installation script for voice dictation system
# Manjaro Linux (KDE)

set -e  # Exit on error

echo "🎤 Voice Dictation Setup for Claude Code"
echo "=========================================="
echo ""

# Check if running on Manjaro/Arch
if ! command -v pacman &> /dev/null; then
    echo "⚠️  Warning: This script is designed for Manjaro/Arch Linux"
    echo "   You may need to adapt package manager commands for your distro"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Install system dependencies
echo "📦 Step 1: Installing system dependencies..."
echo "   - portaudio (for PyAudio)"
echo "   - ffmpeg (for audio processing)"
echo "   - xdotool (for keyboard automation)"
echo ""

sudo pacman -S --needed portaudio ffmpeg xdotool

# Step 2: Check Python version
echo ""
echo "🐍 Step 2: Checking Python version..."
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "   Found Python $PYTHON_VERSION"

# Check if Python >= 3.8
REQUIRED_VERSION="3.8"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "   ❌ Error: Python 3.8 or higher is required"
    exit 1
fi
echo "   ✓ Python version is compatible"

# Step 3: Create virtual environment (optional but recommended)
echo ""
echo "🔧 Step 3: Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   Virtual environment already exists"
else
    python3 -m venv venv
    echo "   ✓ Virtual environment created"
fi

# Step 4: Activate virtual environment and install Python packages
echo ""
echo "📚 Step 4: Installing Python packages..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Test microphone: python dictate.py --test-mic"
echo "3. Test transcription: python dictate.py"
echo "4. See README.md for usage instructions"
echo ""
