#!/usr/bin/env python3
"""
Pronunciation Coach for Refugees
Voice-only. Zero text required. Just speak.
Two modes: phrase drilling + real conversation scenarios.
"""

import sys
import time
import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

# from lessons import generate_lesson, generate_correction_feedback, translate_to_native, list_scenarios
from lessons import generate_lesson, generate_correction_feedback, translate_to_native, prewarm_translations, list_scenarios
from conversation import (
    start_conversation,
    advance_conversation,
    get_conversation_summary,
    list_conversation_scenarios,
    CONVERSATION_SCENARIOS,
)
from phonemes import find_language, get_dialects
from scorer import score_attempt, score_to_stars
from recorder import record_audio, cleanup
from analyzer import transcribe
from session import PhonemeTracker, print_session_heatmap, get_adaptive_focus

# --- FastAPI & ElevenLabs Imports ---
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from memory import load_memory, save_memory, update_memory_from_tracker, get_focus_sounds_from_memory, print_memory_summary
# ----------------------------------

# gTTS language codes - Removed (Using ElevenLabs)
# ----------------------------------

current_language: str = "English"

# --- FastAPI & ElevenLabs Setup ---
app = FastAPI(title="Pronunciation Coach API")

# Update CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY
) if ELEVENLABS_API_KEY else None

class LessonRequest(BaseModel):
    language: str
    scenario: str

class TTSRequest(BaseModel):
    text: str
# ----------------------------------


# ──────────────────────────────────────────
# Audio helpers
# ──────────────────────────────────────────

def _play(path: str):
    if sys.platform == "darwin":
        os.system(f"afplay {path}")
    elif sys.platform == "win32":
        os.system(f"start /wait {path}")
    else:
        os.system(f"mpg123 -q {path} 2>/dev/null || ffplay -nodisp -autoexit {path} 2>/dev/null")


def _speak(text: str, lang: str):
    """
    Speak text using ElevenLabs. 
    Notes: We've removed gTTS. If ElevenLabs fails or key is missing, we log an error.
    """
    print(f"  🔊  {text}")
    
    if not elevenlabs_client:
        print("  ⚠  ElevenLabs not configured. Speech disabled.")
        return

    try:
        # 21m00T838D4w9H5XCrsX is Rachel
        voice_id = "EXAVITQu4vr4xnSDxMaL" 
        audio_generator = elevenlabs_client.text_to_speech.convert(
            voice_id=voice_id,
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
            ),
        )
        audio_bytes = b"".join(list(audio_generator))
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_name = tmp.name
        _play(tmp_name)
        os.unlink(tmp_name)
    except Exception as e:
        print(f"  ⚠  ElevenLabs TTS failed: {e}")


def speak(text: str):
    """Speak using ElevenLabs."""
    _speak(text, "en") # Always use Multilingual model


def speak_english(text: str):
    """Speak using ElevenLabs."""
    _speak(text, "en")


# ──────────────────────────────────────────
# CLI helpers
# ──────────────────────────────────────────

def clear():
    os.system("cls" if sys.platform == "win32" else "clear")


def banner():
    print("""
╔═══════════════════════════════════════════════╗
║        PRONUNCIATION COACH                    ║
║        For New Arrivals Learning English      ║
╚═══════════════════════════════════════════════╝
""")


def record_and_transcribe() -> str:
    """Record audio and return transcribed text."""
    audio_path = record_audio(duration=6)
    print("  ⏳  Transcribing...")
    try:
        spoken = transcribe(audio_path)
    except Exception as e:
        print(f"  ⚠  Transcription error: {e}")
        spoken = ""
    finally:
        cleanup(audio_path)
    return spoken


# --- FastAPI API Endpoints ---

@app.get("/api/setup")
def get_setup_data():
    """Return available scenarios and common languages."""
    return {
        "scenarios": list_scenarios(),
        "common_languages": [
            "Arabic", "Somali", "French", "Spanish", 
            "Tigrinya", "Dari", "Pashto", "Swahili"
        ]
    }

