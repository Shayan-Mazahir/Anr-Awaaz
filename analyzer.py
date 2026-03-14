def transcribe(audio_path: str, model_size: str = "base") -> str:
    """
    Transcribe a .wav file using OpenAI Whisper.
    model_size: "tiny" (fastest) | "base" | "small" | "medium"

    Returns the transcribed text, lowercased and stripped.
    """
    try:
        import whisper
    except ImportError:
        raise RuntimeError("whisper not installed. Run: pip install openai-whisper")

    model = whisper.load_model(model_size)
    # result = model.transcribe(audio_path, language="en", fp16=False)
    result = model.transcribe(audio_path, language="en", fp16=False)
    return result["text"].strip().lower()