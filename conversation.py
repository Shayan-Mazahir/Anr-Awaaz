"""
conversation.py — Scenario-based conversation engine.

Instead of repeating fixed phrases, the user has a real back-and-forth
conversation with a character (doctor, cashier, interviewer, landlord).

Claude plays the character AND evaluates communication + pronunciation simultaneously.
"""

import anthropic
import json
import os
from dotenv import load_dotenv
from phonemes import find_language, get_language_gaps, CMU_TO_IPA, get_phrase_phonemes

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ──────────────────────────────────────────
# Scenario definitions
# Each scenario has a character, setting, goal, and opening line
# ──────────────────────────────────────────

CONVERSATION_SCENARIOS = {
    "doctor": {
        "label": "Doctor's Office",
        "character": "Dr. Smith, a friendly family doctor",
        "character_short": "Doctor",
        "setting": "You are at a doctor's office. You have a headache and fever.",
        "user_goal": "Describe your symptoms, get a diagnosis, and understand the prescription.",
        "opening": "Hello! Come on in. I'm Doctor Smith. What brings you in today?",
        "min_turns": 4,
        "max_turns": 7,
        "end_condition": "prescription given or appointment concluded",
        "vocabulary": ["headache", "fever", "medicine", "appointment", "prescription", "pain", "symptoms"],
    },
    "grocery": {
        "label": "Grocery Store",
        "character": "Maria, a helpful grocery store employee",
        "character_short": "Cashier",
        "setting": "You are at a grocery store. You need to find bread and pay for your items.",
        "user_goal": "Find an item, ask about the price, and complete a purchase.",
        "opening": "Hi there! Welcome. Can I help you find something today?",
        "min_turns": 3,
        "max_turns": 5,
        "end_condition": "purchase completed",
        "vocabulary": ["bread", "price", "aisle", "total", "change", "receipt", "discount"],
    },
    "job_interview": {
        "label": "Job Interview",
        "character": "Mr. Johnson, a hiring manager at a warehouse",
        "character_short": "Interviewer",
        "setting": "You are in a job interview for a warehouse position.",
        "user_goal": "Introduce yourself, explain your experience, and ask about the job.",
        "opening": "Good morning! Please have a seat. Thank you for coming in today. Can you start by telling me a little about yourself?",
        "min_turns": 4,
        "max_turns": 6,
        "end_condition": "interview concluded with next steps discussed",
        "vocabulary": ["experience", "schedule", "salary", "position", "reference", "available", "skills"],
    },
    "school": {
        "label": "School Meeting",
        "character": "Ms. Thompson, a primary school teacher",
        "character_short": "Teacher",
        "setting": "You are meeting your child's teacher at school.",
        "user_goal": "Ask about your child's progress and understand homework requirements.",
        "opening": "Hello! You must be Omar's parent. Thank you for coming in. Please sit down. How are you today?",
        "min_turns": 4,
        "max_turns": 6,
        "end_condition": "parent has understood child's progress and next steps",
        "vocabulary": ["homework", "progress", "reading", "grade", "schedule", "help", "improve"],
    },
    "emergency": {
        "label": "Emergency Call",
        "character": "911 operator named Sarah",
        "character_short": "Operator",
        "setting": "You need to call 911. Someone at home is injured.",
        "user_goal": "Describe the emergency, give your address, and follow instructions.",
        "opening": "911, what is your emergency?",
        "min_turns": 3,
        "max_turns": 5,
        "end_condition": "address confirmed and help dispatched",
        "vocabulary": ["address", "ambulance", "emergency", "injured", "breathing", "fire", "help"],
    },
    "housing": {
        "label": "Talking to Landlord",
        "character": "Mr. Davis, your apartment landlord",
        "character_short": "Landlord",
        "setting": "You are calling your landlord about a problem in your apartment.",
        "user_goal": "Report a maintenance issue (broken heating) and arrange for it to be fixed.",
        "opening": "Hello, this is Mr. Davis. How can I help you?",
        "min_turns": 3,
        "max_turns": 5,
        "end_condition": "repair scheduled",
        "vocabulary": ["heating", "broken", "cold", "repair", "urgent", "apartment", "fixed"],
    },
}


def _get_phoneme_issues(text: str, language_name: str) -> list[str]:
    """
    Find which sounds in a spoken text are likely hard for this speaker.
    Returns a short list of IPA symbols.
    """
    gaps = get_language_gaps(language_name)
    phrase_phonemes = get_phrase_phonemes(text)
    issues = []
    for word, cmu_list in phrase_phonemes.items():
        for cmu in cmu_list:
            base = cmu.rstrip("012")
            ipa = CMU_TO_IPA.get(base)
            if ipa and ipa in gaps and ipa not in issues:
                issues.append(ipa)
    return issues[:3]  # top 3 max


def start_conversation(scenario_key: str, language_name: str) -> dict:
    """
    Initialize a conversation state.
    Returns the opening line and initial state dict.
    """
    scenario = CONVERSATION_SCENARIOS.get(scenario_key)
    if not scenario:
        raise ValueError(f"Unknown scenario: {scenario_key}")

    state = {
        "scenario_key": scenario_key,
        "scenario": scenario,
        "language": language_name,
        "history": [],          # list of {role, text}
        "turn": 0,
        "done": False,
        "scores": [],
        "phoneme_issues_seen": set(),
    }

    # Add opening line to history
    opening = scenario["opening"]
    state["history"].append({"role": "character", "text": opening})

    return state, opening


