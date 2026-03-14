import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from fastapi.responses import Response

# Import original logic
from lessons import list_scenarios, generate_lesson, generate_correction_feedback
from phonemes import find_language
from scorer import score_attempt
from analyzer import transcribe

load_dotenv()

app = FastAPI(title="Pronunciation Coach API")

# Setup CORS to allow React frontend (defaulting to localhost:5173 for Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for hackathon, restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ElevenLabs Client
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY) if ELEVENLABS_API_KEY else None

class LessonRequest(BaseModel):
    language: str
    scenario: str

class TTSRequest(BaseModel):
    text: str

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
        # Adam is a very common premade voice
        voice_id = "pNInz6obpgnuMvkhW4A5" 
        audio_generator = elevenlabs_client.text_to_speech.convert(
            voice_id=voice_id,
            output_format="mp3_44100_128",
            text=req.text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
            ),
        )
        audio_bytes = b"".join(list(audio_generator))
        print("TTS generated successfully.")
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
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Transcribe
        spoken_text = transcribe(tmp_path, model_size="base")
        
        # Check if transcription failed or empty
        if not spoken_text.strip():
             return {
                "score": 0,
                "spoken": "",
                "target": target_phrase,
                "feedback": "I couldn't hear anything. Please try speaking closer to the microphone.",
                "stars": "☆☆☆☆☆"
             }

        # Score
        result = score_attempt(target_phrase, spoken_text, language)
        
        # Feedback
        if result["score"] >= 85:
            feedback = "Excellent! That was very good."
        else:
            feedback = generate_correction_feedback(
                target_phrase=target_phrase,
                spoken_phrase=spoken_text,
                language_query=language,
                mismatched_phonemes=result["phoneme_mismatches"],
            )

        # Build response
        def score_to_stars(score: int) -> str:
            if score >= 90: return "★★★★★"
            elif score >= 75: return "★★★★☆"
            elif score >= 60: return "★★★☆☆"
            elif score >= 40: return "★★☆☆☆"
            else: return "★☆☆☆☆"

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
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
