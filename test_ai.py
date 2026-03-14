#!/usr/bin/env python3
"""
Quick AI test - generates a lesson and shows AI feedback without requiring microphone
"""

from lessons import generate_lesson, generate_correction_feedback
from scorer import score_attempt, score_to_stars

print("=" * 70)
print("PRONUNCIATION COACH - AI FEATURES TEST")
print("=" * 70)

# Test 1: Generate a lesson
print("\n1. AI LESSON GENERATION")
print("-" * 70)
print("Generating lesson for Arabic speakers - Doctor's Office scenario...")
print("(This calls Claude AI to create custom phrases)\n")

lesson = generate_lesson("Arabic", "doctor", num_phrases=3)

print(f"✓ Lesson generated!")
print(f"  Language: {lesson['language']}")
print(f"  Scenario: {lesson['scenario']}")
print(f"  Number of phrases: {len(lesson['phrases'])}\n")

for i, phrase in enumerate(lesson['phrases'], 1):
    print(f"Phrase {i}: \"{phrase['text']}\"")
    print(f"  Target sounds: {', '.join(phrase['target_sounds'])}")
    print(f"  Tip: {phrase['tip']}")
    print()

# Test 2: AI Correction Feedback
print("\n2. AI CORRECTION FEEDBACK")
print("-" * 70)
print("Simulating a pronunciation attempt with errors...\n")

target = "I need to see a doctor"
spoken = "I need see doctor"  # Missing some words

result = score_attempt(target, spoken, "Arabic")
print(f"Target phrase: \"{target}\"")
print(f"What user said: \"{spoken}\"")
print(f"Score: {result['score']}/100 {score_to_stars(result['score'])}")
print(f"Matched words: {result['matched_words']}")
print(f"Missed words: {result['missed_words']}\n")

print("Generating AI feedback...")
feedback = generate_correction_feedback(
    target_phrase=target,
    spoken_phrase=spoken,
    language_query="Arabic",
    mismatched_phonemes=result["phoneme_mismatches"],
)

print(f"\n💬 AI Coach Says:")
print(f"   {feedback}\n")

# Test 3: Another scenario
print("\n3. DIFFERENT SCENARIO TEST")
print("-" * 70)
print("Generating lesson for Spanish speakers - Job Interview scenario...\n")

lesson2 = generate_lesson("Spanish", "job_interview", num_phrases=2)

for i, phrase in enumerate(lesson2['phrases'], 1):
    print(f"Phrase {i}: \"{phrase['text']}\"")
    print(f"  Target sounds: {', '.join(phrase['target_sounds'])}")
    print(f"  Tip: {phrase['tip']}")
    print()

print("=" * 70)
print("✓ ALL AI FEATURES WORKING!")
print("=" * 70)
print("\nYour app is ready to use!")
print("\nTo run the full interactive app:")
print("  1. Open a terminal")
print("  2. cd to this directory")
print("  3. Run: source venv/bin/activate")
print("  4. Run: python main.py")
print("  5. Follow the voice prompts!")
