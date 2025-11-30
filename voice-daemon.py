#!/usr/bin/env python3
"""
Voice Dictation Daemon with System Tray
- System tray icon (PyQt6)
- RealtimeSTT for speech-to-text
- ydotool/xdotool for typing into any app
- Works on both X11 and Wayland
"""

import sys
import os
import signal
import subprocess
import threading
import time
from pathlib import Path

# Add script directory to path for imports
SCRIPT_DIR = Path(__file__).parent.absolute()
os.chdir(SCRIPT_DIR)

# Check for PyQt6
try:
    from PyQt6.QtWidgets import (
        QApplication, QSystemTrayIcon, QMenu, QMessageBox
    )
    from PyQt6.QtGui import QIcon, QAction
    from PyQt6.QtCore import QTimer, pyqtSignal, QObject
except ImportError:
    print("ERROR: PyQt6 not found. Install with: pip install PyQt6")
    sys.exit(1)

# Check for RealtimeSTT
try:
    from RealtimeSTT import AudioToTextRecorder
except ImportError:
    print("ERROR: RealtimeSTT not found. Run: ./install.sh")
    sys.exit(1)


class VoiceSignals(QObject):
    """Qt signals for thread-safe GUI updates"""
    text_ready = pyqtSignal(str)
    status_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)


class VoiceDaemon:
    """Main voice dictation daemon"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # State
        self.is_listening = False
        self.recorder = None
        self.listen_thread = None
        self.shutdown_flag = False
        self.last_typed_text = ""  # Track what we've already typed (for word-by-word)

        # Configuration
        self.model = os.environ.get('VOICE_MODEL', 'small.en')
        self.language = os.environ.get('VOICE_LANGUAGE', 'en')
        self.word_by_word = os.environ.get('VOICE_WORD_BY_WORD', 'true').lower() == 'true'

        # Paths
        self.icon_active = SCRIPT_DIR / 'icons' / 'mic-active.svg'
        self.icon_idle = SCRIPT_DIR / 'icons' / 'mic-idle.svg'
        self.sound_start = SCRIPT_DIR / 'sounds' / 'start.wav'
        self.sound_stop = SCRIPT_DIR / 'sounds' / 'stop.wav'
        self.toggle_file = Path('/tmp/voice-daemon-toggle')
        self.pid_file = Path('/tmp/voice-daemon.pid')

        # Signals for thread-safe updates
        self.signals = VoiceSignals()
        self.signals.text_ready.connect(self.on_text_ready)
        self.signals.status_changed.connect(self.on_status_changed)
        self.signals.error_occurred.connect(self.on_error)

        # Detect text injection method
        self.text_injector = self._detect_text_injector()

        # Setup tray
        self._setup_tray()

        # Setup toggle file watcher
        self._setup_toggle_watcher()

        # Write PID file
        self._write_pid()

        # Handle signals
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGUSR1, self._toggle_signal_handler)

        print(f"Voice Daemon started")
        print(f"  Model: {self.model}")
        print(f"  Mode: {'word-by-word' if self.word_by_word else 'phrase-by-phrase'}")
        print(f"  Text injector: {self.text_injector}")
        print(f"  PID: {os.getpid()}")
        print(f"  Toggle: kill -USR1 {os.getpid()} or touch {self.toggle_file}")

    def _detect_text_injector(self):
        """Detect available text injection method based on session type"""
        # Detect session type
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        print(f"  Session type: {session_type}")

        # On X11, prefer xdotool (simple, no daemon needed)
        if session_type == 'x11':
            if self._command_exists('xdotool'):
                return 'xdotool'

        # On Wayland, try ydotool first (needs ydotoold daemon)
        if session_type == 'wayland':
            if self._command_exists('ydotool'):
                # Check if ydotoold is running
                try:
                    result = subprocess.run(
                        ['pgrep', '-x', 'ydotoold'],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        return 'ydotool'
                except:
                    pass
                print("  Note: ydotool found but ydotoold not running")
                print("  Start with: sudo ydotoold &")

            # Fallback to wtype for Wayland
            if self._command_exists('wtype'):
                return 'wtype'

        # Generic fallback - try xdotool (works if X11 compatibility exists)
        if self._command_exists('xdotool'):
            return 'xdotool'

        # Last resort - try ydotool
        if self._command_exists('ydotool'):
            return 'ydotool'

        print("WARNING: No text injection tool found!")
        print("  For X11: sudo pacman -S xdotool")
        print("  For Wayland: sudo pacman -S ydotool && sudo ydotoold &")
        return None

    def _command_exists(self, cmd):
        """Check if command exists"""
        return subprocess.run(
            ['which', cmd], capture_output=True
        ).returncode == 0

    def _setup_tray(self):
        """Setup system tray icon"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("ERROR: System tray not available")
            sys.exit(1)

        self.tray = QSystemTrayIcon(self.app)
        self._update_tray_icon()

        # Create menu
        menu = QMenu()

        self.toggle_action = QAction("Start Listening", self.app)
        self.toggle_action.triggered.connect(self.toggle_listening)
        menu.addAction(self.toggle_action)

        menu.addSeparator()

        status_action = QAction(f"Model: {self.model}", self.app)
        status_action.setEnabled(False)
        menu.addAction(status_action)

        menu.addSeparator()

        quit_action = QAction("Quit", self.app)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.setToolTip("Voice Dictation - Idle")
        self.tray.show()

    def _update_tray_icon(self):
        """Update tray icon based on state"""
        if self.is_listening:
            icon_path = self.icon_active
        else:
            icon_path = self.icon_idle

        if icon_path.exists():
            self.tray.setIcon(QIcon(str(icon_path)))
        else:
            # Fallback to theme icons
            if self.is_listening:
                self.tray.setIcon(QIcon.fromTheme('audio-input-microphone'))
            else:
                self.tray.setIcon(QIcon.fromTheme('audio-input-microphone-muted'))

    def _on_tray_activated(self, reason):
        """Handle tray icon click"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # Left click
            self.toggle_listening()

    def _setup_toggle_watcher(self):
        """Setup file watcher for toggle"""
        # Clean up old toggle file
        if self.toggle_file.exists():
            self.toggle_file.unlink()

        # Timer to check for toggle file
        self.toggle_timer = QTimer()
        self.toggle_timer.timeout.connect(self._check_toggle_file)
        self.toggle_timer.start(200)  # Check every 200ms

    def _check_toggle_file(self):
        """Check if toggle file was created"""
        if self.toggle_file.exists():
            self.toggle_file.unlink()
            self.toggle_listening()

    def _write_pid(self):
        """Write PID to file"""
        self.pid_file.write_text(str(os.getpid()))

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\nShutting down...")
        self.quit()

    def _toggle_signal_handler(self, signum, frame):
        """Handle toggle signal (SIGUSR1)"""
        # Use Qt timer to run in main thread
        QTimer.singleShot(0, self.toggle_listening)

    def toggle_listening(self):
        """Toggle listening state"""
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self):
        """Start listening for speech"""
        if self.is_listening:
            return

        self.is_listening = True
        self.shutdown_flag = False
        self._update_tray_icon()
        self.toggle_action.setText("Stop Listening")
        self.tray.setToolTip("Voice Dictation - LISTENING")

        # Play start sound
        self._play_sound(self.sound_start)

        # Show notification
        self._notify("Voice Dictation", "Listening... Speak now!")

        # Start listener thread
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()

        print("Started listening")

    def stop_listening(self):
        """Stop listening"""
        if not self.is_listening:
            return

        self.is_listening = False
        self.shutdown_flag = True
        self._update_tray_icon()
        self.toggle_action.setText("Start Listening")
        self.tray.setToolTip("Voice Dictation - Idle")

        # Play stop sound
        self._play_sound(self.sound_stop)

        # Show notification
        self._notify("Voice Dictation", "Stopped listening")

        # Shutdown recorder
        if self.recorder:
            try:
                self.recorder.abort()
                self.recorder.shutdown()
            except:
                pass
            self.recorder = None

        print("Stopped listening")

    def _on_realtime_update(self, text):
        """Callback for realtime transcription updates (word-by-word)"""
        if self.shutdown_flag or not self.is_listening:
            return

        # Type only the new words that weren't already typed
        if text.startswith(self.last_typed_text):
            new_text = text[len(self.last_typed_text):].lstrip()
            if new_text:
                self.signals.text_ready.emit(new_text)
                self.last_typed_text = text

    def _listen_loop(self):
        """Main listening loop (runs in thread)"""
        try:
            # Reset typed text tracker
            self.last_typed_text = ""

            # Initialize recorder
            if self.word_by_word:
                # Word-by-word mode: use realtime callback
                self.recorder = AudioToTextRecorder(
                    model=self.model,
                    language=self.language,
                    enable_realtime_transcription=True,
                    on_realtime_transcription_update=self._on_realtime_update,
                    silero_sensitivity=0.5,
                    webrtc_sensitivity=3,
                    post_speech_silence_duration=0.3,  # Shorter for faster word detection
                    min_length_of_recording=0.3,
                    min_gap_between_recordings=0,
                    spinner=False,
                )
            else:
                # Phrase-by-phrase mode: use blocking text()
                self.recorder = AudioToTextRecorder(
                    model=self.model,
                    language=self.language,
                    enable_realtime_transcription=True,
                    silero_sensitivity=0.5,
                    webrtc_sensitivity=3,
                    post_speech_silence_duration=0.6,  # Longer pause for phrase detection
                    min_length_of_recording=0.5,
                    min_gap_between_recordings=0.1,
                    spinner=False,
                )

            print(f"Recorder initialized, listening... (mode: {'word-by-word' if self.word_by_word else 'phrase-by-phrase'})")

            if self.word_by_word:
                # Word-by-word: keep recorder alive and let callback handle typing
                while self.is_listening and not self.shutdown_flag:
                    # Just keep the loop alive, callback does the work
                    text = self.recorder.text()  # This blocks until speech ends
                    # Reset for next phrase
                    self.last_typed_text = ""
            else:
                # Phrase-by-phrase: wait for complete phrases
                while self.is_listening and not self.shutdown_flag:
                    try:
                        text = self.recorder.text()

                        if self.shutdown_flag:
                            break

                        if text and text.strip():
                            self.signals.text_ready.emit(text.strip())

                    except Exception as e:
                        if not self.shutdown_flag:
                            self.signals.error_occurred.emit(str(e))
                        break

        except Exception as e:
            self.signals.error_occurred.emit(f"Recorder init failed: {e}")

        finally:
            if self.recorder:
                try:
                    self.recorder.shutdown()
                except:
                    pass
                self.recorder = None

            # Update state in main thread
            if self.is_listening:
                self.signals.status_changed.emit(False)

    def on_text_ready(self, text):
        """Handle transcribed text (main thread)"""
        print(f"Transcribed: {text}")
        self._type_text(text)

    def on_status_changed(self, is_listening):
        """Handle status change from thread"""
        if not is_listening and self.is_listening:
            self.stop_listening()

    def on_error(self, error):
        """Handle error from thread"""
        print(f"Error: {error}")
        self._notify("Voice Dictation Error", error)
        if self.is_listening:
            self.stop_listening()

    def _type_text(self, text):
        """Type text into focused window"""
        if not text or not self.text_injector:
            return

        try:
            if self.text_injector == 'ydotool':
                # ydotool works on both X11 and Wayland
                subprocess.run(['ydotool', 'type', '--', text], check=True)

            elif self.text_injector == 'xdotool':
                # xdotool for X11
                subprocess.run(['xdotool', 'type', '--', text], check=True)

            elif self.text_injector == 'wtype':
                # wtype for Wayland
                subprocess.run(['wtype', text], check=True)

            print(f"Typed: {text}")

        except subprocess.CalledProcessError as e:
            print(f"Failed to type text: {e}")
        except Exception as e:
            print(f"Type error: {e}")

    def _play_sound(self, sound_file):
        """Play sound file"""
        if not sound_file.exists():
            return

        try:
            # Try paplay (PulseAudio) first
            if self._command_exists('paplay'):
                subprocess.Popen(
                    ['paplay', str(sound_file)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            # Fallback to aplay
            elif self._command_exists('aplay'):
                subprocess.Popen(
                    ['aplay', '-q', str(sound_file)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except:
            pass

    def _notify(self, title, message):
        """Show desktop notification"""
        try:
            if self._command_exists('notify-send'):
                subprocess.Popen(
                    ['notify-send', '-a', 'Voice Dictation', title, message],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except:
            pass

        # Also show tray message
        try:
            self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 2000)
        except:
            pass

    def quit(self):
        """Quit the daemon"""
        self.shutdown_flag = True
        self.stop_listening()

        # Cleanup
        if self.pid_file.exists():
            self.pid_file.unlink()
        if self.toggle_file.exists():
            self.toggle_file.unlink()

        self.tray.hide()
        self.app.quit()

    def run(self):
        """Run the daemon"""
        return self.app.exec()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Voice Dictation Daemon')
    parser.add_argument('--model', default=None, help='Whisper model (tiny.en, base.en, small.en)')
    args = parser.parse_args()

    if args.model:
        os.environ['VOICE_MODEL'] = args.model

    # Check if already running
    pid_file = Path('/tmp/voice-daemon.pid')
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            # Check if process is running
            os.kill(pid, 0)
            print(f"Daemon already running (PID: {pid})")
            print(f"To toggle: kill -USR1 {pid}")
            print(f"To stop: kill {pid}")
            sys.exit(1)
        except (ProcessLookupError, ValueError):
            # Process not running, clean up stale PID file
            pid_file.unlink()

    daemon = VoiceDaemon()
    sys.exit(daemon.run())


if __name__ == '__main__':
    main()
