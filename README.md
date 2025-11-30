# Voice Dictation

System-wide voice dictation for Linux. Speak anywhere - browser, terminal, IDE, any app.

**Features:**
- System tray daemon with hotkey toggle
- Works on **X11 and Wayland**
- Phrase-by-phrase dictation (natural pauses)
- 100% offline (no internet required)
- Fast CPU inference via faster-whisper
- Audio feedback (sounds + notifications)
- Auto-start on login

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/sasajib/voice-dictation.git
cd voice-dictation

# Install everything
./install.sh
./install-daemon.sh
```

### 2. Download Whisper Model

```bash
source venv/bin/activate
python download-models.py --model base.en
```

### 3. Start the Daemon

```bash
source venv/bin/activate
python voice-daemon.py &
```

### 4. Set Up Hotkey (KDE Plasma)

1. Open **System Settings** → **Shortcuts** → **Custom Shortcuts**
2. Right-click → **New** → **Global Shortcut** → **Command/URL**
3. Configure:
   - **Name**: Voice Dictation
   - **Trigger**: `Super+F12` (or your preference)
   - **Action**: `/path/to/voice-dictation/voice-toggle.sh`
4. Click **Apply**

### 5. Use It!

1. Press `Super+F12` - starts listening (tray icon turns green)
2. Speak naturally into your microphone
3. Pause - text types into the focused window
4. Press `Super+F12` again - stops listening

## Installation Details

### System Requirements

- **OS**: Linux (tested on Manjaro KDE, Arch, Ubuntu)
- **Python**: 3.8+
- **RAM**: 2GB+ (depends on model)
- **Microphone**: Any USB or built-in mic

### Dependencies

The install scripts handle these automatically:

```bash
# System packages (Arch/Manjaro)
sudo pacman -S portaudio ffmpeg xdotool ydotool

# System packages (Ubuntu/Debian)
sudo apt install portaudio19-dev ffmpeg xdotool

# Python packages
pip install -r requirements.txt
pip install PyQt6
```

### Manual Installation

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install Python packages
pip install -r requirements.txt
pip install PyQt6

# 3. Generate sounds and icons
python generate-assets.py

# 4. Download model
python download-models.py --model base.en
```

## Usage

### System Tray Daemon (Recommended)

The daemon runs in the background with a system tray icon.

```bash
# Start daemon
source venv/bin/activate
python voice-daemon.py &

# Toggle via command (or use hotkey)
./voice-toggle.sh

# Stop daemon
kill $(cat /tmp/voice-daemon.pid)
```

**Tray Icon:**
- **Gray mic** = Idle
- **Green mic** = Listening
- **Left-click** = Toggle listening
- **Right-click** = Menu (quit, etc.)

### Terminal Mode (Alternative)

For quick dictation without the daemon:

```bash
source venv/bin/activate

# Single dictation
python dictate.py

# Continuous mode
python dictate.py --continuous

# Copy to clipboard
python dictate.py --clipboard
```

### Auto-Start on Login

```bash
# Copy desktop entry to autostart
cp voice-dictation.desktop ~/.config/autostart/
```

## Configuration

### Whisper Models

Choose based on your needs:

| Model | Speed | Accuracy | RAM | Download |
|-------|-------|----------|-----|----------|
| `tiny.en` | Fastest | Good | ~1GB | `python download-models.py --model tiny.en` |
| `base.en` | Fast | Better | ~1.5GB | `python download-models.py --model base.en` |
| `small.en` | Medium | Great | ~2.5GB | `python download-models.py --model small.en` |
| `medium.en` | Slow | Best | ~5GB | `python download-models.py --model medium.en` |

**Change model:**
```bash
export VOICE_MODEL=small.en
python voice-daemon.py
```

### Hotkey Options

If `Super+F12` conflicts with other shortcuts, try:
- `Ctrl+Alt+V`
- `Meta+Shift+V`
- `F9`

### X11 vs Wayland

The daemon auto-detects your session type:

| Session | Text Injection | Tool |
|---------|---------------|------|
| X11 | xdotool | Works out of the box |
| Wayland | ydotool | Requires `sudo systemctl enable --now ydotool` |

Check your session: `echo $XDG_SESSION_TYPE`

## Files

```
voice-dictation/
├── voice-daemon.py        # Main daemon (system tray + RealtimeSTT)
├── voice-toggle.sh        # Toggle script for hotkey
├── start-voice-daemon.sh  # Startup script for auto-start
├── dictate.py             # Basic terminal dictation
├── download-models.py     # Model downloader
├── generate-assets.py     # Generate sounds/icons
├── install.sh             # Base installation
├── install-daemon.sh      # Daemon installation
├── requirements.txt       # Python dependencies
├── voice-dictation.desktop # Auto-start entry
├── sounds/
│   ├── start.wav          # Listening start sound
│   └── stop.wav           # Listening stop sound
└── icons/
    ├── mic-active.svg     # Tray: listening
    └── mic-idle.svg       # Tray: idle
```

## Troubleshooting

### No microphone detected
```bash
# List audio devices
arecord -l

# Test microphone
python dictate.py --test-mic
```

### Text not typing into apps
```bash
# Check session type
echo $XDG_SESSION_TYPE

# For X11 - test xdotool
xdotool type "test"

# For Wayland - ensure ydotoold is running
sudo systemctl status ydotool
sudo systemctl enable --now ydotool
```

### Daemon won't start
```bash
# Check logs
cat /tmp/voice-daemon.log

# Kill stale process
rm /tmp/voice-daemon.pid
```

### Poor accuracy
```bash
# Use better model
export VOICE_MODEL=small.en
python voice-daemon.py
```

## How It Works

1. **RealtimeSTT** captures microphone audio continuously
2. **WebRTC VAD** detects speech start/end (fast, rough)
3. **Silero VAD** confirms speech segments (accurate)
4. **faster-whisper** transcribes confirmed speech chunks
5. **xdotool/ydotool** types text into the focused window

Latency: 0.5-2 seconds depending on model and phrase length.

## Credits

Built with:
- [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT) - Real-time speech-to-text
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Fast Whisper inference
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model

## License

MIT License - See LICENSE file
