import wave
import tempfile
import os
import struct
import math


def _rms(data: bytes) -> float:
    """Calculate RMS (volume level) of an audio chunk."""
    count = len(data) // 2
    if count == 0:
        return 0.0
    shorts = struct.unpack(f"{count}h", data)
    sum_sq = sum(s * s for s in shorts)
    return math.sqrt(sum_sq / count)


def _stereo_to_mono(data: bytes) -> bytes:
    """Convert stereo interleaved 16-bit PCM to mono by averaging channels."""
    shorts = struct.unpack(f"{len(data)//2}h", data)
    mono = []
    for i in range(0, len(shorts), 2):
        avg = (shorts[i] + shorts[i + 1]) // 2
        mono.append(avg)
    return struct.pack(f"{len(mono)}h", *mono)


def _downsample(data: bytes, from_rate: int, to_rate: int) -> bytes:
    """Simple decimation downsample (e.g. 44100 → 16000)."""
    if from_rate == to_rate:
        return data
    shorts = struct.unpack(f"{len(data)//2}h", data)
    ratio = from_rate / to_rate
    out = []
    i = 0.0
    while int(i) < len(shorts):
        out.append(shorts[int(i)])
        i += ratio
    return struct.pack(f"{len(out)}h", *out)


def _calibrate_threshold(stream, chunk: int, sample_rate: int) -> int:
    """
    Measure ambient noise for 1 second and set threshold at 3x that level.
    Adapts automatically to quiet rooms and noisy hackathon environments.
    """
    print("  📡  Calibrating mic...", end="", flush=True)
    noise_levels = []
    num_chunks = int(sample_rate / chunk * 1.0)  # 1 second worth
    for _ in range(num_chunks):
        data = stream.read(chunk, exception_on_overflow=False)
        mono = _stereo_to_mono(data)
        noise_levels.append(_rms(mono))
    avg_noise = sum(noise_levels) / len(noise_levels)
    # Don't multiply — just add a fixed margin above noise floor
    threshold = int(avg_noise + 3000)  # speech is roughly 3000 RMS above noise
    threshold = max(threshold, 500)
    print(f" done (noise={int(avg_noise)}, threshold={threshold})")
    return threshold


def record_audio(
    silence_duration: float = 1.5,   # seconds of silence before stopping
    max_duration: float = 15.0,      # hard cap — never record longer than this
    min_duration: float = 0.8,       # always record at least this long
    duration: int = None,            # legacy param — ignored
) -> str:
    """
    Record from microphone until the user stops speaking.

    - Auto-calibrates silence threshold based on room noise
    - Captures stereo at 44100Hz (required by ALC256/Intel PCH)
    - Converts to mono 16kHz WAV for Whisper
    - No fixed timer — stops automatically on silence
    """
    try:
        import pyaudio
    except ImportError:
        raise RuntimeError("pyaudio not installed. Run: pip install pyaudio")

    CAPTURE_RATE = 44100   # ALC256 requires stereo at 44100
    TARGET_RATE = 16000    # Whisper works best at 16kHz
    CHANNELS = 2           # stereo capture
    CHUNK = 2048
    FORMAT = pyaudio.paInt16

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=CAPTURE_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    # Auto-calibrate to room noise
    threshold = _calibrate_threshold(stream, CHUNK, CAPTURE_RATE)

    print("  🎙  Listening... (speak now, pause when done)")

    frames = []
    silent_chunks = 0
    speaking_started = False
    chunks_per_second = CAPTURE_RATE / CHUNK
    max_chunks = int(max_duration * chunks_per_second)
    min_chunks = int(min_duration * chunks_per_second)
    silence_chunks_needed = int(silence_duration * chunks_per_second)

    for i in range(max_chunks):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

        mono_data = _stereo_to_mono(data)
        volume = _rms(mono_data)

        if volume > threshold:
            speaking_started = True
            silent_chunks = 0
            print("▮", end="", flush=True)
        else:
            if speaking_started:
                silent_chunks += 1
                print("·", end="", flush=True)

        # Stop: speech detected + silence long enough + min duration met
        if speaking_started and silent_chunks >= silence_chunks_needed and i >= min_chunks:
            break

    print()
    print("  ✓  Got it.")

    stream.stop_stream()
    stream.close()
    pa.terminate()

    # Convert stereo 44100 → mono 16000 for Whisper
    all_data = b"".join(frames)
    mono = _stereo_to_mono(all_data)
    resampled = _downsample(mono, CAPTURE_RATE, TARGET_RATE)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)       # 16-bit
        wf.setframerate(TARGET_RATE)
        wf.writeframes(resampled)

    return tmp.name


def cleanup(path: str):
    """Delete a temporary audio file."""
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass