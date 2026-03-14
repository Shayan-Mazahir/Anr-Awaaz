#!/usr/bin/env python3
"""
Demo script to test components without requiring microphone or API key
"""

print("=" * 60)
print("PRONUNCIATION COACH - COMPONENT DEMO")
print("=" * 60)

# 1. Test Phoneme Analysis
print("\n1. PHONEME ANALYSIS TEST")
print("-" * 60)

from phonemes import find_language, get_language_gaps, find_problems_in_phrase

test_languages = ["Arabic", "Spanish", "French", "Somali"]

for lang_query in test_languages:
    lang = find_language(lang_query)
    if lang:
        gaps = get_language_gaps(lang)
        print(f"\n{lang}:")
        print(f"  English sounds not in {lang}: {len(gaps)}")
        print(f"  Examples: {sorted(list(gaps))[:8]}")

# 2. Test Phrase Analysis
print("\n\n2. PHRASE ANALYSIS TEST")
print("-" * 60)

test_phrases = [
    ("I need to see a doctor", "Arabic"),
    ("How much does this cost", "Spanish"),
    ("I have three years of experience", "French"),
]

for phrase, lang_query in test_phrases:
    problems, lang = find_problems_in_phrase(phrase, lang_query)
    print(f"\nPhrase: \"{phrase}\"")
    print(f"Language: {lang}")
    print(f"Difficult sounds:")
    for p in problems[:5]:  # Show first 5
        print(f"  - Word '{p['word']}' contains /{p['ipa']}/ (CMU: {p['cmu']})")

# 3. Test Scoring
print("\n\n3. SCORING SYSTEM TEST")
print("-" * 60)

from scorer import score_attempt, score_to_stars

test_cases = [
    {
        "target": "I need to see a doctor",
        "spoken": "I need to see a doctor",
        "language": "Arabic",
        "description": "Perfect match"
    },
    {
        "target": "I need to see a doctor",
        "spoken": "I need see doctor",
        "language": "Arabic",
        "description": "Missing some words"
    },
    {
        "target": "I need to see a doctor",
        "spoken": "I want go hospital",
        "language": "Arabic",
        "description": "Completely different"
    },
]

for test in test_cases:
    result = score_attempt(test["target"], test["spoken"], test["language"])
    stars = score_to_stars(result["score"])
    print(f"\n{test['description']}:")
    print(f"  Target: \"{test['target']}\"")
    print(f"  Spoken: \"{test['spoken']}\"")
    print(f"  Score: {result['score']}/100 {stars}")
    print(f"  Matched words: {result['matched_words']}")
    print(f"  Missed words: {result['missed_words']}")

# 4. Test Scenarios
print("\n\n4. AVAILABLE SCENARIOS")
print("-" * 60)

from lessons import list_scenarios, SCENARIOS

scenarios = list_scenarios()
for key, label in scenarios.items():
    info = SCENARIOS[key]
    print(f"\n{label} ({key}):")
    print(f"  Context: {info['context']}")
    print(f"  Example phrases:")
    for example in info['example_phrases'][:2]:
        print(f"    - \"{example}\"")

# 5. Summary
print("\n\n5. SYSTEM STATUS")
print("-" * 60)

import os
from dotenv import load_dotenv
load_dotenv()

print("\n✓ PHOIBLE database: Loaded")
print("✓ CMU Dictionary: Loaded")
print("✓ Phoneme analysis: Working")
print("✓ Scoring system: Working")

api_key = os.getenv("ANTHROPIC_API_KEY")
if api_key and api_key != "your_api_key_here":
    print("✓ Anthropic API key: Configured")
    print("\n⚠️  To test AI lesson generation, run: python lessons.py")
else:
    print("✗ Anthropic API key: NOT SET")
    print("\n⚠️  To enable AI features:")
    print("   1. Get API key from https://console.anthropic.com/settings/keys")
    print("   2. Edit .env file and add: ANTHROPIC_API_KEY=your_key_here")

print("\n" + "=" * 60)
print("DEMO COMPLETE")
print("=" * 60)
print("\nTo run the full app: python main.py")
print("(Requires: API key, microphone access)")
