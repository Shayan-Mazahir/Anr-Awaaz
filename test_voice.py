#!/usr/bin/env python3
"""
Test if text-to-speech is working on your system
"""

import sys
import os
import tempfile
from gtts import gTTS

print("Testing text-to-speech...")
print("-" * 60)

# Create a test audio file
text = "Hello! This is a test of the text to speech system."
print(f"Converting to speech: \"{text}\"")

tts = gTTS(text=text, lang="en", slow=False)
tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
tts.save(tmp.name)

print(f"Audio file created: {tmp.name}")
print("\nAttempting to play audio...")

# Try to play on macOS
if sys.platform == "darwin":
    print("Using macOS 'afplay' command...")
    result = os.system(f"afplay {tmp.name}")
    if result == 0:
        print("✓ Audio played successfully!")
        print("\nIf you heard the voice, text-to-speech is working!")
    else:
        print("✗ Failed to play audio")
        print(f"Error code: {result}")
else:
    print(f"Your platform is: {sys.platform}")
    print("This test is designed for macOS")

# Cleanup
os.unlink(tmp.name)
print("\nTest complete!")
print("-" * 60)
print("\nNote: Make sure your volume is turned up!")
