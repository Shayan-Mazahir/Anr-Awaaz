import anthropic
import json
import os
from dotenv import load_dotenv
from phonemes import find_language, get_language_gaps

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SCENARIOS = {
    "doctor": {
        "label": "Doctor's Office",
        "context": "visiting a doctor, describing symptoms, asking about medication, scheduling appointments",
    },
    "grocery": {
        "label": "Grocery Store",
        "context": "shopping for food, asking for help finding items, checking prices, paying at checkout",
    },
    "job_interview": {
        "label": "Job Interview",
        "context": "introducing yourself, describing your experience, answering common interview questions",
    },
    "school": {
        "label": "School / Parent Meeting",
        "context": "talking to teachers, understanding school schedules, asking about your child's progress",
    },
    "emergency": {
        "label": "Emergency Services",
        "context": "calling 911, describing an emergency, giving your address, asking for help",
    },
    "housing": {
        "label": "Housing / Landlord",
        "context": "renting an apartment, reporting maintenance issues, understanding a lease",
    },
}


def _gaps_to_ipa_list(language_name: str) -> list:
    gaps = get_language_gaps(language_name)
    return sorted(list(gaps))[:20]


def generate_lesson(
    language_query: str,
    scenario_key: str,
    num_phrases: int = 5,
    previously_seen: list = None,
    focus_sounds: list = None,
) -> dict:
    """
    Generate a lesson.
    focus_sounds: IPA phonemes to prioritize (from session tracker / memory).
    If None, falls back to full gap list for this language.
    """
    language_name = find_language(language_query) or "English"
    scenario = SCENARIOS.get(scenario_key)
    if not scenario:
        raise ValueError(f"Scenario '{scenario_key}' not found.")

    # Fallback if no API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        fallback_phrases = [
            {
                "text": "I need to see a doctor",
                "translation": "أحتاج لرؤية طبيب",
                "target_sounds": ["ð", "ɹ"],
                "tip": "For 'the', place your tongue between your teeth and push air through."
            },
            {
                "text": "Where is the pharmacy",
                "translation": "أين الصيدلية؟",
                "target_sounds": ["f", "ɹ", "m"],
                "tip": "Put your top teeth on your bottom lip for the 'f' sound."
            },
            {
                "text": "I have an appointment at ten",
                "translation": "عندي موعد في الساعة العاشرة",
                "target_sounds": ["p", "t", "n"],
                "tip": "Make a small puff of air when you say the 'p' in appointment."
            },
            {
                "text": "Can you speak more slowly",
                "translation": "هل يمكنك التحدث ببطء أكثر؟",
                "target_sounds": ["k", "s", "l"],
                "tip": "Keep your tongue low in your mouth for the 'l' sounds."
            },
            {
                "text": "Thank you for your help",
                "translation": "شكرا لك على مساعدتك",
                "target_sounds": ["θ", "h", "p"],
                "tip": "Blow air out softly for the 'th' sound in Thank."
            }
        ]
        return {
            "language": language_name,
            "scenario": scenario["label"],
            "phrases": fallback_phrases[:num_phrases],
            "focus_sounds": [],
        }

    # Adaptive: use focus sounds from tracker/memory if available
    if focus_sounds:
        gap_ipa = focus_sounds[:8]
        adaptive_note = (
            f"PRIORITY: Focus especially on these sounds the learner is currently struggling with: "
            f"{', '.join(gap_ipa)}\n"
            f"Still use other gap sounds if needed, but prioritize the above."
        )
    else:
        gap_ipa = _gaps_to_ipa_list(language_name)
        adaptive_note = ""

    previously_seen_str = json.dumps(previously_seen or [])

    prompt = f"""You are an English teacher and pronunciation coach for refugees.

The learner's native language/dialect is: {language_name}
Their practice scenario is: {scenario['label']} — {scenario['context']}

English phonemes that do NOT exist in {language_name} (these are hard for this learner):
{', '.join(gap_ipa) if gap_ipa else 'No major gaps detected — focus on natural useful phrases.'}

{adaptive_note}

Your task: Generate exactly {num_phrases} English phrases for this scenario.

Each phrase must:
1. Be SHORT (4–8 words), realistic, immediately useful in the scenario
2. Naturally contain at least one of the difficult phonemes above
3. Use simple everyday vocabulary — no idioms, no complex grammar
4. Come with a translation in {language_name} (the actual script — e.g. Arabic script for Arabic)
5. Come with ONE physical pronunciation tip in plain English
6. NOT repeat these phrases: {previously_seen_str}

The translation is crucial — it teaches the learner what the English phrase MEANS.
The learner hears: translation first (so they understand) → English phrase (so they learn to say it).

Respond ONLY with a JSON array. No preamble, no markdown backticks. Example:
[
  {{
    "text": "I need to see a doctor",
    "translation": "مجھے ڈاکٹر سے ملنا ہے",
    "target_sounds": ["ð", "ɹ"],
    "tip": "For 'the', place your tongue between your teeth and push air through"
  }}
]

Rules for tips:
- One sentence only
- Physical, actionable (tongue position, lip shape, airflow)
- Never say 'try to' — give a direct instruction
- Write the tip in plain English (it will be translated and spoken to the learner)"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    phrases = json.loads(raw)

    return {
        "language": language_name,
        "scenario": scenario["label"],
        "phrases": phrases,
        "focus_sounds": focus_sounds or gap_ipa,
    }


# ──────────────────────────────────────────
# Fast translation — Google Translate + cache
# ──────────────────────────────────────────

LANG_TO_GOOGLE = {
    "Arabic": "ar", "Egyptian Arabic": "ar", "Moroccan Arabic": "ar",
    "Lebanese Arabic": "ar", "Najdi Arabic": "ar",
    "Urdu": "ur", "Hindi": "hi", "Hindi-Urdu": "ur",
    "French": "fr", "Spanish": "es", "Somali": "so",
    "Swahili": "sw", "Amharic": "am", "Pashto": "ps",
    "Southwestern Pashto": "ps", "Northwestern Pashto": "ps",
    "Yousafzai Pashto": "ps", "Persian": "fa", "Farsi": "fa",
    "Dari": "fa", "Turkish": "tr", "Bengali": "bn",
    "Nepali": "ne", "Vietnamese": "vi", "Ukrainian": "uk",
    "Romanian": "ro", "Tigrinya": "ti", "Tamil": "ta",
    "Telugu": "te", "Burmese": "my", "Sinhala": "si",
}

_translation_cache: dict = {}


def translate_to_native(text: str, language_name: str) -> str:
    """
    Fast translation using Google Translate with in-memory caching.
    ~100ms vs 2-3s for Claude API calls.
    Falls back to English if language unsupported or network fails.
    """
    if language_name == "English":
        return text

    cache_key = f"{language_name}:{text}"
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]

    lang_code = LANG_TO_GOOGLE.get(language_name)
    if not lang_code:
        return text

    try:
        from deep_translator import GoogleTranslator
        result = GoogleTranslator(source="en", target=lang_code).translate(text)
        _translation_cache[cache_key] = result
        return result
    except Exception as e:
        print(f"  ⚠  Translation failed ({language_name}): {e}")
        return text


def prewarm_translations(language_name: str):
    """
    Pre-translate all common UI strings right after language is picked.
    Makes the rest of the session feel instant — hits cache for everything after.
    """
    common = [
        "This phrase means:",
        "Now listen to the English:",
        "Now you say it. Speak after the beep.",
        "Your turn. Speak now.",
        "One moment while I prepare your lesson.",
        "Excellent! That was very good.",
        "You did a wonderful job today. Keep practicing your English!",
        "Do not give up. Every session makes you stronger. Try again tomorrow.",
        "How would you like to practice? Choose a number.",
        "Which situation would you like to practice? Choose a number.",
        "Conversation — have a real conversation with a character",
        "Phrase Drilling — practice specific phrases one by one",
        "Tip:",
        "I did not hear you. Please try again.",
        "Your score is",
        "Lesson complete!",
    ]
    print("  ⏳  Loading translations...", end="", flush=True)
    for s in common:
        translate_to_native(s, language_name)
    print(" ✓")


# ──────────────────────────────────────────
# AI correction feedback
# ──────────────────────────────────────────

def generate_correction_feedback(
    target_phrase: str,
    spoken_phrase: str,
    language_query: str,
    mismatched_phonemes: list,
    native_language: str = "English",
) -> str:
    """
    Generate warm, specific correction in the learner's native language.
    Falls back to static tip if no API key.
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        if mismatched_phonemes:
            m = mismatched_phonemes[0]
            return f"Good try! For the word '{m['word']}', pay attention to the /{m['ipa']}/ sound. Say it slowly."
        return "Nice effort. Try to speak a little more clearly next time."

    language_name = find_language(language_query) or language_query

    if mismatched_phonemes:
        top = sorted(
            mismatched_phonemes,
            key=lambda x: (not x.get("is_language_gap", False), x.get("similarity", 1.0))
        )[:3]
        mismatch_str = "Sound mismatches (worst first):\n" + "\n".join(
            f"  - /{m['target_ipa']}/ in '{m['word']}'"
            + (f" → they said /{m['spoken_ipa']}/" if m.get("spoken_ipa") else " → missing")
            + (" [known gap for this language]" if m.get("is_language_gap") else "")
            for m in top
        )
    else:
        mismatch_str = "No significant phoneme mismatches."

    respond_in = native_language if native_language != "English" else "English"

    prompt = f"""You are a warm, encouraging English pronunciation coach for a refugee.
Native language/dialect: {language_name}

Target: "{target_phrase}"
They said: "{spoken_phrase}"

{mismatch_str}

Respond in {respond_in} (use actual {respond_in} script).

2-3 sentences:
- Start positive
- Name ONE sound to fix (the most important)
- Give physical instruction (tongue/lip position)
- End with the corrected word in context

Warm, precise, no bullet points."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def list_scenarios() -> dict:
    return {k: v["label"] for k, v in SCENARIOS.items()}


if __name__ == "__main__":
    print("Testing lessons.py...\n")
    lesson = generate_lesson("Egyptian Arabic", "doctor", num_phrases=2)
    print(f"Language: {lesson['language']}")
    print(f"Scenario: {lesson['scenario']}\n")
    for i, p in enumerate(lesson["phrases"], 1):
        print(f"Phrase {i}: {p['text']}")
        print(f"  Translation: {p['translation']}")
        print(f"  Targets: {', '.join(p['target_sounds'])}")
        print(f"  Tip: {p['tip']}\n")