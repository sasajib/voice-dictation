#!/usr/bin/env python3
"""
Voice Dictation for Terminal/Claude Code
Uses RealtimeSTT with faster-whisper backend for real-time speech-to-text
FIXED: Proper Ctrl+C handling and signal management
"""

import sys
import signal
import argparse
from pathlib import Path

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global shutdown_requested
    print("\n\n⏹️  Stopping... (press Ctrl+C again to force quit)")
    shutdown_requested = True
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

try:
    from RealtimeSTT import AudioToTextRecorder
    import pyperclip
except ImportError as e:
    print(f"❌ Error: Missing dependency: {e}")
    print("\n💡 Please run: ./install.sh")
    print("   Or manually: pip install -r requirements.txt")
    sys.exit(1)


class VoiceDictation:
    """Real-time voice dictation using RealtimeSTT"""

    def __init__(self, model="base.en", language="en", enable_realtime=True):
        """
        Initialize voice dictation

        Args:
            model: Whisper model size (tiny.en, base.en, small.en, medium.en)
            language: Language code (en, es, fr, etc.)
            enable_realtime: Enable real-time transcription (faster feedback)
        """
        self.model = model
        self.language = language
        self.recorder = None

        print(f"🔧 Initializing voice dictation...")
        print(f"   Model: {model}")
        print(f"   Language: {language}")
        print(f"   Real-time: {enable_realtime}")
        print(f"   Press Ctrl+C to stop anytime")

        try:
            self.recorder = AudioToTextRecorder(
                model=model,
                language=language,
                enable_realtime_transcription=enable_realtime,
                silero_sensitivity=0.5,
                webrtc_sensitivity=3,
                post_speech_silence_duration=0.4,
                min_length_of_recording=0.5,
                min_gap_between_recordings=0.1,
                spinner=False,  # Disable spinner for better Ctrl+C handling
            )
            print("✓ Voice dictation ready!")
        except Exception as e:
            print(f"❌ Error initializing recorder: {e}")
            print("\n💡 Common issues:")
            print("   - No microphone detected")
            print("   - Permission denied (check audio settings)")
            print("   - Missing system dependencies (run install.sh)")
            sys.exit(1)

    def __del__(self):
        """Cleanup when object is destroyed"""
        if self.recorder:
            try:
                self.recorder.shutdown()
            except:
                pass

    def listen_once(self, output_mode="print"):
        """
        Listen for speech and return transcribed text

        Args:
            output_mode: How to output text (print, clipboard, return)

        Returns:
            Transcribed text string
        """
        global shutdown_requested

        if shutdown_requested:
            return ""

        print("\n🎤 Listening... (speak now, Ctrl+C to stop)")

        try:
            # This blocks until speech is detected and ends
            text = self.recorder.text()

            if shutdown_requested:
                return ""

            if not text or not text.strip():
                print("⚠️  No speech detected")
                return ""

            # Handle output based on mode
            if output_mode == "print":
                print(f"\n📝 Transcribed: {text}")
            elif output_mode == "clipboard":
                pyperclip.copy(text)
                print(f"\n📋 Copied to clipboard: {text}")

            return text

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopped by user")
            return ""
        except Exception as e:
            if not shutdown_requested:
                print(f"\n❌ Error during transcription: {e}")
            return ""

    def listen_continuous(self, output_mode="print"):
        """
        Continuously listen and transcribe until Ctrl+C

        Args:
            output_mode: How to output text (print, clipboard)
        """
        global shutdown_requested

        print("\n🎤 Continuous listening mode")
        print("   Press Ctrl+C to stop")
        print("   Speak naturally, pause to finish each phrase")
        print("")

        try:
            while not shutdown_requested:
                text = self.listen_once(output_mode)
                if text and not shutdown_requested:
                    print("")  # Empty line for readability

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopped continuous mode")
        finally:
            if self.recorder:
                try:
                    self.recorder.shutdown()
                except:
                    pass

    def test_microphone(self):
        """Test if microphone is working"""
        print("\n🎤 Testing microphone...")
        print("   Speak for a few seconds... (Ctrl+C to cancel)")

        try:
            text = self.recorder.text()
            if text:
                print(f"\n✓ Microphone working! Heard: '{text}'")
                return True
            else:
                print("\n⚠️  No audio detected. Check:")
                print("   1. Microphone is connected and enabled")
                print("   2. Correct audio input device selected")
                print("   3. Microphone permissions granted")
                return False
        except KeyboardInterrupt:
            print("\n\n⏹️  Test cancelled")
            return False
        except Exception as e:
            print(f"\n❌ Microphone test failed: {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Voice dictation for terminal/Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single dictation (print to stdout)
  python dictate-fixed.py

  # Copy to clipboard
  python dictate-fixed.py --clipboard

  # Continuous mode
  python dictate-fixed.py --continuous

  # Use different model (better accuracy, slower)
  python dictate-fixed.py --model small.en

  # Test microphone
  python dictate-fixed.py --test-mic

Models (speed vs accuracy):
  - tiny.en   : Fastest, lowest accuracy
  - base.en   : Balanced (default)
  - small.en  : Better accuracy, slower
  - medium.en : Best accuracy, slowest (needs good CPU)

Note: Press Ctrl+C ONCE to stop gracefully
        """
    )

    parser.add_argument(
        '--model',
        default='base.en',
        choices=['tiny.en', 'base.en', 'small.en', 'medium.en'],
        help='Whisper model size (default: base.en)'
    )

    parser.add_argument(
        '--language',
        default='en',
        help='Language code (default: en)'
    )

    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Continuous listening mode (Ctrl+C to stop)'
    )

    parser.add_argument(
        '--clipboard',
        action='store_true',
        help='Copy transcription to clipboard instead of printing'
    )

    parser.add_argument(
        '--test-mic',
        action='store_true',
        help='Test microphone and exit'
    )

    parser.add_argument(
        '--no-realtime',
        action='store_true',
        help='Disable real-time transcription (wait for full audio)'
    )

    args = parser.parse_args()

    # Determine output mode
    output_mode = "clipboard" if args.clipboard else "print"

    # Initialize dictation
    try:
        dictation = VoiceDictation(
            model=args.model,
            language=args.language,
            enable_realtime=not args.no_realtime
        )
    except KeyboardInterrupt:
        print("\n\n⏹️  Cancelled during initialization")
        sys.exit(0)

    # Test microphone if requested
    if args.test_mic:
        try:
            success = dictation.test_microphone()
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n\n⏹️  Test cancelled")
            sys.exit(0)

    # Run dictation
    try:
        if args.continuous:
            dictation.listen_continuous(output_mode)
        else:
            dictation.listen_once(output_mode)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped")
    finally:
        # Cleanup
        if dictation and dictation.recorder:
            try:
                dictation.recorder.shutdown()
            except:
                pass


if __name__ == "__main__":
    main()
