#!/bin/bash
# List available audio devices

echo "🎤 Audio Devices on Your System"
echo "================================"
echo ""

echo "📋 Recording Devices (arecord):"
arecord -l
echo ""

echo "📋 Playback Devices (aplay):"
aplay -l
echo ""

echo "📋 PulseAudio Sources (if available):"
if command -v pactl &> /dev/null; then
    pactl list sources short
else
    echo "   PulseAudio not found"
fi
echo ""

echo "📋 PulseAudio Sinks (if available):"
if command -v pactl &> /dev/null; then
    pactl list sinks short
else
    echo "   PulseAudio not found"
fi
echo ""

echo "💡 Tips:"
echo "   - Look for 'card X: device Y' in arecord output"
echo "   - Default device is usually card 0, device 0"
echo "   - Test with: arecord -f cd -d 3 test.wav && aplay test.wav"
