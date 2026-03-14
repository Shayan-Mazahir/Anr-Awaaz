# Quick Start Guide

## Summary

This is an **AI Pronunciation Coach** that helps refugees learn English by:
1. Identifying which English sounds don't exist in their native language
2. Generating practice phrases with those difficult sounds
3. Recording their pronunciation and giving AI-powered feedback

## Installation Complete ✓

You've already installed everything! Here's what was set up:
- ✓ System dependencies (portaudio)
- ✓ Python packages (Whisper, Claude, gTTS, PyAudio, etc.)
- ✓ PHOIBLE linguistic database (23MB)
- ✓ NLTK CMU pronunciation dictionary

## Before You Run

**You need an Anthropic API key** to use the AI features.

### Get Your API Key:

1. Go to: https://console.anthropic.com/settings/keys
2. Sign up / log in
3. Click "Create Key"
4. Copy the key (starts with `sk-ant-`)

### Add Your API Key:

Edit the `.env` file in this directory:

```bash
# Open the .env file and replace the placeholder with your real key:
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

Or use this command (replace with your real key):

```bash
echo "ANTHROPIC_API_KEY=sk-ant-your-actual-key-here" > .env
```

## How to Run

### 1. Test Components (No API Key Needed)

```bash
source venv/bin/activate
python demo.py
```

This shows:
- How the phoneme analysis works
- Which sounds are difficult for different languages
- How the scoring system works
- Available practice scenarios

### 2. Test AI Lesson Generation (Requires API Key)

```bash
source venv/bin/activate
python lessons.py
```

This will:
- Generate 3 practice phrases for Arabic speakers at a doctor's office
- Show the difficult sounds in each phrase
- Display pronunciation tips

### 3. Run the Full App (Requires API Key + Microphone)

```bash
source venv/bin/activate
python main.py
```

This is the complete voice-guided experience:
1. Select your native language
2. Choose a scenario (doctor, grocery, job interview, etc.)
3. Practice 5 phrases with AI feedback

**Note:** Make sure to allow microphone access when prompted!

## Quick Demo Output

When you ran `demo.py`, you saw:

### Phoneme Analysis
- **Arabic speakers** struggle with 37 English sounds (like /aɪ/, /aʊ/, /θ/)
- **Spanish speakers** struggle with 41 sounds (like /h/, /d̠ʒ/, /æ/)
- The app automatically detects these from a linguistic database!

### Phrase Analysis
For "I need to see a doctor" (Arabic speaker):
- Word "I" contains /aɪ/ sound (not in Arabic)
- Word "doctor" contains /ɑː/ and /əː/ sounds (not in Arabic)

### Scoring Example
- Perfect match: 100/100 ★★★★★
- Missing 2 words: 75/100 ★★★★☆
- Completely wrong: 19/100 ★☆☆☆☆

### 6 Available Scenarios
1. Doctor's Office
2. Grocery Store
3. Job Interview
4. School / Parent Meeting
5. Emergency Services
6. Housing / Landlord

## File Overview

- `main.py` - Run this for the full app
- `demo.py` - Run this to test components
- `lessons.py` - AI lesson generation
- `phonemes.py` - Phoneme analysis engine
- `recorder.py` - Audio recording
- `analyzer.py` - Speech recognition (Whisper)
- `scorer.py` - Pronunciation scoring

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
→ Edit `.env` file and add your API key

### "No module named 'pandas'" or similar
→ Make sure you're in the virtual environment:
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### Audio not working
→ Check microphone permissions in System Preferences/Settings

### First run is slow
→ Whisper downloads ML models on first use (normal, happens once)

## What Happens in a Full Session

```
1. "What is your native language?"
   → You type: 1 (Arabic)

2. "Which situation would you like to practice?"
   → You type: 1 (Doctor's Office)

3. AI generates 5 custom phrases like:
   "I have a headache"
   "When should I take this medicine"
   etc.

4. For each phrase:
   - Computer speaks it twice
   - Gives a tip: "Put your tongue between your teeth for 'th'"
   - Records you saying it (6 seconds)
   - Transcribes what you said
   - Scores your pronunciation (0-100)
   - AI gives personalized feedback

5. Final summary:
   "Your average score was 78/100"
   "Good effort. Practice these phrases every day..."
```

## Technologies Used

- **AI**: Claude (Anthropic) for lesson generation
- **Speech Recognition**: OpenAI Whisper
- **Text-to-Speech**: Google TTS
- **Phonetics**: PHOIBLE database + CMU Dictionary
- **Audio**: PyAudio for recording

## Next Steps

1. **Get your API key** from Anthropic
2. **Edit `.env`** to add the key
3. **Run `python lessons.py`** to test AI generation
4. **Run `python main.py`** for the full experience!

## Support

If something doesn't work:
1. Check that you're in the virtual environment (`source venv/bin/activate`)
2. Check that your API key is set correctly in `.env`
3. Check that your microphone is connected and permissions are granted
4. Try running `demo.py` first to isolate the issue

---

**Built for WatAI Hackathon** - Helping refugees learn English pronunciation through AI 🌍
