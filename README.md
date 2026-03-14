# Pronunciation Coach for Refugees

An AI-powered voice-only language learning application that helps refugees and new arrivals learn English pronunciation by identifying which sounds don't exist in their native language and creating customized lessons.

## What It Does

This app:
- Identifies which English sounds are difficult for speakers of different languages
- Generates customized pronunciation lessons for real-world scenarios (doctor visits, grocery shopping, job interviews, etc.)
- Records user pronunciation attempts
- Provides AI-powered feedback and scoring
- Works entirely through voice (no reading required!)

## How It Works

### Technical Architecture

1. **Phoneme Analysis** (`phonemes.py`)
   - Uses PHOIBLE linguistic database (3000+ languages)
   - Compares English phoneme inventory with user's native language
   - Identifies "gap sounds" that don't exist in their language

2. **AI Lesson Generation** (`lessons.py`)
   - Uses Claude AI to generate realistic practice phrases
   - Phrases contain difficult sounds specific to the learner's language
   - Provides actionable pronunciation tips

3. **Voice Recording** (`recorder.py`)
   - Records user pronunciation via microphone
   - Uses PyAudio for cross-platform audio capture

4. **Speech Recognition** (`analyzer.py`)
   - Uses OpenAI Whisper to transcribe speech
   - Converts user's pronunciation to text

5. **Scoring System** (`scorer.py`)
   - Compares target vs actual pronunciation
   - Provides 0-100 score with star ratings
   - Identifies specific pronunciation errors

6. **Main Interface** (`main.py`)
   - Voice-guided CLI interface
   - Text-to-speech for all instructions
   - Manages lesson flow and user interaction

## Installation

### 1. Install System Dependencies

**macOS:**
```bash
brew install portaudio
```

**Linux:**
```bash
sudo dnf install portaudio-devel -y
# or on Ubuntu/Debian:
sudo apt-get install portaudio19-dev
```

**Windows:**
- PyAudio wheels should work automatically

### 2. Download PHOIBLE Dataset

```bash
curl -L -o phoible.csv "https://raw.githubusercontent.com/phoible/dev/master/data/phoible.csv"
```

### 3. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Python Dependencies

```bash
pip install nltk openai-whisper gtts pyaudio numpy scipy anthropic pandas python-dotenv
python -c "import nltk; nltk.download('cmudict')"
```

### 5. Set Up API Key

1. Get an Anthropic API key from https://console.anthropic.com/settings/keys
2. Create a `.env` file in the project directory:

```bash
echo "ANTHROPIC_API_KEY=your_actual_api_key_here" > .env
```

**IMPORTANT:** Replace `your_actual_api_key_here` with your real API key!

## Running the Application

### Standard Run (Full Voice Interface)

```bash
source venv/bin/activate  # Activate virtual environment
python main.py
```

### What Happens:

1. **Language Selection**
   - System asks: "What is your native language?"
   - Choose from: Arabic, Somali, French, Spanish, Tigrinya, Dari, Pashto, Swahili
   - Or type any language name

2. **Scenario Selection**
   - Choose a real-world scenario:
     - Doctor's Office
     - Grocery Store
     - Job Interview
     - School / Parent Meeting
     - Emergency Services
     - Housing / Landlord

3. **Practice Loop** (5 phrases)
   - Computer speaks the phrase twice
   - Gives pronunciation tip
   - You speak into microphone (6 seconds)
   - System transcribes and scores your pronunciation
   - AI provides personalized feedback

4. **Final Summary**
   - Shows average score
   - Provides encouragement

### Example Session:

```
╔═══════════════════════════════════════════════╗
║        PRONUNCIATION COACH                    ║
║        For New Arrivals Learning English      ║
╚═══════════════════════════════════════════════╝

  Common languages:
  1. Arabic
  2. Somali
  3. French
  ...

  Your language: 1

  Choose a situation:
  1. Doctor's Office
  2. Grocery Store
  ...

  Enter number: 1

  ── Phrase 1 of 5 ──
  Practicing sounds: ð, ɹ

  [Computer speaks: "I have a headache"]
  [Computer speaks tip: "Put your tongue between your teeth for 'th'"]

  🎙  Speak now...
  [6 seconds of recording]

  You said: "i have a headache"
  Score: 95/100  ★★★★★
  Excellent! That was very good.
```

