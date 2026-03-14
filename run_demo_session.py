#!/usr/bin/env python3
"""
Automated demo session - simulates a full pronunciation coaching session
without requiring microphone or keyboard input
"""

import time
from lessons import generate_lesson, generate_correction_feedback
from scorer import score_attempt, score_to_stars

def print_banner():
    print("""
╔═══════════════════════════════════════════════╗
║        PRONUNCIATION COACH                    ║
║        For New Arrivals Learning English      ║
╚═══════════════════════════════════════════════╝
""")

def simulate_session():
    print_banner()

    # Simulated user choices
    language = "Arabic"
    scenario = "doctor"

    print(f"\n[SIMULATED] User selected language: {language}")
    print(f"[SIMULATED] User selected scenario: Doctor's Office")
    print(f"\n{'='*60}")
    print("GENERATING LESSON WITH AI...")
    print(f"{'='*60}\n")

    # Generate lesson
    lesson = generate_lesson(language, scenario, num_phrases=3)

    print(f"✓ Lesson ready: {lesson['scenario']} — {lesson['language']}")
    print(f"✓ {len(lesson['phrases'])} practice phrases generated\n")
    time.sleep(1)

    # Simulate pronunciation attempts
    simulated_attempts = [
        {"accuracy": "high", "spoken": None},  # Perfect attempt
        {"accuracy": "medium", "spoken": None},  # Good attempt with minor errors
        {"accuracy": "low", "spoken": None},  # Needs work
    ]

    scores = []

    for i, phrase_data in enumerate(lesson["phrases"], 1):
        phrase = phrase_data["text"]
        tip = phrase_data.get("tip", "")
        target_sounds = phrase_data.get("target_sounds", [])

        print(f"\n{'─'*60}")
        print(f"  PHRASE {i} OF {len(lesson['phrases'])}")
        print(f"{'─'*60}")
        print(f"  Target phrase: \"{phrase}\"")
        print(f"  Practicing sounds: {', '.join(target_sounds)}")
        print(f"  Tip: {tip}")
        print()

        # Simulate what the user said
        attempt = simulated_attempts[i-1]

        if attempt["accuracy"] == "high":
            # Perfect pronunciation
            spoken = phrase.lower()
            print(f"  🎙  [SIMULATED] User speaks perfectly: \"{spoken}\"")
        elif attempt["accuracy"] == "medium":
            # Missing one word
            words = phrase.lower().split()
            if len(words) > 3:
                spoken = " ".join(words[:-1])  # Drop last word
            else:
                spoken = " ".join(words[:2])
            print(f"  🎙  [SIMULATED] User speaks (minor error): \"{spoken}\"")
        else:
            # More significant errors
            words = phrase.lower().split()
            spoken = " ".join(words[::2])  # Every other word
            print(f"  🎙  [SIMULATED] User speaks (needs practice): \"{spoken}\"")

        print(f"  ⏳  Transcribing and scoring...")
        time.sleep(0.5)

        # Score the attempt
        result = score_attempt(phrase, spoken, language)
        stars = score_to_stars(result["score"])
        scores.append(result["score"])

        print(f"\n  ✓ Transcribed: \"{spoken}\"")
        print(f"  📊 Score: {result['score']}/100  {stars}")

        # Generate AI feedback if not perfect
        if result["score"] < 85:
            print(f"  🤖 Generating AI feedback...")
            time.sleep(0.5)

            feedback = generate_correction_feedback(
                target_phrase=phrase,
                spoken_phrase=spoken,
                language_query=language,
                mismatched_phonemes=result["phoneme_mismatches"],
            )

            print(f"\n  💬 AI Coach Says:")
            print(f"     {feedback}")
        else:
            print(f"\n  💬 Coach: Excellent! That was very good.")

        time.sleep(1)

    # Final summary
    avg = int(sum(scores) / len(scores))
    print(f"\n{'='*60}")
    print(f"  LESSON COMPLETE")
    print(f"{'='*60}")
    print(f"\n  📈 Individual scores:")
    for i, score in enumerate(scores, 1):
        print(f"     Phrase {i}: {score}/100  {score_to_stars(score)}")

    print(f"\n  🎯 Average score: {avg}/100  {score_to_stars(avg)}")

    if avg >= 80:
        message = "You did a wonderful job today. Keep practicing!"
    elif avg >= 60:
        message = "Good effort. Practice these phrases every day and you will improve quickly."
    else:
        message = "Don't give up. Every practice session makes you stronger. Try again tomorrow."

    print(f"\n  💬 Final Message: {message}")
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("PRONUNCIATION COACH - AUTOMATED DEMO SESSION")
    print("="*60)
    print("\nThis simulates a complete coaching session with:")
    print("  ✓ AI-generated lesson")
    print("  ✓ Simulated pronunciation attempts")
    print("  ✓ Automated scoring")
    print("  ✓ AI-powered feedback")
    print("\n" + "="*60 + "\n")

    time.sleep(1)

    try:
        simulate_session()

        print("\n" + "="*60)
        print("DEMO SESSION COMPLETE!")
        print("="*60)
        print("\nThis demonstrated all the key features:")
        print("  ✓ AI lesson generation (Claude)")
        print("  ✓ Phoneme-based difficulty matching")
        print("  ✓ Pronunciation scoring")
        print("  ✓ Personalized AI feedback")
        print("\nTo run the REAL interactive version:")
        print("  1. Open your terminal")
        print("  2. cd to this directory")
        print("  3. Run: source venv/bin/activate")
        print("  4. Run: python main.py")
        print("  5. Speak into your microphone when prompted!")
        print("="*60 + "\n")

    except KeyboardInterrupt:
        print("\n\n  Demo interrupted. Goodbye!")
