# 🗣 Anṅ Awaaz — Oral-First English Pronunciation Coach

> Built at the WatAI × Reception House Waterloo Hackathon, March 14 2026.  
> An AI-powered, voice-first English learning tool for refugees and newcomers with limited literacy.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Architecture Overview](#architecture-overview)
3. [Requirements](#requirements)
4. [Setup & Installation](#setup--installation)
5. [Running the App](#running-the-app)
6. [Hosting & Deployment](#hosting--deployment)
7. [How to Use](#how-to-use)
8. [Project Structure](#project-structure)
9. [How to Contribute](#how-to-contribute)
10. [Known Bugs](#known-bugs)
11. [Issues That May Come Up](#issues-that-may-come-up)
12. [Where to Fix Known Issues](#where-to-fix-known-issues)
13. [API Keys & Environment Variables](#api-keys--environment-variables)
14. [Roadmap / Future Work](#roadmap--future-work)
15. For Support - RayyanMoosani.com

---

## What It Does

Anṅ Awaaz teaches spoken English to people who may not read or write. It has two practice modes:

**Phrase Drilling** — Claude generates 5 phrases tailored to the learner's native language phoneme gaps (sounds that don't exist in their language are prioritised). The user listens, then repeats. Whisper transcribes the audio, a phoneme-level scorer grades it, and Claude gives feedback in the learner's own language.

**Conversation Mode** — Claude role-plays a real-life character (doctor, cashier, teacher, landlord, 911 operator) in a multi-turn dialogue. The user speaks naturally. Every turn is scored for both communication clarity and pronunciation.

The entire UI is voice-guided. Language selection uses flag buttons + native script so someone who cannot read English can still navigate it independently.

---

## Architecture Overview

```
Browser (index.html)
    │
    │  HTTP / FormData
    ▼
FastAPI server (app.py / main.py)
    ├── /api/tts          → ElevenLabs (voice output)
    ├── /api/lesson       → Claude claude-sonnet-4-20250514 (lesson generation)
    ├── /api/score        → Whisper (STT) + scorer.py (phoneme scoring)
    ├── /api/translate    → deep-translator / Google Translate
    ├── /api/conversation → Claude (roleplay engine)
    └── /api/dialects     → phonemes.py / PHOIBLE database

Core modules:
    phonemes.py   — PHOIBLE + CMU dict → language gap detection
    scorer.py     — phoneme-level pronunciation scoring
    analyzer.py   — Whisper STT with accent-aware prompting
    lessons.py    — Claude lesson + feedback generation
    conversation.py — Claude conversation engine
    session.py    — in-session phoneme tracking
    memory.py     — cross-session progress persistence (JSON files)
```

---

## Requirements

- Python 3.10+
- [PHOIBLE dataset CSV](https://phoible.org/) — `phoible.csv` must be in the project root
- API keys for:
  - [Anthropic](https://console.anthropic.com/) (Claude)
  - [ElevenLabs](https://elevenlabs.io/) (voice output)
- `ffmpeg` installed on your system (Whisper uses it to decode audio)

### Python packages

```
fastapi
uvicorn
python-dotenv
anthropic
elevenlabs
openai-whisper
deep-translator
nltk
pandas
pydantic
python-multipart
```

Install everything at once:

```bash
pip install fastapi uvicorn python-dotenv anthropic elevenlabs openai-whisper deep-translator nltk pandas pydantic python-multipart
```

You also need the NLTK CMU pronouncing dictionary:

```python
import nltk
nltk.download('cmudict')
```

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-team/anṅ-awaaz.git
cd anṅ-awaaz
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt` yet:

```bash
pip install fastapi uvicorn python-dotenv anthropic elevenlabs openai-whisper deep-translator nltk pandas pydantic python-multipart
python3 -c "import nltk; nltk.download('cmudict')"
```

### 4. Add the PHOIBLE dataset

Download `phoible.csv` from [https://phoible.org/](https://phoible.org/) and place it in the project root directory (same folder as `app.py`).

### 5. Create your `.env` file

```bash
cp .env.example .env
```

Then edit `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
```

### 6. Place the frontend

Make sure `index.html` is either:
- In a `static/` folder (served automatically by FastAPI), **or**
- In the project root (served at `/` by the fallback route in `app.py`)

---

## Running the App

### Web app (recommended)

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Then open your browser at: `http://localhost:8000`

### CLI mode (microphone required, no browser)

```bash
python main.py
```

For CLI + FastAPI server together:

```bash
python main.py --server
```

---

## Hosting & Deployment

Run on your laptop and share the local IP with others on the same WiFi:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Find your IP:
```bash
ipconfig getifaddr en0    # macOS
hostname -I               # Linux
ipconfig                  # Windows
```

Other devices on the same network can visit `http://YOUR_IP:8000`.

> ⚠️ Make sure your firewall allows port 8000.

### Option B — Cloud VM (e.g. AWS EC2 / GCP / DigitalOcean)

1. SSH into your server and clone the repo
2. Follow the setup steps above
3. Install `nginx` as a reverse proxy:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

4. Run with a process manager:

```bash
pip install gunicorn
gunicorn app:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

> Use `-w 1` (one worker). The app stores conversation state in memory — multiple workers each have their own state dict, causing sessions to break across requests. See Known Bugs.

### Option C — Railway / Render / Fly.io (PaaS)

These platforms can deploy directly from a GitHub repo. You'll need to:

1. Add a `Procfile`:
```
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

2. Set environment variables (`ANTHROPIC_API_KEY`, `ELEVENLABS_API_KEY`) in the platform dashboard.

3. Add `phoible.csv` to the repo (it's ~14MB, consider Git LFS).

> ⚠️ Whisper downloads model weights on first run (~140MB for `small`). This will be slow on first boot in a serverless environment. Pin to `tiny` model for faster cold starts.

---

## How to Use

1. **Open the app** in a browser — on first click you'll hear a welcome message.
2. **Tap your language flag** — e.g. 🇸🇦 Arabic. If your language has dialects, a second row appears.
3. **Tap Continue** — the app reads out the practice options in your language.
4. **Choose a mode** — Repeat Phrases (🔁) or Conversation (💬).
5. **Tap a situation** — Doctor 🏥, Shop 🛒, Job 💼, School 📚, Help 🚨, or Home 🏠.
6. **Tap Start** — lessons generate in ~3 seconds.
7. **Listen** to the phrase, then tap the 🎙 button and speak.
8. **See your score** and hear feedback in your language.
9. **Continue** through all phrases, then see your summary.

---

## Project Structure

```
anṅ-awaaz/
├── app.py              # FastAPI server — all HTTP endpoints
├── main.py             # CLI entry point + FastAPI server (legacy)
├── analyzer.py         # Whisper STT with accent-aware prompting
├── conversation.py     # Claude conversation engine (roleplay)
├── lessons.py          # Claude lesson generation + AI feedback
├── phonemes.py         # PHOIBLE + CMU dict — language gap detection
├── scorer.py           # Phoneme-level pronunciation scoring
├── session.py          # Per-session phoneme tracker (adaptive difficulty)
├── memory.py           # Cross-session JSON memory (per language)
├── recorder.py         # Microphone recording (CLI mode only)
├── index.html          # Full single-page frontend
├── phoible.csv         # PHOIBLE phoneme database (download separately)
├── memory/             # Auto-created — stores per-language progress JSON
├── .env                # API keys (never commit this)
└── requirements.txt
```

---

## How to Contribute

### Adding a new scenario

Edit `SCENARIOS` in `lessons.py` and `CONVERSATION_SCENARIOS` in `conversation.py`. Both need a matching entry. In `index.html`, add the scenario to `SCENARIO_META`:

```javascript
const SCENARIO_META = {
    // ...
    pharmacy: { illus: '💊', short: "Pharmacy" },
};
```

Then add it to the `VOICE_SCENARIO` dict in the same file for the audio description.

### Adding a new language

Languages come from PHOIBLE automatically — if it's in the database, the phoneme gaps will be computed. To add it to the default language grid on the homepage, add an entry to `LANG_META` in `index.html`:

```javascript
const LANG_META = {
    // ...
    "Hausa": { flag: "🇳🇬", native: "Harshen Hausa" },
};
```

And add it to `common_languages` in `app.py`'s `/api/setup` endpoint.

### Improving Whisper accuracy

Edit `analyzer.py`. The `initial_prompt` and `context` parameter are the main levers. Longer, more specific prompts and passing recent conversation text as context both help significantly for accented speech.

### Changing the AI model or prompts

All Claude calls use `claude-sonnet-4-20250514`. To change the model, update the `model=` parameter in:
- `lessons.py` → `generate_lesson()` and `generate_correction_feedback()`
- `conversation.py` → `advance_conversation()` and `get_conversation_summary()`

### Changing the TTS voice

ElevenLabs voice ID is set in `app.py`:
```python
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Bella
```
Browse available voices at [elevenlabs.io/voice-library](https://elevenlabs.io/voice-library) and swap the ID.

---

## Known Bugs

### 1. Whisper mishears broken/accented English
**Status:** Partially fixed.  
**What happens:** Whisper transcribes "I looking for sugar" as "we're looking for you." This happens because Whisper's default behaviour is to normalise broken speech into fluent English.  
**Current fix:** `analyzer.py` passes an `initial_prompt` describing the speaker and recent conversation as context. Works well in quiet environments.  
**Remaining issue:** Still fails on very short phrases (1–2 words) and very strong accents in noisy environments.  
**Fix location:** `analyzer.py` → `transcribe()` function.

### 2. Conversation state resets on server restart
**Status:** Known, not fixed.  
**What happens:** `conversation_states` is a plain Python dict in `app.py`. If the server restarts mid-session, the session is lost and the next turn returns a 404.  
**Fix location:** `app.py` → replace `conversation_states = {}` with Redis, a database, or at minimum write to a temp JSON file.

### 3. Multiple workers break conversation sessions
**Status:** Known.  
**What happens:** If you run with `gunicorn -w 4`, each worker has its own `conversation_states` dict. A session started on worker 1 won't be found on worker 2.  
**Fix:** Use `-w 1` for now, or move state to Redis (see above).

### 4. TTS doesn't play without a prior user click
**Status:** Partially fixed.  
**What happens:** Browsers block audio autoplay before any user gesture. The welcome message and some voice prompts can be silently blocked.  
**Current fix:** `unlockAudio()` is called at the top of every click handler to pre-unlock the Web Audio context.  
**Remaining issue:** If a user sits on the page for a long time before clicking anything, the first audio may still be blocked in some browsers.  
**Fix location:** `index.html` → `unlockAudio()` and `playTTS()`.

### 5. Translation adds latency before voice plays
**Status:** Known.  
**What happens:** Translating UI text via the `/api/translate` endpoint takes ~1–2 seconds. If the browser's gesture window expires during this await, the subsequent `play()` call is blocked.  
**Current fix:** Audio context is unlocked synchronously before translation is awaited.  
**Fix location:** `index.html` → `speakStepScenario()`, `speakPhraseIntro()`, `selectScenario()`.

### 6. PHOIBLE loads slowly on startup
**Status:** Known, not fixed.  
**What happens:** `phonemes.py` loads the entire `phoible.csv` into a pandas DataFrame on import. On slower machines this takes 3–5 seconds and blocks the first request.  
**Fix location:** `phonemes.py` — load in a background thread or pre-cache the gap lookups to a smaller JSON file at build time.

### 7. Score is 0 when Whisper returns empty string
**Status:** Fixed in `app.py`.  
**What happens:** If Whisper hears silence or noise and returns empty, the app now returns a helpful message instead of crashing or returning a confusing zero score.

---

## Issues That May Come Up

### "phoible.csv not found"
You need to download it separately. Get it from [https://phoible.org/](https://phoible.org/) and place it in the project root. Without it, `phonemes.py` will crash on import and nothing will work.

### "whisper not installed"
```bash
pip install openai-whisper
```
Whisper also requires `ffmpeg`. On macOS: `brew install ffmpeg`. On Ubuntu: `sudo apt install ffmpeg`.

### Whisper model downloads on first run
The first time `transcribe()` is called it will download the model weights (~140MB for `small`). This is automatic but takes time. It's cached after the first download at `~/.cache/whisper/`.

### "ElevenLabs not configured" — voice doesn't work
Check that `ELEVENLABS_API_KEY` is set in your `.env` file. The app will still work without it — scoring and feedback work — but there will be no voice output.

### Browser microphone permission denied
The app requires microphone access. If the browser shows a permission denied error, go to your browser's site settings and allow microphone for `localhost:8000`.

### `deep_translator` rate limiting
Google Translate (used by `translate_to_native` in `lessons.py`) has rate limits on the free tier. If you see translation errors after many requests, add a small sleep between calls or upgrade to the paid API.

### CMU dictionary word not found
Some words — especially proper nouns, very rare words, or misspellings — are not in the CMU pronouncing dictionary. `scorer.py` silently skips these words. This means the phoneme score can be inflated if many words in a phrase are unknown to CMU.

### Session ID collision
`conversation_states` uses UUIDs, so collision is extremely unlikely but theoretically possible if many sessions are running simultaneously.

---

## Where to Fix Known Issues

| Issue | File | Function / Line |
|-------|------|-----------------|
| Whisper mishears accented speech | `analyzer.py` | `transcribe()` — adjust `initial_prompt` and `context` |
| Whisper model size (speed vs accuracy) | `app.py` | Lines calling `transcribe(..., model_size=...)` |
| Conversation state lost on restart | `app.py` | `conversation_states = {}` — replace with persistent store |
| Multi-worker session bug | `app.py` | Same — move state out of process memory |
| TTS autoplay blocked | `index.html` | `unlockAudio()`, `playTTS()`, `playTTSAndWait()` |
| Translation latency before voice | `index.html` | `speakStepScenario()`, `selectScenario()`, `speakPhraseIntro()` |
| PHOIBLE slow startup | `phonemes.py` | Module-level `pd.read_csv()` call — consider lazy loading |
| Score inflated for unknown words | `scorer.py` | `score_attempt()` — handle missing CMU entries explicitly |
| Memory not connected to web app | `memory.py` | `app.py` endpoints don't call `load_memory` / `save_memory` — CLI only |
| Claude prompt for unclear speech | `conversation.py` | `advance_conversation()` — the `speech_seems_unclear` heuristic |

---

## API Keys & Environment Variables

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
ELEVENLABS_API_KEY=sk_...
```

| Variable | Required | Used in | Notes |
|----------|----------|---------|-------|
| `ANTHROPIC_API_KEY` | Yes | `lessons.py`, `conversation.py` | Get from console.anthropic.com |
| `ELEVENLABS_API_KEY` | Yes for voice | `app.py`, `main.py` | Get from elevenlabs.io. App still works without it but is silent. |

---

## Roadmap / Future Work

**Short term (1–2 weeks)**
- Move conversation state to Redis or SQLite so sessions survive server restarts
- Add a `requirements.txt` with pinned versions
- Pre-compute and cache PHOIBLE gap lookups per language so startup is instant
- Add a loading spinner on the language page while PHOIBLE initialises

**Medium term (1–2 months)**
- Connect `memory.py` to the web app — currently cross-session memory only works in CLI mode
- Add visual picture cues on each phrase card (e.g. a photo of a doctor's office when practicing those phrases) for learners who don't read
- Add more scenarios: pharmacy, bus/transit, bank, post office
- Allow the user to re-hear the character's reply in conversation mode by tapping the message bubble
- Add a "slow" button on TTS playback that replays at 0.75x speed

**Long term**
- Offline mode — bundle a small Whisper model (tiny) and run everything locally so it works without internet
- Tablet/kiosk mode optimised for Reception House waiting rooms
- Partner with a linguist to validate the phoneme gap mappings against real learner data
- Add video cues (short clips) showing mouth position for difficult sounds like /θ/ and /ð/
- Multi-user support with proper accounts so progress isn't lost when clearing browser storage

---

## Credits

Built at the **AI & Data Science for Good Hackathon**, March 14 2026  
Hosted by Reception House Waterloo Region × University of Waterloo × WatAI

**Core technologies:**
- [Claude](https://anthropic.com) (Anthropic) — lesson generation, conversation engine, feedback
- [Whisper](https://github.com/openai/whisper) (OpenAI) — speech-to-text
- [ElevenLabs](https://elevenlabs.io) — multilingual text-to-speech
- [PHOIBLE](https://phoible.org) — cross-linguistic phoneme database
- [CMU Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict) — English phoneme lookup
- [FastAPI](https://fastapi.tiangolo.com) — backend API
