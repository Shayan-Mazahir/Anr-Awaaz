def transcribe(audio_path: str, model_size: str = "base", context: str = "") -> str:
    """
    Transcribe a .wav file using OpenAI Whisper.
    model_size: "tiny" (fastest) | "base" | "small" | "medium"
    context: recent conversation text (last 1-2 character lines) to bias Whisper
             toward words already in play — huge help for short/accented phrases.

    Returns the transcribed text, lowercased and stripped.
    Returns empty string if Whisper thinks there's no real speech.
    """
    try:
        import whisper
    except ImportError:
        raise RuntimeError("whisper not installed. Run: pip install openai-whisper")

    model = whisper.load_model(model_size)

    # Combining a speaker description with recent conversation context is the most
    # effective Whisper prompt strategy for accented/broken speech.
    # e.g. if the teacher just said "reading and math", Whisper will correctly
    # hear "his reading" instead of mishearing it as "can you try".
    base = "Non-native English speaker with a strong accent practicing conversational English."
    prompt = f"{base} {context.strip()}" if context.strip() else base

    result = model.transcribe(
        audio_path,
        language="en",
        fp16=False,
        initial_prompt=prompt,
        temperature=0,
        best_of=1,
        beam_size=5,
        condition_on_previous_text=False,
    )

    # Reject if Whisper itself isn't confident there's real speech.
    segments = result.get("segments", [])
    if segments:
        avg_no_speech = sum(s.get("no_speech_prob", 0.0) for s in segments) / len(segments)
        if avg_no_speech > 0.6:
            return ""

    text = result["text"].strip().lower()
    if len(text.split()) < 1:
        return ""

    return text