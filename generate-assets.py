#!/usr/bin/env python3
"""
Generate sound and icon assets for Voice Dictation Daemon
"""

import wave
import struct
import math
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

def generate_tone(filename, frequency, duration_ms, volume=0.5, fade=True):
    """Generate a simple tone WAV file"""
    sample_rate = 44100
    num_samples = int(sample_rate * duration_ms / 1000)

    with wave.open(str(filename), 'w') as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)

        for i in range(num_samples):
            t = i / sample_rate

            # Generate sine wave
            value = math.sin(2 * math.pi * frequency * t)

            # Apply fade in/out
            if fade:
                fade_samples = int(num_samples * 0.1)  # 10% fade
                if i < fade_samples:
                    value *= i / fade_samples
                elif i > num_samples - fade_samples:
                    value *= (num_samples - i) / fade_samples

            # Apply volume and convert to 16-bit
            sample = int(value * volume * 32767)
            wav.writeframes(struct.pack('<h', sample))

def generate_start_sound():
    """Generate ascending tone for start"""
    filename = SCRIPT_DIR / 'sounds' / 'start.wav'
    sample_rate = 44100
    duration_ms = 200
    num_samples = int(sample_rate * duration_ms / 1000)

    with wave.open(str(filename), 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        for i in range(num_samples):
            t = i / sample_rate
            progress = i / num_samples

            # Ascending frequency (440Hz to 880Hz)
            frequency = 440 + (880 - 440) * progress
            value = math.sin(2 * math.pi * frequency * t)

            # Fade in/out
            fade_samples = int(num_samples * 0.15)
            if i < fade_samples:
                value *= i / fade_samples
            elif i > num_samples - fade_samples:
                value *= (num_samples - i) / fade_samples

            sample = int(value * 0.4 * 32767)
            wav.writeframes(struct.pack('<h', sample))

    print(f"Created: {filename}")

def generate_stop_sound():
    """Generate descending tone for stop"""
    filename = SCRIPT_DIR / 'sounds' / 'stop.wav'
    sample_rate = 44100
    duration_ms = 200
    num_samples = int(sample_rate * duration_ms / 1000)

    with wave.open(str(filename), 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        for i in range(num_samples):
            t = i / sample_rate
            progress = i / num_samples

            # Descending frequency (880Hz to 440Hz)
            frequency = 880 - (880 - 440) * progress
            value = math.sin(2 * math.pi * frequency * t)

            # Fade in/out
            fade_samples = int(num_samples * 0.15)
            if i < fade_samples:
                value *= i / fade_samples
            elif i > num_samples - fade_samples:
                value *= (num_samples - i) / fade_samples

            sample = int(value * 0.4 * 32767)
            wav.writeframes(struct.pack('<h', sample))

    print(f"Created: {filename}")

def generate_icons():
    """Generate SVG icons for tray"""

    # Active (listening) icon - green microphone
    active_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <!-- Microphone body -->
  <rect x="9" y="2" width="6" height="11" rx="3" fill="#4CAF50"/>
  <!-- Microphone stand -->
  <path d="M12 15v4M8 19h8" stroke="#4CAF50" stroke-width="2" stroke-linecap="round"/>
  <!-- Sound waves -->
  <path d="M5 9a7 7 0 0 0 14 0" stroke="#4CAF50" stroke-width="2" fill="none" stroke-linecap="round"/>
  <!-- Recording indicator -->
  <circle cx="19" cy="5" r="3" fill="#f44336">
    <animate attributeName="opacity" values="1;0.3;1" dur="1s" repeatCount="indefinite"/>
  </circle>
</svg>'''

    active_file = SCRIPT_DIR / 'icons' / 'mic-active.svg'
    active_file.write_text(active_svg)
    print(f"Created: {active_file}")

    # Idle icon - gray microphone
    idle_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <!-- Microphone body -->
  <rect x="9" y="2" width="6" height="11" rx="3" fill="#9E9E9E"/>
  <!-- Microphone stand -->
  <path d="M12 15v4M8 19h8" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round"/>
  <!-- Sound waves -->
  <path d="M5 9a7 7 0 0 0 14 0" stroke="#9E9E9E" stroke-width="2" fill="none" stroke-linecap="round"/>
</svg>'''

    idle_file = SCRIPT_DIR / 'icons' / 'mic-idle.svg'
    idle_file.write_text(idle_svg)
    print(f"Created: {idle_file}")


if __name__ == '__main__':
    print("Generating Voice Dictation assets...")
    print()

    # Ensure directories exist
    (SCRIPT_DIR / 'sounds').mkdir(exist_ok=True)
    (SCRIPT_DIR / 'icons').mkdir(exist_ok=True)

    # Generate sounds
    print("Generating sounds...")
    generate_start_sound()
    generate_stop_sound()
    print()

    # Generate icons
    print("Generating icons...")
    generate_icons()
    print()

    print("Done!")
