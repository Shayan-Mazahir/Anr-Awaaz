import os
import tempfile
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from lessons import generate_lesson, generate_correction_feedback, list_scenarios, translate_to_native
from conversation import start_conversation, advance_conversation, get_conversation_summary, list_conversation_scenarios, CONVERSATION_SCENARIOS
from phonemes import find_language, get_dialects
from scorer import score_attempt, score_to_stars
from analyzer import transcribe

app = FastAPI(title="Pronunciation Coach API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory conversation states
conversation_states = {}

# ── ElevenLabs TTS ──
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
el_client = ElevenLabs(api_key=ELEVENLABS_API_KEY) if ELEVENLABS_API_KEY else None
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Bella


class TTSRequest(BaseModel):
    text: str

class LessonRequest(BaseModel):
    language: str
    scenario: str

class ConversationStartRequest(BaseModel):
    scenario: str
    language: str

class ConversationTurnRequest(BaseModel):
    session_id: str
    spoken_text: str


@app.get("/")
def root():
    return FileResponse("static/index.html")


@app.get("/api/setup")
def get_setup():
    return {
        "scenarios": list_scenarios(),
        "conversation_scenarios": list_conversation_scenarios(),
        "common_languages": [
            "Arabic", "Urdu", "Somali", "French", "Spanish",
            "Pashto", "Dari", "Swahili", "Hindi", "Bengali",
            "Tigrinya", "Amharic", "Turkish", "Vietnamese"
        ]
    }


@app.get("/api/dialects/{language}")
def get_dialects_for_language(language: str):
    dialects = get_dialects(language)
    name = find_language(language)
    return {"language": name, "dialects": dialects}


@app.post("/api/tts")
def generate_tts(req: TTSRequest):
    if not el_client:
        raise HTTPException(status_code=500, detail="ElevenLabs not configured")
    try:
        audio_gen = el_client.text_to_speech.convert(
            voice_id=VOICE_ID,
            output_format="mp3_44100_128",
            text=req.text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75, style=0.0, use_speaker_boost=True),
        )
        audio_bytes = b"".join(list(audio_gen))
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/translate")
def translate(language: str = Form(...), text: str = Form(...)):
    result = translate_to_native(text, language)
    return {"translation": result}


@app.post("/api/lesson")
def create_lesson(req: LessonRequest):
    try:
        lesson = generate_lesson(req.language, req.scenario, num_phrases=5)
        return lesson
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/score")
async def score_audio(
    target_phrase: str = Form(...),
    language: str = Form(...),
    audio: UploadFile = File(...)
):
    suffix = ".webm" if "webm" in (audio.content_type or "") else ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Pass the target phrase as context so Whisper knows what words to expect
        spoken_text = transcribe(tmp_path, model_size="small", context=target_phrase)
        if not spoken_text or not spoken_text.strip():
            return {
                "score": 0, "phoneme_score": 0, "word_score": 0,
                "spoken": "", "target": target_phrase,
                "feedback": "I couldn't hear you clearly. Make sure your microphone is on and try speaking a little louder.",
                "stars": "☆☆☆☆☆", "matched_words": [], "missed_words": [],
                "phoneme_mismatches": []
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
                native_language=language,
            )

        return {
            "score": result["score"],
            "phoneme_score": result.get("phoneme_score", result["score"]),
            "word_score": result.get("word_score", result["score"]),
            "spoken": spoken_text,
            "target": target_phrase,
            "feedback": feedback,
            "stars": score_to_stars(result["score"]),
            "matched_words": result["matched_words"],
            "missed_words": result["missed_words"],
            "phoneme_mismatches": [
                {"word": m["word"], "ipa": m.get("target_ipa", m.get("ipa", "")), "is_gap": m.get("is_language_gap", False)}
                for m in result["phoneme_mismatches"][:5]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/conversation/start")
def start_conv(req: ConversationStartRequest):
    import uuid
    session_id = str(uuid.uuid4())
    state, opening = start_conversation(req.scenario, req.language)
    conversation_states[session_id] = state
    scenario_info = CONVERSATION_SCENARIOS[req.scenario]
    return {
        "session_id": session_id,
        "opening": opening,
        "character": scenario_info["character_short"],
        "setting": scenario_info["setting"],
        "goal": scenario_info["user_goal"],
    }


@app.post("/api/conversation/turn")
def conversation_turn(req: ConversationTurnRequest):
    state = conversation_states.get(req.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    result = advance_conversation(state, req.spoken_text)

    if result["done"]:
        summary = get_conversation_summary(state, state["language"])
        result["summary"] = summary
        del conversation_states[req.session_id]

    return result


@app.post("/api/conversation/score_audio")
async def score_conv_audio(
    session_id: str = Form(...),
    audio: UploadFile = File(...)
):
    suffix = ".webm" if "webm" in (audio.content_type or "") else ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        audio_bytes = await audio.read()
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # Build context from the last 2 character lines in this conversation.
        # Passing this to Whisper dramatically improves accuracy for short/accented
        # responses — if the teacher just said "reading and math", Whisper is far
        # more likely to correctly hear "his reading" instead of "can you try".
        context = ""
        state = conversation_states.get(session_id)
        if state and state.get("history"):
            char_lines = [h["text"] for h in state["history"] if h["role"] == "character"][-2:]
            context = " ".join(char_lines)

        spoken_text = transcribe(tmp_path, model_size="small", context=context)

        if not spoken_text or not spoken_text.strip():
            return {"spoken_text": "", "unclear": True}

        return {"spoken_text": spoken_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)