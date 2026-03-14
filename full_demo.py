#!/usr/bin/env python3
"""
Full interactive demo with text-to-speech simulation
This runs the complete app flow without requiring microphone input
"""

import time
import os
from lessons import generate_lesson, generate_correction_feedback, list_scenarios
from scorer import score_attempt, score_to_stars

def clear():
    os.system("clear")

def banner():
    print("""
╔═══════════════════════════════════════════════╗
║        PRONUNCIATION COACH                    ║
║        For New Arrivals Learning English      ║
╚═══════════════════════════════════════════════╝
""")

def speak_simulation(text: str):
    """Simulate text-to-speech"""
    print(f"  🔊 [COMPUTER SPEAKS]: \"{text}\"")
    time.sleep(1)

def run_full_demo():
    clear()
    banner()

    # Step 1: Language Selection
    print("\n" + "="*60)
    print("STEP 1: LANGUAGE SELECTION")
    print("="*60 + "\n")

    speak_simulation("Welcome. What is your native language?")

    print("\n  Common languages:")
    langs = ["Arabic", "Somali", "French", "Spanish", "Tigrinya", "Dari", "Pashto", "Swahili"]
    for i, l in enumerate(langs, 1):
        print(f"  {i}. {l}")
    print("  Or type any language name.")
    print()

    # Simulated user input
    choice = "1"
    print(f"  👤 [USER TYPES]: {choice}")
    language = "Arabic"

    speak_simulation(f"Great. Your language is {language}.")
    time.sleep(1)

    # Step 2: Scenario Selection
    clear()
    banner()

    print("\n" + "="*60)
    print("STEP 2: SCENARIO SELECTION")
    print("="*60 + "\n")

    speak_simulation("Which situation would you like to practice?")

    print("\n  Choose a situation:\n")
    scenarios = list_scenarios()
    for i, (k, label) in enumerate(scenarios.items(), 1):
        print(f"  {i}. {label}")
    print()

    # Simulated user input
    choice = "1"
    print(f"  👤 [USER TYPES]: {choice}")
    scenario_key = "doctor"

    speak_simulation(f"Let's practice Doctor's Office.")
    time.sleep(1)

    # Step 3: Generate Lesson
    clear()
    banner()

    print("\n" + "="*60)
    print("STEP 3: AI GENERATING LESSON")
    print("="*60 + "\n")

    print("  ⏳  Generating your lesson...")
    speak_simulation("One moment while I prepare your lesson.")

    lesson = generate_lesson(language, scenario_key, num_phrases=5)

    print(f"\n  ✓ Lesson ready: {lesson['scenario']} — {lesson['language']}")
    speak_simulation(f"Your lesson is ready. We will practice {len(lesson['phrases'])} phrases for the {lesson['scenario']} situation.")
    time.sleep(1)

    # Step 4: Practice Phrases
    scores = []

    # Simulate different accuracy levels
    accuracy_levels = ["perfect", "good", "medium", "good", "perfect"]

    for i, phrase_data in enumerate(lesson["phrases"], 1):
        clear()
        banner()

        phrase = phrase_data["text"]
        tip = phrase_data.get("tip", "")
        target_sounds = phrase_data.get("target_sounds", [])

        print(f"\n" + "="*60)
        print(f"STEP {3+i}: PRACTICING PHRASE {i} OF {len(lesson['phrases'])}")
        print("="*60 + "\n")

        print(f"  ── Phrase {i} of {len(lesson['phrases'])} ──")
        print(f"  Practicing sounds: {', '.join(target_sounds)}")
        print()

        # Speak the phrase
        speak_simulation("Listen carefully.")
        time.sleep(0.3)
        speak_simulation(phrase)
        time.sleep(0.5)
        speak_simulation(phrase)

        # Give tip
        speak_simulation(f"Remember: {tip}")
        time.sleep(0.5)
        speak_simulation("Now you try. Speak after the beep.")
        time.sleep(0.3)

        print("\n  🎙  Speak now...")
        print("  🔴 Recording for 6 seconds...")

        # Simulate recording
        for j in range(6):
            time.sleep(0.5)
            print(f"    {'▮' * (j+1)}", end='\r')
        print()

        # Simulate different pronunciation attempts
        accuracy = accuracy_levels[i-1]
        if accuracy == "perfect":
            spoken = phrase.lower()
            print(f"  👤 [USER SPEAKS PERFECTLY]: \"{spoken}\"")
        elif accuracy == "good":
            words = phrase.lower().split()
            spoken = " ".join(words[:-1]) if len(words) > 4 else " ".join(words)
            print(f"  👤 [USER SPEAKS (minor error)]: \"{spoken}\"")
        else:
            words = phrase.lower().split()
            spoken = " ".join(words[:-2]) if len(words) > 3 else " ".join(words[:3])
            print(f"  👤 [USER SPEAKS (needs practice)]: \"{spoken}\"")

        # Transcribe
        speak_simulation("Let me listen...")
        print("  ⏳  Transcribing...")
        time.sleep(1)

        print(f"  You said: \"{spoken}\"")

        # Score
        result = score_attempt(phrase, spoken, language)
        stars = score_to_stars(result["score"])
        scores.append(result["score"])

        print(f"  Score: {result['score']}/100  {stars}")
        speak_simulation(f"Your score is {result['score']} out of 100.")

        # Feedback
        if result["score"] >= 85:
            msg = "Excellent! That was very good."
            speak_simulation(msg)
        else:
            print("\n  🤖 AI is generating personalized feedback...")
            feedback = generate_correction_feedback(
                target_phrase=phrase,
                spoken_phrase=spoken,
                language_query=language,
                mismatched_phonemes=result["phoneme_mismatches"],
            )
            print(f"\n  💬 Coach: {feedback}\n")
            speak_simulation(feedback)

        time.sleep(2)

    # Step 5: Final Summary
    clear()
    banner()

    print("\n" + "="*60)
    print("STEP 9: LESSON SUMMARY")
    print("="*60 + "\n")

    avg = int(sum(scores) / len(scores))

    print(f"  ══ Lesson Complete ══")
    print(f"\n  📊 Individual Scores:")
    for i, score in enumerate(scores, 1):
        stars = score_to_stars(score)
        print(f"     Phrase {i}: {score}/100  {stars}")

    print(f"\n  🎯 Average score: {avg}/100  {score_to_stars(avg)}")
    speak_simulation(f"Lesson complete! Your average score was {avg} out of 100.")

    if avg >= 80:
        msg = "You did a wonderful job today. Keep practicing!"
    elif avg >= 60:
        msg = "Good effort. Practice these phrases every day and you will improve quickly."
    else:
        msg = "Do not give up. Every practice session makes you stronger. Try again tomorrow."

    speak_simulation(msg)

    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" "*15 + "FULL PRONUNCIATION COACH DEMO")
    print("="*70)
    print("\nThis simulates the COMPLETE app experience including:")
    print("  ✓ Voice guidance (text-to-speech simulation)")
    print("  ✓ Language & scenario selection")
    print("  ✓ AI lesson generation with Claude")
    print("  ✓ Simulated pronunciation recording")
    print("  ✓ Real-time scoring")
    print("  ✓ Personalized AI feedback")
    print("  ✓ Final summary and encouragement")
    print("\nSit back and watch the complete flow!")
    print("="*70 + "\n")

    input("Press ENTER to start the demo...")

    try:
        run_full_demo()

        print("\n" + "="*70)
        print(" "*20 + "🎉 DEMO COMPLETE! 🎉")
        print("="*70)
        print("\n✅ ALL FEATURES DEMONSTRATED:")
        print("   • AI-powered lesson generation")
        print("   • Phoneme-based difficulty matching for Arabic speakers")
        print("   • Automated pronunciation scoring")
        print("   • Personalized feedback from Claude AI")
        print("   • Complete voice-guided interface")
        print("\n📱 TO RUN THE REAL APP WITH YOUR VOICE:")
        print("   1. Open Terminal")
        print("   2. Run: cd /Users/rayyan/Desktop/Personal-Projects/WatAI/watIA-hackathon")
        print("   3. Run: source venv/bin/activate")
        print("   4. Run: python main.py")
        print("   5. Speak into your microphone when prompted!")
        print("\n" + "="*70 + "\n")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye!")