## Testing Individual Components

### Test Phoneme Analysis (No API Key Required)

```bash
source venv/bin/activate
python -c "
from phonemes import find_language, get_language_gaps, find_problems_in_phrase

# Find language
lang = find_language('Arabic')
print(f'Language: {lang}')

# Get phoneme gaps
gaps = get_language_gaps(lang)
print(f'Difficult sounds: {sorted(list(gaps))[:10]}')

# Analyze a phrase
phrase = 'I need to see a doctor'
problems, _ = find_problems_in_phrase(phrase, 'Arabic')
print(f'\\nProblems in \"{phrase}\":')
for p in problems:
    print(f'  {p[\"word\"]}: /{p[\"ipa\"]}/ sound')
"
```

### Test Lesson Generation (Requires API Key)

```bash
source venv/bin/activate
python lessons.py
```

### Test Voice Recording

```bash
source venv/bin/activate
python recorder.py
```

## File Structure

```
watIA-hackathon/
├── main.py              # Main application entry point
├── lessons.py           # AI lesson generation (Claude)
├── phonemes.py          # Phoneme analysis (PHOIBLE)
├── recorder.py          # Audio recording (PyAudio)
├── analyzer.py          # Speech recognition (Whisper)
├── scorer.py            # Pronunciation scoring
├── phoible.csv          # Linguistic database (23MB)
├── modules.txt          # Installation instructions
├── .env                 # API keys (YOU MUST CREATE THIS)
├── .env.example         # Template for .env
├── venv/                # Virtual environment
└── README.md            # This file
```

## How the Scoring Works

1. **Word Matching**: Compares which words were said correctly
2. **Phoneme Analysis**: Identifies which difficult sounds were in missed words
3. **Bonus Points**: Extra credit for correctly pronouncing words with difficult sounds
4. **Final Score**: 0-100 scale with star ratings

**Star Ratings:**
- ★★★★★ (90-100): Excellent
- ★★★★☆ (75-89): Very good
- ★★★☆☆ (60-74): Good
- ★★☆☆☆ (40-59): Needs practice
- ★☆☆☆☆ (0-39): Keep trying

## Technologies Used

- **Python 3.13**
- **PHOIBLE**: Cross-linguistic phonological database
- **Claude AI (Anthropic)**: Lesson generation and feedback
- **OpenAI Whisper**: Speech-to-text transcription
- **gTTS (Google Text-to-Speech)**: Voice guidance
- **NLTK + CMU Dictionary**: English phonetic analysis
- **PyAudio**: Microphone recording
- **Pandas**: Data processing

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
- Make sure you created `.env` file with your API key
- Format: `ANTHROPIC_API_KEY=sk-ant-...`

### "portaudio not found" or PyAudio errors
- macOS: `brew install portaudio`
- Linux: `sudo apt-get install portaudio19-dev`
- Windows: Usually works without extra setup

### "phoible.csv not found"
```bash
curl -L -o phoible.csv "https://raw.githubusercontent.com/phoible/dev/master/data/phoible.csv"
```

### Whisper is slow
- First run downloads ML models (takes time)
- Using "base" model for speed/accuracy balance
- Can change to "tiny" in `analyzer.py` for faster (less accurate) transcription

### No audio output (text-to-speech not working)
- macOS: Should work with `afplay`
- Linux: Install `mpg123` or `ffplay`
- Windows: Should work with built-in player

## Future Enhancements

- Web interface for easier access
- Progress tracking across sessions
- More scenarios and lesson types
- Support for more languages
- Audio waveform visualization
- Mobile app version

## Credits

Built for WatAI Hackathon - helping refugees learn English pronunciation through AI-powered voice coaching.

## License

MIT License - Free to use and modify