@app.post("/api/lesson")
def create_lesson(req: LessonRequest):
    """Generate a lesson based on native language and scenario."""
    try:
        # Note: req.scenario in app.py was req.scenario, but lessons.py uses scenario_key
        lesson = generate_lesson(req.language, req.scenario, num_phrases=5)
        return lesson
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/tts")
def generate_tts(req: TTSRequest):
    """Generate TTS using ElevenLabs and return audio bytes."""
    if not elevenlabs_client:
        raise HTTPException(status_code=500, detail="ElevenLabs API key not configured")
    print(f"Generating TTS for: {req.text}")
    try:
        voice_id = "21m00T838D4w9H5XCrsX" 
        audio_generator = elevenlabs_client.text_to_speech.convert(
            voice_id=voice_id,
            output_format="mp3_44100_128",
            text=req.text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5, similarity_boost=0.75, style=0.0, use_speaker_boost=True,
            ),
        )
        audio_bytes = b"".join(list(audio_generator))
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        print(f"ElevenLabs Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

@app.post("/api/score")
async def score_audio(
    target_phrase: str = Form(...),
    language: str = Form(...),
    audio: UploadFile = File(...)
):
    """Score the spoken audio against the target phrase."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        spoken_text = transcribe(tmp_path, model_size="base")
        if not spoken_text.strip():
             return {
                "score": 0, "spoken": "", "target": target_phrase,
                "feedback": "I couldn't hear anything. Please try speaking closer to the microphone.",
                "stars": "☆☆☆☆☆"
             }

        result = score_attempt(target_phrase, spoken_text, language)
        
        if result["score"] >= 85:
            feedback = "Excellent! That was very good."
        else:
            feedback = generate_correction_feedback(
                target_phrase=target_phrase,
                spoken_phrase=spoken_text,
                language_query=language,
                mismatched_phonemes=result["phoneme_mismatches"],
            )

        return {
            "score": result["score"],
            "spoken": result["spoken"],
            "target": result["target"],
            "feedback": feedback,
            "stars": score_to_stars(result["score"]),
            "matched_words": result["matched_words"],
            "missed_words": result["missed_words"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring error: {str(e)}")
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)

# ----------------------------


# ──────────────────────────────────────────
# Language + dialect selection
# ──────────────────────────────────────────

def pick_language() -> tuple:
    global current_language

    speak_english("Welcome. Please type your native language.")
    print("\n  Examples: Arabic, Urdu, Somali, French, Spanish, Pashto, Dari, Swahili")
    print("  Or type any language name.\n")
    choice = input("  Your language: ").strip()

    name = find_language(choice)
    if not name:
        print(f"\n  ⚠  '{choice}' not found. Using Arabic as default.")
        speak_english("Language not found. Using Arabic.")
        name = "Arabic"

    dialects = get_dialects(choice)
    if dialects:
        print(f"\n  We found multiple dialects for {name.split()[0]}:")
        for i, d in enumerate(dialects, 1):
            print(f"  {i}. {d}")
        print()
        d_choice = input("  Pick your dialect (number, or press Enter to skip): ").strip()
        if d_choice:
            try:
                idx = int(d_choice) - 1
                if 0 <= idx < len(dialects):
                    name = dialects[idx]
            except ValueError:
                matched = find_language(d_choice)
                if matched and matched in dialects:
                    name = matched

    current_language = name
    prewarm_translations(name)

    # Load memory and show returning user summary
    profile = load_memory(name)
    print_memory_summary(profile)

    greeting = translate_to_native(
        "Welcome! We will practice English together. I will teach you useful phrases and help you speak clearly.",
        name
    )
    speak(greeting)
    return name, profile


# ──────────────────────────────────────────
# Mode selection
# ──────────────────────────────────────────

def pick_mode() -> str:
    prompt = translate_to_native(
        "How would you like to practice? Choose a number.",
        current_language
    )
    speak(prompt)

    opt1 = translate_to_native("Conversation — have a real conversation with a character", current_language)
    opt2 = translate_to_native("Phrase Drilling — practice specific phrases one by one", current_language)

    print(f"\n  1. 🗣  {opt1}")
    print(f"  2. 📝  {opt2}")
    print()
    choice = input("  Enter number: ").strip()
    return "drill" if choice == "2" else "conversation"


# ──────────────────────────────────────────
# Scenario selection
# ──────────────────────────────────────────

def pick_scenario(mode: str) -> str:
    prompt = translate_to_native(
        "Which situation would you like to practice? Choose a number.",
        current_language
    )
    speak(prompt)

    scenarios = list_conversation_scenarios() if mode == "conversation" else list_scenarios()
    keys = list(scenarios.keys())

    print()
    for i, (k, label) in enumerate(scenarios.items(), 1):
        translated_label = translate_to_native(label, current_language)
        print(f"  {i}. {translated_label}")
    print()

    choice = input("  Enter number: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(keys):
            return keys[idx]
    except (ValueError, IndexError):
        pass

    print("  Invalid choice, defaulting to doctor.")
    return "doctor"

# ──────────────────────────────────────────
# CONVERSATION MODE
# ──────────────────────────────────────────

def run_conversation(language: str, scenario_key: str):
    scenario_info = CONVERSATION_SCENARIOS[scenario_key]

    # Set the scene — tell user what's happening in their language
    scene_intro = translate_to_native(
        f"You are about to practice: {scenario_info['label']}. {scenario_info['setting']} Your goal: {scenario_info['user_goal']} Speak naturally — just like a real conversation.",
        language
    )
    speak(scene_intro)
    time.sleep(0.5)

    # Start conversation
    state, opening = start_conversation(scenario_key, language)

    print(f"\n  ══ {scenario_info['label']} ══")
    print(f"  [{scenario_info['character_short']}]: {opening}\n")

    # Speak the character's opening in English
    speak_english(opening)

    while not state["done"]:
        # User's turn
        your_turn = translate_to_native("Your turn. Speak now.", language)
        speak(your_turn)
        time.sleep(0.3)
        print("  🎙  Speak now...")

        spoken = record_and_transcribe()
        if not spoken:
            retry = translate_to_native("I didn't hear you. Please try again.", language)
            speak(retry)
            continue

        print(f"  You said: \"{spoken}\"")

        # Advance conversation
        print("  ⏳  Processing...")
        result = advance_conversation(state, spoken)

        # Show and speak character reply in English
        print(f"\n  [{scenario_info['character_short']}]: {result['character_reply']}\n")
        speak_english(result["character_reply"])
        time.sleep(0.3)

        # Show scores
        comm_stars = score_to_stars(result["communication_score"])
        pron_stars = score_to_stars(result["pronunciation_score"])
        print(f"  Communication: {result['communication_score']}/100 {comm_stars}")
        print(f"  Pronunciation: {result['pronunciation_score']}/100 {pron_stars}")

        # Pronunciation note in native language
        if result["pronunciation_note"]:
            print(f"  Note: {result['pronunciation_note']}")
            speak(result["pronunciation_note"])

        # New vocabulary
        if result["new_vocabulary"]:
            print(f"  ✓ English words you used: {', '.join(result['new_vocabulary'])}")

        print()
        time.sleep(0.5)

    # Conversation complete — summary
    print("\n  ══ Conversation Complete ══\n")
    summary = get_conversation_summary(state, language)

    print(f"  Communication score: {summary['avg_communication']}/100")
    print(f"  Pronunciation score: {summary['avg_pronunciation']}/100")
    print(f"  Overall:             {summary['overall']}/100  {score_to_stars(summary['overall'])}")
    print()

    speak(summary["closing_message"])


# ──────────────────────────────────────────
# PHRASE DRILL MODE
# ──────────────────────────────────────────

def run_phrase(phrase_data: dict, language: str, phrase_num: int, total: int, tracker: PhonemeTracker):
    phrase = phrase_data["text"]
    translation = phrase_data.get("translation", "")
    tip = phrase_data.get("tip", "")
    target_sounds = phrase_data.get("target_sounds", [])

    print(f"\n  ── Phrase {phrase_num} of {total} ──")
    print(f"  English: {phrase}")
    if translation:
        print(f"  Means:   {translation}")
    print(f"  Sounds:  {', '.join(target_sounds)}")
    print()

    if translation:
        meaning = translate_to_native("This phrase means:", language)
        speak(f"{meaning} {translation}")
        time.sleep(0.5)

    listen = translate_to_native("Now listen to the English:", language)
    speak(listen)
    time.sleep(0.3)
    speak_english(phrase)
    time.sleep(0.5)
    speak_english(phrase)

    tip_native = translate_to_native(f"Tip: {tip}", language)
    speak(tip_native)
    time.sleep(0.5)

    your_turn = translate_to_native("Now you say it. Speak after the beep.", language)
    speak(your_turn)
    time.sleep(0.3)
    print("  🎙  Speak now...")

    spoken = record_and_transcribe()
    print(f"  You said: \"{spoken}\"")

    result = score_attempt(phrase, spoken, language)
    stars = score_to_stars(result["score"])

    # Show both scores
    print(f"  Score:    {result['score']}/100  {stars}")
    print(f"  Phoneme:  {result['phoneme_score']}/100  ← pronunciation accuracy")
    print(f"  Words:    {result['word_score']}/100  ← word accuracy")

    # Feed tracker
    tracker.record(result["phoneme_mismatches"], phrase)

    score_msg = translate_to_native(f"Your score is {result['score']} out of 100.", language)
    speak(score_msg)

    if result["score"] >= 85:
        speak(translate_to_native("Excellent! That was very good.", language))
    else:
        feedback = generate_correction_feedback(
            target_phrase=phrase,
            spoken_phrase=spoken,
            language_query=language,
            mismatched_phonemes=result["phoneme_mismatches"],
            native_language=language,
        )
        print(f"\n  Coach: {feedback}\n")
        speak(feedback)

    return result["score"]


def run_drill(language: str, scenario_key: str, profile: dict):
    tracker = PhonemeTracker(language)

    memory_focus = get_focus_sounds_from_memory(profile, n=6)
    if memory_focus:
        print(f"\n  🧠 Resuming from last session — focusing on: {' '.join('/' + p + '/' for p in memory_focus)}\n")

    print("\n  ⏳  Generating your lesson...")
    speak(translate_to_native("One moment while I prepare your lesson.", language))

    lesson = generate_lesson(
        language, scenario_key, num_phrases=5,
        focus_sounds=memory_focus or None
    )
    print(f"\n  Lesson ready: {lesson['scenario']} — {language}")
    speak(translate_to_native(
        f"Your lesson is ready. We will practice {len(lesson['phrases'])} English phrases.",
        language
    ))
    time.sleep(0.5)

    scores = []
    seen = []
    for i, phrase_data in enumerate(lesson["phrases"], 1):
        score = run_phrase(phrase_data, language, i, len(lesson["phrases"]), tracker)
        scores.append(score)
        seen.append(phrase_data["text"])
        time.sleep(1)

        if i == 3:
            focus = get_adaptive_focus(tracker, num_sounds=5)
            if focus:
                print(f"\n  🎯 Adapting: {', '.join('/' + p + '/' for p in focus)}\n")

    avg = int(sum(scores) / len(scores))
    print(f"\n  ══ Lesson Complete ══")
    print(f"  Average score: {avg}/100  {score_to_stars(avg)}")

    # Save to memory
    updated = update_memory_from_tracker(profile, tracker)
    save_memory(language, updated)
    print(f"  💾 Progress saved.")

    print_session_heatmap(tracker)

    speak(translate_to_native(f"Lesson complete! Your average score was {avg} out of 100.", language))

    top = tracker.top_struggles(2)
    if top and avg < 85:
        struggle_str = " and ".join(f"/{p}/" for p in top)
        speak(translate_to_native(f"Keep practicing the {struggle_str} sounds. You are improving!", language))
    elif avg >= 80:
        speak(translate_to_native("You did a wonderful job today. Keep practicing your English!", language))
    else:
        speak(translate_to_native("Do not give up. Every session makes you stronger. Try again tomorrow.", language))

# ──────────────────────────────────────────
# Main
# ──────────────────────────────────────────

def main():
    if "--server" in sys.argv:
        import uvicorn
        print("🚀 Starting FastAPI Server...")
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
        return

    clear()
    banner()

    try:
        language, profile = pick_language()  # ← unpack tuple
        clear(); banner()
        mode = pick_mode()
        clear(); banner()
        scenario = pick_scenario(mode)
        clear(); banner()

        if mode == "conversation":
            run_conversation(language, scenario)
        else:
            run_drill(language, scenario, profile)  # ← pass profile

    except KeyboardInterrupt:
        print("\n\n  Goodbye!")
        speak_english("Goodbye. Keep practicing your English!")
        sys.exit(0)


if __name__ == "__main__":
    main()