def advance_conversation(state: dict, user_said: str) -> dict:
    """
    Given what the user said, advance the conversation.

    Returns:
    {
        "character_reply": str,       # what the character says next
        "pronunciation_note": str,    # short note in native language about their pronunciation
        "communication_score": int,   # 0-100: did they get their point across?
        "pronunciation_score": int,   # 0-100: how was their pronunciation
        "done": bool,                 # is the conversation over?
        "new_vocabulary": [str],      # English words they used correctly this turn
    }
    """
    scenario = state["scenario"]
    language = state["language"]
    turn = state["turn"] + 1

    # Build conversation history for Claude
    history_str = "\n".join(
        f"{'[Character]' if h['role'] == 'character' else '[User]'}: {h['text']}"
        for h in state["history"]
    )

    # Find phoneme issues in what they said
    phoneme_issues = _get_phoneme_issues(user_said, language)

    is_last_turn = turn >= scenario["max_turns"]
    should_end = turn >= scenario["min_turns"]

    # Detect if the transcription looks like garbled noise rather than real speech.
    # Heuristic: very short, or contains no recognisable English words at all.
    words_spoken = user_said.strip().split()
    speech_seems_unclear = len(words_spoken) <= 1 or (
        len(words_spoken) <= 3 and not any(w in [
            "i", "a", "the", "to", "is", "my", "me", "hi", "hello", "yes", "no",
            "help", "need", "want", "have", "can", "please", "thank", "okay", "ok",
            "where", "what", "how", "who", "when", "why", "do", "are", "you",
        ] for w in words_spoken)
    )

    prompt = f"""You are running a language learning conversation simulation.

CHARACTER: {scenario['character']}
SETTING: {scenario['setting']}
USER GOAL: {scenario['user_goal']}
END CONDITION: {scenario['end_condition']}

The user's native language is: {language}
This is turn {turn} of {scenario['max_turns']} maximum.
{"This is the FINAL turn — wrap up the conversation naturally." if is_last_turn else ""}
{"The conversation can end if the goal has been achieved." if should_end else "Continue the conversation."}

Conversation so far:
{history_str}
[User]: {user_said}

{"⚠️ IMPORTANT: The user's speech above looks garbled or was unclear (possibly a microphone issue or they are still learning). Do NOT penalise them harshly. Have the character politely ask them to repeat or offer helpful prompts. Set communication_score to 40 and pronunciation_score to 40 minimum — we cannot fairly score unclear audio." if speech_seems_unclear else ""}

Respond with a JSON object (no markdown, no preamble):
{{
  "character_reply": "what {scenario['character_short']} says next, in character, 1-2 sentences max, simple vocabulary. If speech was unclear, kindly ask them to repeat or offer a simple yes/no question to help.",
  "communication_success": true/false,
  "communication_note": "one sentence: did the user successfully communicate their point? be specific. If audio was unclear, say so gently.",
  "pronunciation_feedback": "one warm sentence in {language} about their pronunciation — pick the most important thing to fix from these sounds they struggle with: {', '.join(phoneme_issues) if phoneme_issues else 'no major issues detected'}. If speech was unclear or too short to judge, give general encouragement only in {language}.",
  "communication_score": 0-100,
  "pronunciation_score": 0-100,
  "conversation_complete": true/false,
  "new_vocabulary": ["english", "words", "they", "used", "correctly"]
}}

Rules:
- character_reply must sound natural, like a real person in that role
- Keep character speech simple — this is a language learner
- communication_score: 100 = perfectly clear, 0 = completely unclear. NEVER go below 40 if speech was simply hard to hear.
- pronunciation_score: 100 = native-like, 0 = incomprehensible. NEVER go below 40 for unclear/short audio.
- pronunciation_feedback MUST be in {language} script
- conversation_complete = true only if the user's goal is achieved or max turns reached"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)

    # Update state
    state["history"].append({"role": "user", "text": user_said})
    state["history"].append({"role": "character", "text": result["character_reply"]})
    state["turn"] = turn
    state["scores"].append({
        "communication": result["communication_score"],
        "pronunciation": result["pronunciation_score"],
    })
    state["done"] = result.get("conversation_complete", False) or is_last_turn

    return {
        "character_reply": result["character_reply"],
        "pronunciation_note": result["pronunciation_feedback"],
        "communication_score": result["communication_score"],
        "pronunciation_score": result["pronunciation_score"],
        "communication_note": result.get("communication_note", ""),
        "done": state["done"],
        "new_vocabulary": result.get("new_vocabulary", []),
    }


def get_conversation_summary(state: dict, native_language: str) -> dict:
    """
    Generate a final summary of the conversation.
    Returns scores and a motivating closing message in native language.
    """
    scores = state["scores"]
    if not scores:
        return {"avg_communication": 0, "avg_pronunciation": 0, "message": ""}

    avg_comm = int(sum(s["communication"] for s in scores) / len(scores))
    avg_pron = int(sum(s["pronunciation"] for s in scores) / len(scores))
    overall = int((avg_comm + avg_pron) / 2)

    # Recap the conversation in a useful way
    history_str = "\n".join(
        f"{'Character' if h['role'] == 'character' else 'You'}: {h['text']}"
        for h in state["history"]
    )

    scenario = state["scenario"]
    vocab_used = list(set(
        word
        for turn_data in scores
        for word in []  # placeholder — vocab tracked per turn
    ))

    prompt = f"""A refugee just completed an English conversation practice session.

Scenario: {scenario['label']}
Their native language: {native_language}
Communication score: {avg_comm}/100
Pronunciation score: {avg_pron}/100

Conversation:
{history_str}

Write a SHORT closing message in {native_language} (use actual {native_language} script) that:
1. Celebrates what they did well (be specific — mention something from the conversation)
2. Names ONE thing to keep practicing
3. Ends with encouragement

2-3 sentences max. Output only the message, nothing else."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )

    closing = response.content[0].text.strip()

    return {
        "avg_communication": avg_comm,
        "avg_pronunciation": avg_pron,
        "overall": overall,
        "closing_message": closing,
    }


def list_conversation_scenarios() -> dict:
    return {k: v["label"] for k, v in CONVERSATION_SCENARIOS.items()}