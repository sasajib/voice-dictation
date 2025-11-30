#!/usr/bin/env python3
"""
Download Whisper models before using voice dictation
This allows Ctrl+C to work properly in the main dictation script
"""

import sys
import signal

# Handle Ctrl+C gracefully
def signal_handler(sig, frame):
    print("\n\n⏹️  Download cancelled")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

try:
    from faster_whisper import WhisperModel
    from huggingface_hub import snapshot_download
except ImportError as e:
    print(f"❌ Error: Missing dependency: {e}")
    print("\n💡 Please run: pip install -r requirements.txt")
    sys.exit(1)

import argparse

def download_model(model_name, show_progress=True):
    """Download a Whisper model"""

    print(f"📥 Downloading {model_name} model...")
    print(f"   This is a one-time download")
    print(f"   Press Ctrl+C to cancel")
    print("")

    model_sizes = {
        'tiny.en': '~75 MB',
        'base.en': '~150 MB',
        'small.en': '~500 MB',
        'medium.en': '~1.5 GB',
    }

    print(f"   Size: {model_sizes.get(model_name, 'unknown')}")
    print(f"   Location: ~/.cache/huggingface/hub/")
    print("")

    try:
        # This will download the model with progress bar
        print("   Downloading files...")
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        print(f"\n✅ {model_name} model downloaded successfully!")
        return True

    except KeyboardInterrupt:
        print("\n\n⏹️  Download cancelled")
        return False
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download Whisper models for offline use",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download tiny model (fastest, smallest)
  python download-models.py --model tiny.en

  # Download base model (recommended)
  python download-models.py --model base.en

  # Download all common models
  python download-models.py --all

Model sizes:
  tiny.en   : ~75 MB  (fastest, lowest accuracy)
  base.en   : ~150 MB (balanced - recommended)
  small.en  : ~500 MB (better accuracy)
  medium.en : ~1.5 GB (best accuracy)

After downloading, models are cached and won't be downloaded again.
        """
    )

    parser.add_argument(
        '--model',
        choices=['tiny.en', 'base.en', 'small.en', 'medium.en'],
        help='Which model to download'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Download all common models (tiny, base, small)'
    )

    args = parser.parse_args()

    if not args.model and not args.all:
        print("❌ Error: Specify --model or --all")
        print("\nExamples:")
        print("  python download-models.py --model base.en")
        print("  python download-models.py --all")
        sys.exit(1)

    models_to_download = []

    if args.all:
        models_to_download = ['tiny.en', 'base.en', 'small.en']
    else:
        models_to_download = [args.model]

    print("🎤 Whisper Model Downloader")
    print("=" * 50)
    print("")

    success_count = 0

    for i, model in enumerate(models_to_download, 1):
        if len(models_to_download) > 1:
            print(f"[{i}/{len(models_to_download)}] ", end="")

        if download_model(model):
            success_count += 1
        else:
            break  # Stop on failure or cancellation

        if i < len(models_to_download):
            print("\n" + "-" * 50 + "\n")

    print("\n" + "=" * 50)

    if success_count == len(models_to_download):
        print(f"✅ Downloaded {success_count}/{len(models_to_download)} models successfully!")
        print("\n🎤 Ready to use:")
        print("   python dictate-fixed.py --test-mic")
    else:
        print(f"⚠️  Downloaded {success_count}/{len(models_to_download)} models")


if __name__ == "__main__":
    main()
